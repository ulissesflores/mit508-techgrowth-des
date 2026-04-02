# TechGrowth DES

Discrete-event simulation of a Kafka → Flink → Iceberg pipeline under PACELC-style network partitions and Black Friday burst load.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19244059.svg)](https://doi.org/10.5281/zenodo.19244059)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ulissesflores/mit508-techgrowth-des/blob/main/colab/TechGrowth_DES.ipynb)

This repository packages a reproducible simulation study for a high-growth e-commerce data platform. It models burst traffic, queueing pressure, and PACELC-induced latency under a Kafka/Flink/Iceberg architecture and produces publication-quality outputs for analysis and citation.

## At a glance

- Domain: data platform engineering, distributed systems, and resilience analysis
- Method: SimPy-based discrete-event simulation
- Experimental focus: SLA validation under Black Friday burst conditions
- Release: [v1.0.0 — TechGrowth DES Simulation](https://github.com/ulissesflores/mit508-techgrowth-des/releases/tag/v1.0.0)
- DOI: [10.5281/zenodo.19244059](https://doi.org/10.5281/zenodo.19244059)
- Zero-setup run: [Google Colab notebook](https://colab.research.google.com/github/ulissesflores/mit508-techgrowth-des/blob/main/colab/TechGrowth_DES.ipynb)

## What this repository demonstrates

- burst-load behavior in a Kafka → Flink → Iceberg pipeline
- PACELC-aware network partition injection and latency amplification
- queueing dynamics grounded in Little's Law
- cell-based isolation and shuffle-sharding under stress
- reproducible report generation from a single simulation entrypoint

## Key outputs

- [Final paper (PDF)](./docs/paper/TechGrowth_Final.pdf)
- [Methodological appendix (PDF)](./docs/appendix/Appendix_A_TechGrowth.pdf)
- Six publication-quality figures generated programmatically into `output/`
- Versioned archival release with DOI-backed citation metadata

## Quick start

### Option 1: Google Colab

Use the Colab notebook for the fastest zero-configuration run:

[Open `TechGrowth_DES.ipynb`](https://colab.research.google.com/github/ulissesflores/mit508-techgrowth-des/blob/main/colab/TechGrowth_DES.ipynb)

### Option 2: Local execution

```bash
git clone https://github.com/ulissesflores/mit508-techgrowth-des.git
cd mit508-techgrowth-des

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

### Option 3: Docker

```bash
docker build -t techgrowth-des .
docker run -v "$(pwd)/output:/app/output" techgrowth-des
```

## Repository layout

```text
src/        simulation, configuration, and report generation
colab/      notebook-based reproducible execution
docs/       paper and appendix artifacts
output/     generated figures and outputs
tests/      regression checks for simulation behavior
```

## Experimental setup

Two traffic regimes are simulated across a 60-second horizon with deterministic seed control:

1. Nominal operation: 578 events/s
2. Black Friday burst: 5,800 events/s

The simulation includes:

- Poisson-like arrival behavior
- 10 cells × 14 consumers per cell
- log-normal service and commit latency
- PACELC partition events
- tail-latency perturbation

This produces visible queueing pressure while keeping the system stable during the burst regime.

## Academic context

This artifact was developed in the context of `MIT-508 — Data Platform Engineering` in the MSc in AI program at AGTU. The course context is relevant provenance, but the repository is published as a standalone reproducible software artifact with its own release and citation surface.

## Citation

If you use this repository in academic or technical work, cite the released software artifact:

- DOI: [10.5281/zenodo.19244059](https://doi.org/10.5281/zenodo.19244059)
- Citation metadata: [CITATION.cff](./CITATION.cff)

```bibtex
@misc{flores2026techgrowth,
  author    = {Flores, Carlos Ulisses},
  title     = {TechGrowth DES: Stochastic Simulation of Kafka-Flink-Iceberg Pipeline with PACELC Network Partition Injection},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19244059},
  url       = {https://github.com/ulissesflores/mit508-techgrowth-des}
}
```

## References

Core references include Little's Law, PACELC trade-offs, tail-latency literature, and lakehouse/data-mesh architectural work. See the appendix and paper files under `docs/` for the full academic bibliography.
