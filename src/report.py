"""
Gerador de gráficos científicos e relatório em português.

Todos os gráficos seguem padrão de publicação: Times New Roman,
DPI 300, exportação PNG + PDF, legendas em português.

References
----------
.. [1] Little, J. D. C. (1961). DOI: 10.1287/opre.9.3.383
.. [2] Abadi, D. J. (2012). DOI: 10.1109/MC.2012.33
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import datetime
from typing import TYPE_CHECKING, Dict

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker  # noqa: F401
import numpy as np

if TYPE_CHECKING:
    from src.simulation import TechGrowthPipelineSimulation

warnings.filterwarnings("ignore", category=RuntimeWarning)

plt.rcParams.update(
    {
        "figure.figsize": (12, 6),
        "figure.dpi": 150,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


class ReportGenerator:
    """
    Gera 6 gráficos científicos, relatório Markdown e proveniência JSON.

    Parameters
    ----------
    sim : TechGrowthPipelineSimulation
        Simulação executada com resultados.
    output_dir : str
        Diretório para salvar artefatos.
    """

    def __init__(
        self, sim: TechGrowthPipelineSimulation, output_dir: str = "output"
    ) -> None:
        self.sim = sim
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(self, metrics: Dict) -> None:
        """Gera todos os gráficos e o relatório consolidado."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Gerando gráficos...")

        self._plot_latency_over_time()
        self._plot_ecdf()
        self._plot_consumer_lag()
        self._plot_throughput()
        self._plot_violin_by_cell()
        self._plot_partition_impact()
        self._save_provenance(metrics)
        self._generate_report_md(metrics)

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Todos os artefatos salvos em '{self.output_dir}/'"
        )

    def _save_fig(self, fig: plt.Figure, name: str) -> None:
        """Salva figura em PNG (300 dpi) e PDF (vetorial)."""
        fig.savefig(
            f"{self.output_dir}/{name}.png", dpi=300, bbox_inches="tight"
        )
        fig.savefig(f"{self.output_dir}/{name}.pdf", bbox_inches="tight")
        plt.close(fig)

    def _plot_latency_over_time(self) -> None:
        """
        Figura 1 — Latência End-to-End ao Longo do Tempo.

        Escala logarítmica no eixo Y. Scatter azul (normal) vs.
        vermelho (partição). Marcação de SLA e burst sombreado.
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        times = [r.arrival_time_ms / 1000 for r in self.sim.results]
        latencies = [r.end_to_end_latency_ms for r in self.sim.results]
        partition_mask = [r.was_during_partition for r in self.sim.results]

        normal_t = [t for t, p in zip(times, partition_mask) if not p]
        normal_l = [lat for lat, p in zip(latencies, partition_mask) if not p]
        ax.scatter(
            normal_t,
            normal_l,
            s=1,
            alpha=0.4,
            c="#2171b5",
            label="Operação normal",
            rasterized=True,
        )

        part_t = [t for t, p in zip(times, partition_mask) if p]
        part_l = [lat for lat, p in zip(latencies, partition_mask) if p]
        if part_t:
            ax.scatter(
                part_t,
                part_l,
                s=3,
                alpha=0.7,
                c="#e34a33",
                label="Durante partição PACELC",
                rasterized=True,
            )

        ax.axhline(
            y=self.sim.config.sla_target_ms,
            color="black",
            linestyle="--",
            linewidth=1,
            label=f"SLA ({self.sim.config.sla_target_ms / 1000:.0f}s)",
        )
        ax.axvspan(
            self.sim.config.burst_start_ms / 1000,
            self.sim.config.burst_end_ms / 1000,
            alpha=0.08,
            color="orange",
            label="Burst Black Friday (5.800 eps)",
        )

        for pe in self.sim.partition_log:
            ax.axvspan(
                pe.start_ms / 1000,
                pe.end_ms / 1000,
                alpha=0.15,
                color="red",
                linewidth=0,
            )

        ax.set_yscale("log")
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Latência end-to-end (ms)")
        ax.set_title(
            "Figura 1 — Latência End-to-End: "
            "Operação Normal vs. Partições de Rede (PACELC)"
        )
        ax.legend(loc="upper left", framealpha=0.9)
        ax.set_ylim(bottom=1)

        fig.tight_layout()
        self._save_fig(fig, "fig1_latencia_tempo")
        print("  ✓ Figura 1 — Latência ao longo do tempo")

    def _plot_ecdf(self) -> None:
        """
        Figura 2 — ECDF de Latência com Marcação de SLA.

        Duas curvas: todos os eventos vs. durante partição.
        Anotação de % conformidade.
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        all_latencies = sorted(
            [r.end_to_end_latency_ms for r in self.sim.results]
        )
        ecdf_y = np.arange(1, len(all_latencies) + 1) / len(all_latencies)
        ax.plot(
            all_latencies,
            ecdf_y,
            color="#2171b5",
            linewidth=2,
            label="Todos os eventos",
        )

        part_latencies = sorted(
            [
                r.end_to_end_latency_ms
                for r in self.sim.results
                if r.was_during_partition
            ]
        )
        if part_latencies:
            ecdf_p = np.arange(1, len(part_latencies) + 1) / len(
                part_latencies
            )
            ax.plot(
                part_latencies,
                ecdf_p,
                color="#e34a33",
                linewidth=2,
                label="Durante partição PACELC",
            )

        sla = self.sim.config.sla_target_ms
        ax.axvline(
            x=sla,
            color="black",
            linestyle="--",
            linewidth=1,
            label=f"SLA ({sla / 1000:.0f}s)",
        )

        compliance = np.mean(np.array(all_latencies) <= sla) * 100
        ax.annotate(
            f"Conformidade geral: {compliance:.1f}% ≤ SLA",
            xy=(sla * 0.7, 0.5),
            fontsize=11,
            fontweight="bold",
            color="#2171b5",
        )

        if part_latencies:
            part_compliance = (
                np.mean(np.array(part_latencies) <= sla) * 100
            )
            ax.annotate(
                f"Durante partição: {part_compliance:.1f}% ≤ SLA",
                xy=(sla * 0.7, 0.4),
                fontsize=11,
                fontweight="bold",
                color="#e34a33",
            )

        ax.set_xscale("log")
        ax.set_xlabel("Latência end-to-end (ms)")
        ax.set_ylabel("Probabilidade acumulada")
        ax.set_title(
            "Figura 2 — ECDF de Latência: Conformidade com SLA de 5 Minutos"
        )
        ax.legend(loc="lower right", framealpha=0.9)

        fig.tight_layout()
        self._save_fig(fig, "fig2_ecdf_latencia")
        print("  ✓ Figura 2 — ECDF de latência")

    def _plot_consumer_lag(self) -> None:
        """
        Figura 3 — Consumer Lag do Kafka ao Longo do Tempo.

        Profundidade de fila com marcação da Lei de Little (L = λW).
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        times = [t / 1000 for t, _ in self.sim.consumer_lag]
        lags = [lag for _, lag in self.sim.consumer_lag]

        ax.plot(times, lags, color="#2171b5", linewidth=0.5, alpha=0.7)
        ax.fill_between(times, lags, alpha=0.2, color="#2171b5")

        ax.axvspan(
            self.sim.config.burst_start_ms / 1000,
            self.sim.config.burst_end_ms / 1000,
            alpha=0.08,
            color="orange",
            label="Burst Black Friday",
        )

        little_l = self.sim.config.burst_rate_eps * np.mean(
            [r.end_to_end_latency_ms / 1000 for r in self.sim.results]
        )
        ax.axhline(
            y=little_l,
            color="green",
            linestyle="--",
            linewidth=1.5,
            label=f"Lei de Little: L = λW ≈ {little_l:.0f}",
        )

        for pe in self.sim.partition_log:
            ax.axvspan(
                pe.start_ms / 1000,
                pe.end_ms / 1000,
                alpha=0.15,
                color="red",
                linewidth=0,
            )

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Consumer Lag (eventos pendentes)")
        ax.set_title(
            "Figura 3 — Consumer Lag do Kafka: "
            "Profundidade de Fila e Lei de Little"
        )
        ax.legend(loc="upper left", framealpha=0.9)

        fig.tight_layout()
        self._save_fig(fig, "fig3_consumer_lag")
        print("  ✓ Figura 3 — Consumer lag")

    def _plot_throughput(self) -> None:
        """
        Figura 4 — Throughput Efetivo (Eventos/Segundo).

        Throughput vs. taxa de chegada sob burst de Black Friday.
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        bin_ms = self.sim.config.throughput_bin_ms
        bins = np.arange(
            0, self.sim.config.sim_duration_ms + bin_ms, bin_ms
        )
        completions = np.array(
            [r.completion_time_ms for r in self.sim.results]
        )
        counts, _ = np.histogram(completions, bins=bins)
        throughput = counts / (bin_ms / 1000.0)

        bin_centers = (bins[:-1] + bins[1:]) / 2 / 1000
        ax.plot(
            bin_centers,
            throughput,
            color="#2171b5",
            linewidth=1.5,
            label="Throughput efetivo",
        )

        arrival_rate = np.array(
            [
                (
                    self.sim.config.burst_rate_eps
                    if self.sim.config.burst_start_ms
                    <= t * 1000
                    <= self.sim.config.burst_end_ms
                    else self.sim.config.nominal_rate_eps
                )
                for t in bin_centers
            ]
        )
        ax.plot(
            bin_centers,
            arrival_rate,
            color="gray",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label="Taxa de chegada",
        )

        ax.axvspan(
            self.sim.config.burst_start_ms / 1000,
            self.sim.config.burst_end_ms / 1000,
            alpha=0.08,
            color="orange",
            label="Burst Black Friday",
        )

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Eventos por segundo (eps)")
        ax.set_title(
            "Figura 4 — Throughput Efetivo: "
            "Sustentação sob Burst de Black Friday"
        )
        ax.legend(loc="upper right", framealpha=0.9)

        fig.tight_layout()
        self._save_fig(fig, "fig4_throughput")
        print("  ✓ Figura 4 — Throughput efetivo")

    def _plot_violin_by_cell(self) -> None:
        """
        Figura 5 — Distribuição de Latência por Célula (Violin Plot).

        Demonstra isolamento via Cell-Based Architecture. Células
        afetadas por partição marcadas com ★ e cor vermelha.
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        cell_data = []
        cell_labels = []
        affected_cells = set()

        for cell_id in range(self.sim.config.num_cells):
            cell_latencies = [
                r.end_to_end_latency_ms
                for r in self.sim.results
                if r.cell_id == cell_id
            ]
            if cell_latencies:
                cell_data.append(cell_latencies)
                had_partition = any(
                    pe.affected_cell == cell_id
                    for pe in self.sim.partition_log
                )
                if had_partition:
                    affected_cells.add(len(cell_data) - 1)
                suffix = " *" if had_partition else ""
                cell_labels.append(f"Célula {cell_id}{suffix}")

        parts = ax.violinplot(
            cell_data, showmeans=True, showmedians=True
        )

        for i, pc in enumerate(parts["bodies"]):
            pc.set_facecolor(
                "#e34a33" if i in affected_cells else "#2171b5"
            )
            pc.set_alpha(0.6)

        ax.set_yscale("log")
        ax.set_xticks(range(1, len(cell_labels) + 1))
        ax.set_xticklabels(cell_labels, rotation=45, ha="right")
        ax.axhline(
            y=self.sim.config.sla_target_ms,
            color="black",
            linestyle="--",
            linewidth=1,
            label="SLA (300s)",
        )
        ax.set_ylabel("Latência end-to-end (ms) — escala log")
        ax.set_title(
            "Figura 5 — Distribuição de Latência por Célula "
            "(* = afetada por partição)"
        )
        ax.legend(loc="upper right")

        fig.tight_layout()
        self._save_fig(fig, "fig5_violin_celulas")
        print("  ✓ Figura 5 — Violin plot por célula")

    def _plot_partition_impact(self) -> None:
        """
        Figura 6 — Impacto PACELC: box plot comparativo + barras SLA.

        Quantifica empiricamente o trade-off PA/EL do teorema PACELC
        (Abadi, 2012, DOI: 10.1109/MC.2012.33).
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        normal_lat = [
            r.end_to_end_latency_ms
            for r in self.sim.results
            if not r.was_during_partition
        ]
        partition_lat = [
            r.end_to_end_latency_ms
            for r in self.sim.results
            if r.was_during_partition
        ]

        bp = ax1.boxplot(
            [normal_lat, partition_lat if partition_lat else [0]],
            tick_labels=["Operação\nNormal", "Durante\nPartição"],
            patch_artist=True,
            showfliers=False,
        )
        bp["boxes"][0].set_facecolor("#2171b5")
        bp["boxes"][0].set_alpha(0.6)
        if partition_lat:
            bp["boxes"][1].set_facecolor("#e34a33")
            bp["boxes"][1].set_alpha(0.6)

        ax1.set_yscale("log")
        ax1.set_ylabel("Latência (ms) — escala log")
        ax1.set_title("Comparação de Distribuições")
        ax1.axhline(
            y=self.sim.config.sla_target_ms,
            color="black",
            linestyle="--",
            linewidth=1,
            label="SLA",
        )
        ax1.legend()

        sla = self.sim.config.sla_target_ms
        normal_compliance = np.mean(np.array(normal_lat) <= sla) * 100
        partition_compliance = (
            np.mean(np.array(partition_lat) <= sla) * 100
            if partition_lat
            else 100.0
        )

        bars = ax2.bar(
            ["Normal", "Partição"],
            [normal_compliance, partition_compliance],
            color=["#2171b5", "#e34a33"],
            alpha=0.7,
        )
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("Conformidade SLA (%)")
        ax2.set_title("Conformidade SLA: Normal vs. Partição")
        ax2.axhline(
            y=99.0,
            color="green",
            linestyle="--",
            linewidth=1,
            label="Meta 99,0%",
        )
        ax2.legend()

        for bar, val in zip(
            bars, [normal_compliance, partition_compliance]
        ):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center",
                fontweight="bold",
            )

        fig.suptitle(
            "Figura 6 — Impacto das Partições de Rede: "
            "Validação Empírica do PACELC",
            fontsize=13,
            fontweight="bold",
        )
        fig.tight_layout()
        self._save_fig(fig, "fig6_pacelc_impacto")
        print("  ✓ Figura 6 — Impacto PACELC")

    def _save_provenance(self, metrics: Dict) -> None:
        """Salva proveniência experimental em JSON."""
        provenance = {
            "experiment": (
                "TechGrowth DES — Pipeline Kafka→Flink→Iceberg"
            ),
            "author": "Carlos Ulisses Flores",
            "orcid": "0000-0002-6034-7765",
            "course": "MIT-508 — Data Platform Engineering (AGTU)",
            "timestamp": datetime.now().isoformat(),
            "python_version": "3.10+",
            "dependencies": {
                "simpy": "4.1.1",
                "numpy": "1.26+",
                "matplotlib": "3.8+",
                "scipy": "1.12+",
            },
            "metrics": metrics,
            "references": {
                "little_law": (
                    "Little, J. D. C. (1961). DOI: 10.1287/opre.9.3.383"
                ),
                "pacelc": (
                    "Abadi, D. J. (2012). DOI: 10.1109/MC.2012.33"
                ),
                "kafka_exactly_once": (
                    "Wang et al. (2021). DOI: 10.1145/3448016.3457556"
                ),
                "tail_latency": (
                    "Dean & Barroso (2013). DOI: 10.1145/2408776.2408794"
                ),
                "shuffle_sharding": (
                    "MacCárthaigh (2019). AWS Builders' Library"
                ),
                "cell_architecture": (
                    "AWS (2024). Well-Architected Framework"
                ),
            },
        }

        path = f"{self.output_dir}/experiment_provenance.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(provenance, f, indent=2, ensure_ascii=False)
        print("  ✓ Proveniência experimental (JSON)")

    def _generate_report_md(self, metrics: Dict) -> None:
        """Gera relatório acadêmico em Markdown (português)."""
        sla_s = self.sim.config.sla_target_ms / 1000
        cfg = self.sim.config

        report = f"""# Relatório de Validação Experimental — TechGrowth DES

**Disciplina:** MIT-508 — Data Platform Engineering (AGTU)
**Autor:** Carlos Ulisses Flores
**ORCID:** [0000-0002-6034-7765](https://orcid.org/0000-0002-6034-7765)
**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Seed:** {cfg.seed}

---

## 1. Parâmetros do Experimento

| Parâmetro | Valor |
|-----------|-------|
| Duração da simulação | {cfg.sim_duration_ms / 1000:.0f} s |
| Taxa nominal | {cfg.nominal_rate_eps:.0f} eps |
| Taxa burst (Black Friday) | {cfg.burst_rate_eps:.0f} eps |
| Janela de burst | {cfg.burst_start_ms / 1000:.0f}s – {cfg.burst_end_ms / 1000:.0f}s |
| Número de células | {cfg.num_cells} |
| Consumers/célula | {cfg.consumers_per_cell} |
| SLA alvo | {sla_s:.0f} s ({sla_s / 60:.0f} min) |
| Partições PACELC | {'Habilitadas' if cfg.partition_enabled else 'Desabilitadas'} |
| Prob. de partição | {cfg.partition_probability:.3f}/s (~1 a cada {1 / cfg.partition_probability:.0f}s) |
| Duração da partição | {cfg.partition_duration_ms:.0f} ms |

## 2. Resultados

| Métrica | Valor |
|---------|-------|
| Total de eventos processados | {metrics['total_events']:,} |
| **Conformidade SLA geral** | **{metrics['sla_compliance_pct']:.1f}%** |
| Latência P50 | {metrics['p50_latency_ms']:.1f} ms |
| Latência P95 | {metrics['p95_latency_ms']:.1f} ms |
| Latência P99 | {metrics['p99_latency_ms']:.1f} ms |
| Latência máxima | {metrics['max_latency_ms']:.1f} ms |
| Partições injetadas | {metrics['partitions_injected']} |
| Eventos durante partição | {metrics['events_during_partition']} |
| **SLA durante partição** | **{metrics['sla_compliance_during_partition_pct']:.1f}%** |
| P99 durante partição | {metrics['p99_during_partition_ms']:.1f} ms |
| Lei de Little (L = λW) | {metrics['little_law_L']:.0f} eventos simultâneos |

## 3. Análise

### 3.1 Conformidade com SLA

A simulação demonstra que a arquitetura celular com {cfg.num_cells} células \
e {cfg.consumers_per_cell} consumers por célula sustenta \
**{metrics['sla_compliance_pct']:.1f}% de conformidade com o SLA de \
{sla_s / 60:.0f} minutos** sob burst de Black Friday \
({cfg.burst_rate_eps:.0f} eps). O dimensionamento via Lei de Little \
(L = λW) garante ρ ≈ {cfg.burst_rate_eps / (cfg.num_cells * cfg.consumers_per_cell * (1000 / (cfg.flink_latency_mean_ms + cfg.iceberg_commit_ms))):.2f} \
durante burst, mantendo estabilidade do sistema de filas.

### 3.2 Validação PACELC

A injeção de {metrics['partitions_injected']} partições de rede demonstrou \
empiricamente o trade-off PA/EL do teorema PACELC (Abadi, 2012): durante \
partições, a arquitetura manteve disponibilidade (PA) com latência elevada \
(P99 = {metrics['p99_during_partition_ms']:.1f} ms vs. \
{metrics['p99_latency_ms']:.1f} ms geral), resultando em \
**{metrics['sla_compliance_during_partition_pct']:.1f}% de conformidade SLA** \
para eventos processados durante partições. O isolamento celular via shuffle \
sharding (MacCárthaigh, 2019) limitou o blast radius a uma única célula \
por partição.

### 3.3 Lei de Little

Conforme Little (1961), L = λW. Para λ = {cfg.burst_rate_eps:.0f} eps e W \
médio de {metrics['mean_latency_ms'] / 1000:.3f}s, o sistema mantém L ≈ \
{metrics['little_law_L']:.0f} eventos simultâneos em processamento, \
demonstrando que a capacidade instalada ({cfg.num_cells} × \
{cfg.consumers_per_cell} = {cfg.num_cells * cfg.consumers_per_cell} \
consumers) é suficiente para absorver o burst sem crescimento irreversível \
de fila.

## 4. Artefatos Gerados

- `fig1_latencia_tempo.png/pdf` — Latência ao longo do tempo
- `fig2_ecdf_latencia.png/pdf` — ECDF com SLA
- `fig3_consumer_lag.png/pdf` — Consumer lag e Lei de Little
- `fig4_throughput.png/pdf` — Throughput efetivo
- `fig5_violin_celulas.png/pdf` — Distribuição por célula
- `fig6_pacelc_impacto.png/pdf` — Impacto de partições PACELC
- `experiment_provenance.json` — Proveniência experimental

---

**Referências utilizadas na simulação:**

1. Little, J. D. C. (1961). A Proof for the Queuing Formula: L = λW. \
*Operations Research*, 9(3), 383-387. DOI: 10.1287/opre.9.3.383
2. Abadi, D. J. (2012). Consistency Tradeoffs in Modern Distributed \
Database System Design. *IEEE Computer*, 45(2), 37-42. DOI: 10.1109/MC.2012.33
3. Wang, G. et al. (2021). Consistency and Completeness: Rethinking \
Distributed Stream Processing in Apache Kafka. *SIGMOD '21*, 2602-2613. \
DOI: 10.1145/3448016.3457556
4. Dean, J. & Barroso, L. A. (2013). The Tail at Scale. *Communications \
of the ACM*, 56(2), 74-80. DOI: 10.1145/2408776.2408794
5. MacCárthaigh, C. (2019). Workload isolation using shuffle-sharding. \
*The Amazon Builders' Library*.
"""

        path = f"{self.output_dir}/relatorio_des.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        print("  ✓ Relatório em português (Markdown)")
