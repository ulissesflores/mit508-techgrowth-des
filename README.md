# TechGrowth — Simulação de Eventos Discretos (DES)

**Pipeline Kafka → Flink → Iceberg com Injeção de Partições de Rede (PACELC)**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ulissesflores/mit508-techgrowth-des/blob/main/colab/TechGrowth_DES.ipynb)

> **Validação experimental do SLA de 5 minutos sob burst de Black Friday (5.800 eps) com análise PACELC.**

---

## Contexto Acadêmico

| Campo | Valor |
|-------|-------|
| **Disciplina** | MIT-508 — Data Platform Engineering |
| **Instituição** | American Global Tech University (AGTU) |
| **Programa** | Mestrado em Inteligência Artificial |
| **Professor** | Dr. Emerson Rodolfo Abraham |
| **Autor** | Carlos Ulisses Flores |
| **ORCID** | [0000-0002-6034-7765](https://orcid.org/0000-0002-6034-7765) |
| **Data** | Março de 2026 |

Este repositório contém os artefatos de validação experimental do estudo de caso **TechGrowth** — uma empresa de e-commerce em hipercrescimento cuja arquitetura de dados é modernizada via *Data Lakehouse* (Apache Iceberg), Arquitetura Kappa (Kafka + Flink) e *Cell-Based Architecture* com *shuffle sharding*.

---

## O Experimento

Dois regimes são simulados sob tráfego de stress idêntico (seed = 42, horizonte de 60 segundos):

1. **Operação nominal** (0–15s e 45–60s): 578 eps — volume cotidiano (~50M eventos/dia)
2. **Burst Black Friday** (15–45s): 5.800 eps — 10× o volume nominal

A simulação modela:

- **Produtor Kafka** com taxa variável (Poisson) e exactly-once semantics (Wang et al., 2021)
- **Consumer Group Flink** com 10 células × 14 consumers = 140 total, latência log-normal
- **Sink Iceberg** com commit log-normal
- **Cell-Based Architecture** com shuffle sharding (MacCárthaigh, 2019)
- **Injeção de partições PACELC** (~1 a cada 30s, 2s de duração, 50× latência)
- **Latência de cauda** (0,3% probabilidade, 20× — Dean & Barroso, 2013)

### Dimensionamento (Lei de Little)

Para λ = 5.800 eps e tempo de serviço médio W ≈ 23 ms, cada consumer processa ~43 eps. Com 140 consumers totais, a capacidade é ~6.090 eps → ρ ≈ 0,95 durante burst. O sistema é estável (ρ < 1) com queuing visível — trade-off intencional para demonstrar dinâmica de filas.

---

## Estrutura do Repositório

```
mit508-techgrowth-des/
├── .github/workflows/ci.yml    # GitHub Actions: lint + test
├── CITATION.cff                # Metadados de citação acadêmica
├── Dockerfile                  # Reprodutibilidade via container
├── LICENSE                     # Apache 2.0
├── README.md                   # Este arquivo
├── requirements.txt            # Dependências Python
├── src/
│   ├── __init__.py
│   ├── config.py               # ExperimentConfig dataclass
│   ├── simulation.py           # TechGrowthPipelineSimulation (SimPy DES)
│   ├── report.py               # ReportGenerator (6 gráficos + relatório)
│   └── main.py                 # Ponto de entrada
├── colab/
│   └── TechGrowth_DES.ipynb    # Notebook Google Colab auto-contido
├── output/                     # Artefatos gerados pela simulação
│   └── .gitkeep
└── tests/
    └── test_simulation.py      # Testes unitários (pytest)
```

---

## Como Executar

### Opção 1: Google Colab (Recomendado — Zero Configuração)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ulissesflores/mit508-techgrowth-des/blob/main/colab/TechGrowth_DES.ipynb)

### Opção 2: Execução Local

```bash
git clone https://github.com/ulissesflores/mit508-techgrowth-des.git
cd mit508-techgrowth-des

python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python -m src.main
```

### Opção 3: Docker (Reprodutibilidade Máxima)

```bash
docker build -t techgrowth-des .
docker run -v $(pwd)/output:/app/output techgrowth-des
```

---

## Gráficos Gerados

A simulação produz 6 figuras em formato de publicação (300 dpi, Times New Roman, legendas em português):

| Figura | Descrição |
|--------|-----------|
| **Fig 1** | Latência end-to-end ao longo do tempo (escala log Y) |
| **Fig 2** | ECDF de latência com marcação de SLA (5 min) |
| **Fig 3** | Consumer lag do Kafka com Lei de Little (L = λW) |
| **Fig 4** | Throughput efetivo vs. taxa de chegada |
| **Fig 5** | Violin plot de latência por célula (★ = partição) |
| **Fig 6** | Impacto PACELC: box plot + conformidade SLA |

---

## Parâmetros do Experimento

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Seed | 42 | Reprodutibilidade determinística |
| Duração | 60s | Captura transição nominal→burst→nominal |
| Taxa nominal | 578 eps | 50M eventos/dia ÷ 86.400s |
| Taxa burst | 5.800 eps | 10× nominal (Black Friday) |
| Janela burst | 15s–45s | 30s de estresse sustentado |
| Células | 10 | Cell-Based Architecture |
| Consumers/célula | 14 | ρ ≈ 0,95 durante burst (via Lei de Little) |
| SLA alvo | 300.000 ms | 5 minutos |
| Partições PACELC | ~1/30s, 2s | Validação empírica do teorema |

---

## Referências

1. Little, J. D. C. (1961). A Proof for the Queuing Formula: L = λW. *Operations Research*, 9(3), 383-387. https://doi.org/10.1287/opre.9.3.383
2. Abadi, D. J. (2012). Consistency Tradeoffs in Modern Distributed Database System Design. *IEEE Computer*, 45(2), 37-42. https://doi.org/10.1109/MC.2012.33
3. Wang, G. et al. (2021). Consistency and Completeness: Rethinking Distributed Stream Processing in Apache Kafka. *SIGMOD '21*, 2602-2613. https://doi.org/10.1145/3448016.3457556
4. Dean, J. & Barroso, L. A. (2013). The Tail at Scale. *Communications of the ACM*, 56(2), 74-80. https://doi.org/10.1145/2408776.2408794
5. MacCárthaigh, C. (2019). Workload isolation using shuffle-sharding. *The Amazon Builders' Library*.
6. AWS. (2024). *Reducing the Scope of Impact with Cell-Based Architecture*. AWS Well-Architected Framework.
7. Armbrust, M. et al. (2021). Lakehouse: A New Generation of Open Platforms. *CIDR '21*.
8. Dehghani, Z. (2022). *Data Mesh: Delivering Data-Driven Value at Scale*. O'Reilly Media.

---

## Licença

Apache License 2.0 — veja [LICENSE](LICENSE) para detalhes.

## Citação

Se utilizar este software em sua pesquisa, cite usando os metadados em [CITATION.cff](CITATION.cff) ou o DOI do Zenodo acima.

```bibtex
@misc{flores2026techgrowth,
  author    = {Flores, Carlos Ulisses},
  title     = {TechGrowth DES: Stochastic Simulation of Kafka-Flink-Iceberg
               Pipeline with PACELC Network Partition Injection},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://github.com/ulissesflores/mit508-techgrowth-des}
}
```
