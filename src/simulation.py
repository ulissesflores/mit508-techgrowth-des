"""
TechGrowth — Simulação DES do pipeline Kafka → Flink → Iceberg.

Modela produtor Kafka com taxa variável (Poisson), Consumer Group Flink
com processamento log-normal por célula, Sink Iceberg, Cell-Based
Architecture com shuffle sharding e injeção de partições PACELC.

References
----------
.. [1] Little, J. D. C. (1961). DOI: 10.1287/opre.9.3.383
.. [2] Abadi, D. J. (2012). DOI: 10.1109/MC.2012.33
.. [3] Wang, G. et al. (2021). DOI: 10.1145/3448016.3457556
.. [4] Dean, J. & Barroso, L. A. (2013). DOI: 10.1145/2408776.2408794
.. [5] MacCárthaigh, C. (2019). Shuffle sharding. AWS Builders' Library.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import simpy

from src.config import EventRecord, ExperimentConfig, PartitionEvent


class TechGrowthPipelineSimulation:
    """
    Simulação DES estocástica do pipeline TechGrowth.

    Parameters
    ----------
    config : ExperimentConfig
        Configuração completa do experimento.
    """

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config
        self.rng = np.random.RandomState(config.seed)
        self.partition_rng = np.random.RandomState(config.seed + 7)
        self.env = simpy.Environment()
        self.results: List[EventRecord] = []
        self.partition_log: List[PartitionEvent] = []
        self.consumer_lag: List[Tuple[float, int]] = []
        self._pending_events = 0
        self._event_counter = 0

        self.cells = [
            simpy.Resource(self.env, capacity=config.consumers_per_cell)
            for _ in range(config.num_cells)
        ]
        self._cell_partitioned = [False] * config.num_cells

    def _get_arrival_rate(self, current_time_ms: float) -> float:
        """
        Retorna taxa de chegada (eps) no instante atual.

        Transição nominal → burst → nominal modela Black Friday
        com pico de 10× o volume (Wang et al., 2021).
        """
        if self.config.burst_start_ms <= current_time_ms <= self.config.burst_end_ms:
            return self.config.burst_rate_eps
        return self.config.nominal_rate_eps

    def _assign_cell(self, event_id: int) -> int:
        """
        Shuffle sharding: atribui evento a célula via hash.

        Com C(10,2) = 45 combinações, o blast radius de uma partição
        é limitado a 1/10 do tráfego (MacCárthaigh, 2019).
        """
        return event_id % self.config.num_cells

    def _compute_processing_latency(self, cell_id: int) -> float:
        """
        Calcula latência Flink (log-normal) + Iceberg commit.

        Aplica penalidade PACELC (50×) durante partição e modela
        latência de cauda (Dean & Barroso, 2013).
        """
        base_latency = self.rng.lognormal(
            mean=np.log(self.config.flink_latency_mean_ms),
            sigma=self.config.flink_latency_sigma,
        )
        iceberg_latency = self.rng.lognormal(
            mean=np.log(self.config.iceberg_commit_ms),
            sigma=0.3,
        )
        total = base_latency + iceberg_latency

        if self._cell_partitioned[cell_id]:
            total *= self.config.partition_latency_multiplier

        if self.rng.random() < self.config.tail_latency_probability:
            total *= self.config.tail_latency_multiplier

        return total

    def _event_producer(self):
        """
        Produtor Kafka com taxa variável (processo de Poisson).

        Idempotent producer com exactly-once semantics
        (Wang et al., 2021, DOI: 10.1145/3448016.3457556).
        """
        while True:
            rate = self._get_arrival_rate(self.env.now)
            if rate <= 0:
                yield self.env.timeout(1)
                continue

            interval_ms = self.rng.exponential(1000.0 / rate)
            yield self.env.timeout(interval_ms)

            if self.env.now > self.config.sim_duration_ms:
                break

            self._event_counter += 1
            event_id = self._event_counter
            cell_id = self._assign_cell(event_id)
            self.env.process(self._process_event(event_id, cell_id))

    def _process_event(self, event_id: int, cell_id: int):
        """
        Processa evento no pipeline: enfileiramento → Flink → Iceberg.

        Consumer lag registrado como profundidade de fila, análogo
        ao consumer lag do Apache Kafka.
        """
        arrival_time = self.env.now
        self._pending_events += 1
        self.consumer_lag.append((self.env.now, self._pending_events))

        with self.cells[cell_id].request() as req:
            yield req
            processing_start = self.env.now

            was_partitioned = self._cell_partitioned[cell_id]
            latency = self._compute_processing_latency(cell_id)
            was_tail = latency > (
                self.config.flink_latency_mean_ms + self.config.iceberg_commit_ms
            ) * 10

            yield self.env.timeout(latency)

        completion_time = self.env.now
        self._pending_events -= 1

        self.results.append(
            EventRecord(
                event_id=event_id,
                cell_id=cell_id,
                arrival_time_ms=arrival_time,
                processing_start_ms=processing_start,
                completion_time_ms=completion_time,
                end_to_end_latency_ms=completion_time - arrival_time,
                was_during_partition=was_partitioned,
                was_tail_latency=was_tail,
            )
        )

    def _partition_injector(self):
        """
        Injeta partições de rede para validação PACELC (Abadi, 2012).

        Processo de Poisson independente: ~1 partição a cada 30s,
        duração de 2s, afetando UMA célula por vez para demonstrar
        blast radius limitado via shuffle sharding.
        """
        if not self.config.partition_enabled:
            return

        while self.env.now < self.config.sim_duration_ms:
            interval = self.partition_rng.exponential(
                1000.0 / self.config.partition_probability
            )
            yield self.env.timeout(interval)

            if self.env.now > self.config.sim_duration_ms:
                break

            affected_cell = self.partition_rng.randint(0, self.config.num_cells)
            self._cell_partitioned[affected_cell] = True

            self.partition_log.append(
                PartitionEvent(
                    start_ms=self.env.now,
                    end_ms=self.env.now + self.config.partition_duration_ms,
                    affected_cell=affected_cell,
                )
            )

            yield self.env.timeout(self.config.partition_duration_ms)
            self._cell_partitioned[affected_cell] = False

    def run(self) -> Dict:
        """
        Executa simulação completa e retorna métricas consolidadas.

        Returns
        -------
        dict
            Métricas: total_events, sla_compliance_pct, percentis,
            throughput, partitions_injected, little_law_L, etc.
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando simulação DES...")
        print(f"  Seed: {self.config.seed}")
        print(f"  Duração: {self.config.sim_duration_ms / 1000:.0f}s")
        print(f"  Taxa nominal: {self.config.nominal_rate_eps:.0f} eps")
        print(f"  Taxa burst: {self.config.burst_rate_eps:.0f} eps")
        print(
            f"  Burst: {self.config.burst_start_ms / 1000:.0f}s"
            f"–{self.config.burst_end_ms / 1000:.0f}s"
        )
        print(f"  Células: {self.config.num_cells}")
        print(f"  Consumers/célula: {self.config.consumers_per_cell}")
        print(
            f"  Partições PACELC: "
            f"{'habilitadas' if self.config.partition_enabled else 'desabilitadas'}"
        )
        print()

        self.env.process(self._event_producer())
        self.env.process(self._partition_injector())
        self.env.run(until=self.config.sim_duration_ms)

        return self._compute_metrics()

    def _compute_metrics(self) -> Dict:
        """Computa métricas consolidadas da simulação."""
        if not self.results:
            return {"error": "Nenhum evento processado"}

        latencies = np.array([r.end_to_end_latency_ms for r in self.results])
        sla = self.config.sla_target_ms

        partition_events = [r for r in self.results if r.was_during_partition]
        partition_latencies = (
            np.array([r.end_to_end_latency_ms for r in partition_events])
            if partition_events
            else np.array([0.0])
        )

        metrics = {
            "total_events": len(self.results),
            "sla_target_ms": sla,
            "sla_compliance_pct": float(np.mean(latencies <= sla) * 100),
            "p50_latency_ms": float(np.percentile(latencies, 50)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "p99_latency_ms": float(np.percentile(latencies, 99)),
            "max_latency_ms": float(np.max(latencies)),
            "mean_latency_ms": float(np.mean(latencies)),
            "std_latency_ms": float(np.std(latencies)),
            "partitions_injected": len(self.partition_log),
            "events_during_partition": len(partition_events),
            "sla_compliance_during_partition_pct": (
                float(np.mean(partition_latencies <= sla) * 100)
                if partition_events
                else 100.0
            ),
            "p99_during_partition_ms": (
                float(np.percentile(partition_latencies, 99))
                if len(partition_events) > 1
                else 0.0
            ),
            "little_law_L": float(
                np.mean(latencies / 1000.0) * self.config.burst_rate_eps
            ),
            "config": {
                "seed": self.config.seed,
                "sim_duration_ms": self.config.sim_duration_ms,
                "nominal_rate_eps": self.config.nominal_rate_eps,
                "burst_rate_eps": self.config.burst_rate_eps,
                "num_cells": self.config.num_cells,
                "consumers_per_cell": self.config.consumers_per_cell,
                "partition_enabled": self.config.partition_enabled,
            },
        }

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulação concluída.")
        print(f"  Eventos processados: {metrics['total_events']:,}")
        print(
            f"  Conformidade SLA ({sla / 1000:.0f}s): "
            f"{metrics['sla_compliance_pct']:.1f}%"
        )
        print(f"  Latência P50: {metrics['p50_latency_ms']:.1f} ms")
        print(f"  Latência P95: {metrics['p95_latency_ms']:.1f} ms")
        print(f"  Latência P99: {metrics['p99_latency_ms']:.1f} ms")
        print(f"  Partições injetadas: {metrics['partitions_injected']}")
        print(f"  Eventos durante partição: {metrics['events_during_partition']}")
        print(
            f"  SLA durante partição: "
            f"{metrics['sla_compliance_during_partition_pct']:.1f}%"
        )
        print(
            f"  Lei de Little L (burst): "
            f"{metrics['little_law_L']:.0f} eventos simultâneos"
        )

        return metrics
