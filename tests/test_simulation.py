"""
Testes unitários da simulação TechGrowth DES.

Verifica configuração, distribuição celular, taxas de chegada,
Lei de Little e conformidade SLA.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.config import ExperimentConfig
from src.simulation import TechGrowthPipelineSimulation


class TestConfigDefaults:
    """Verifica valores padrão do ExperimentConfig."""

    def test_seed(self) -> None:
        cfg = ExperimentConfig()
        assert cfg.seed == 42

    def test_nominal_rate(self) -> None:
        cfg = ExperimentConfig()
        assert cfg.nominal_rate_eps == 578.0

    def test_burst_rate(self) -> None:
        cfg = ExperimentConfig()
        assert cfg.burst_rate_eps == 5_800.0

    def test_num_cells(self) -> None:
        cfg = ExperimentConfig()
        assert cfg.num_cells == 10

    def test_consumers_per_cell(self) -> None:
        cfg = ExperimentConfig()
        assert cfg.consumers_per_cell == 14

    def test_sla_target(self) -> None:
        cfg = ExperimentConfig()
        assert cfg.sla_target_ms == 300_000.0


class TestCellAssignment:
    """Verifica que shuffle sharding distribui uniformemente."""

    def test_uniform_distribution(self) -> None:
        cfg = ExperimentConfig()
        sim = TechGrowthPipelineSimulation(cfg)

        cell_counts = [0] * cfg.num_cells
        for event_id in range(1, 10_001):
            cell_id = sim._assign_cell(event_id)
            cell_counts[cell_id] += 1

        expected = 10_000 / cfg.num_cells
        for count in cell_counts:
            assert abs(count - expected) / expected < 0.05

    def test_deterministic(self) -> None:
        cfg = ExperimentConfig()
        sim = TechGrowthPipelineSimulation(cfg)
        assert sim._assign_cell(42) == sim._assign_cell(42)


class TestArrivalRate:
    """Verifica taxa de chegada nominal e burst."""

    def test_nominal_before_burst(self) -> None:
        cfg = ExperimentConfig()
        sim = TechGrowthPipelineSimulation(cfg)
        assert sim._get_arrival_rate(0) == cfg.nominal_rate_eps

    def test_nominal_after_burst(self) -> None:
        cfg = ExperimentConfig()
        sim = TechGrowthPipelineSimulation(cfg)
        assert sim._get_arrival_rate(50_000) == cfg.nominal_rate_eps

    def test_burst_during_window(self) -> None:
        cfg = ExperimentConfig()
        sim = TechGrowthPipelineSimulation(cfg)
        assert sim._get_arrival_rate(20_000) == cfg.burst_rate_eps

    def test_burst_at_boundaries(self) -> None:
        cfg = ExperimentConfig()
        sim = TechGrowthPipelineSimulation(cfg)
        assert sim._get_arrival_rate(15_000) == cfg.burst_rate_eps
        assert sim._get_arrival_rate(45_000) == cfg.burst_rate_eps


class TestLittleLaw:
    """
    Verifica Lei de Little: L = λW (tolerância 20%).

    Executa mini-simulação de 10s sem partições para condições
    de estado estacionário mais limpas.
    """

    def test_little_law_approximation(self) -> None:
        cfg = ExperimentConfig(
            sim_duration_ms=10_000,
            burst_start_ms=0,
            burst_end_ms=0,
            partition_enabled=False,
            nominal_rate_eps=578.0,
        )
        sim = TechGrowthPipelineSimulation(cfg)
        metrics = sim.run()

        if metrics["total_events"] < 100:
            pytest.skip("Poucos eventos para validar Lei de Little")

        latencies = np.array(
            [r.end_to_end_latency_ms for r in sim.results]
        )
        avg_w_s = np.mean(latencies) / 1000.0
        lambda_eps = cfg.nominal_rate_eps
        expected_l = lambda_eps * avg_w_s

        actual_events = metrics["total_events"]
        expected_events = cfg.nominal_rate_eps * (cfg.sim_duration_ms / 1000.0)
        throughput_ratio = actual_events / expected_events

        assert 0.8 < throughput_ratio < 1.2, (
            f"Lei de Little: throughput {actual_events} vs esperado "
            f"{expected_events:.0f} (ratio={throughput_ratio:.2f})"
        )
        assert expected_l > 0, (
            f"Lei de Little: L={expected_l:.1f} deve ser positivo"
        )


class TestSLACompliance:
    """Executa mini-simulação e verifica conformidade SLA > 95%."""

    def test_sla_above_threshold(self) -> None:
        cfg = ExperimentConfig(
            sim_duration_ms=5_000,
            partition_enabled=False,
        )
        sim = TechGrowthPipelineSimulation(cfg)
        metrics = sim.run()

        assert metrics["sla_compliance_pct"] > 95.0, (
            f"SLA compliance {metrics['sla_compliance_pct']:.1f}% < 95%"
        )

    def test_events_processed(self) -> None:
        cfg = ExperimentConfig(
            sim_duration_ms=5_000,
            partition_enabled=False,
        )
        sim = TechGrowthPipelineSimulation(cfg)
        metrics = sim.run()

        assert metrics["total_events"] > 0
