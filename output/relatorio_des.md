# Relatório de Validação Experimental — TechGrowth DES

**Disciplina:** MIT-508 — Data Platform Engineering (AGTU)
**Autor:** Carlos Ulisses Flores
**ORCID:** [0000-0002-6034-7765](https://orcid.org/0000-0002-6034-7765)
**Data:** 26/03/2026 22:03
**Seed:** 42

---

## 1. Parâmetros do Experimento

| Parâmetro | Valor |
|-----------|-------|
| Duração da simulação | 60 s |
| Taxa nominal | 578 eps |
| Taxa burst (Black Friday) | 5800 eps |
| Janela de burst | 15s – 45s |
| Número de células | 10 |
| Consumers/célula | 14 |
| SLA alvo | 300 s (5 min) |
| Partições PACELC | Habilitadas |
| Prob. de partição | 0.033/s (~1 a cada 30s) |
| Duração da partição | 2000 ms |

## 2. Resultados

| Métrica | Valor |
|---------|-------|
| Total de eventos processados | 191,317 |
| **Conformidade SLA geral** | **100.0%** |
| Latência P50 | 1218.9 ms |
| Latência P95 | 2504.8 ms |
| Latência P99 | 2764.1 ms |
| Latência máxima | 3687.8 ms |
| Partições injetadas | 2 |
| Eventos durante partição | 58 |
| **SLA durante partição** | **100.0%** |
| P99 durante partição | 3206.0 ms |
| Lei de Little (L = λW) | 7058 eventos simultâneos |

## 3. Análise

### 3.1 Conformidade com SLA

A simulação demonstra que a arquitetura celular com 10 células e 14 consumers por célula sustenta **100.0% de conformidade com o SLA de 5 minutos** sob burst de Black Friday (5800 eps). O dimensionamento via Lei de Little (L = λW) garante ρ ≈ 0.95 durante burst, mantendo estabilidade do sistema de filas.

### 3.2 Validação PACELC

A injeção de 2 partições de rede demonstrou empiricamente o trade-off PA/EL do teorema PACELC (Abadi, 2012): durante partições, a arquitetura manteve disponibilidade (PA) com latência elevada (P99 = 3206.0 ms vs. 2764.1 ms geral), resultando em **100.0% de conformidade SLA** para eventos processados durante partições. O isolamento celular via shuffle sharding (MacCárthaigh, 2019) limitou o blast radius a uma única célula por partição.

### 3.3 Lei de Little

Conforme Little (1961), L = λW. Para λ = 5800 eps e W médio de 1.217s, o sistema mantém L ≈ 7058 eventos simultâneos em processamento, demonstrando que a capacidade instalada (10 × 14 = 140 consumers) é suficiente para absorver o burst sem crescimento irreversível de fila.

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

1. Little, J. D. C. (1961). A Proof for the Queuing Formula: L = λW. *Operations Research*, 9(3), 383-387. DOI: 10.1287/opre.9.3.383
2. Abadi, D. J. (2012). Consistency Tradeoffs in Modern Distributed Database System Design. *IEEE Computer*, 45(2), 37-42. DOI: 10.1109/MC.2012.33
3. Wang, G. et al. (2021). Consistency and Completeness: Rethinking Distributed Stream Processing in Apache Kafka. *SIGMOD '21*, 2602-2613. DOI: 10.1145/3448016.3457556
4. Dean, J. & Barroso, L. A. (2013). The Tail at Scale. *Communications of the ACM*, 56(2), 74-80. DOI: 10.1145/2408776.2408794
5. MacCárthaigh, C. (2019). Workload isolation using shuffle-sharding. *The Amazon Builders' Library*.
