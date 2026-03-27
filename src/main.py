#!/usr/bin/env python3
"""
TechGrowth DES — Ponto de entrada da simulação.

Executa a Simulação de Eventos Discretos do pipeline
Kafka → Flink → Iceberg e gera artefatos de pesquisa.

Usage
-----
    python -m src.main
    python src/main.py
"""

from __future__ import annotations

from src.config import ExperimentConfig
from src.report import ReportGenerator
from src.simulation import TechGrowthPipelineSimulation


def main() -> None:
    """Executa simulação com configuração padrão e gera artefatos."""
    print("=" * 70)
    print("TechGrowth — Simulação de Eventos Discretos (DES)")
    print("Pipeline Kafka → Flink → Iceberg com Partições PACELC")
    print("MIT-508 — Data Platform Engineering (AGTU)")
    print("=" * 70)
    print()

    config = ExperimentConfig()
    sim = TechGrowthPipelineSimulation(config)
    metrics = sim.run()

    report = ReportGenerator(sim, output_dir="output")
    report.generate_all(metrics)

    print()
    print("=" * 70)
    print("Simulação concluída com sucesso!")
    print("Artefatos disponíveis em: output/")
    print("=" * 70)


if __name__ == "__main__":
    main()
