"""
Configuração e dataclasses do experimento TechGrowth DES.

Parâmetros calibrados para validação do pipeline Kafka → Flink → Iceberg
sob burst de Black Friday (5.800 eps) com injeção de partições PACELC.

References
----------
.. [1] Little, J. D. C. (1961). DOI: 10.1287/opre.9.3.383
.. [2] Abadi, D. J. (2012). DOI: 10.1109/MC.2012.33
.. [3] Wang, G. et al. (2021). DOI: 10.1145/3448016.3457556
.. [4] Dean, J. & Barroso, L. A. (2013). DOI: 10.1145/2408776.2408794
"""

from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    """
    Parâmetros de proveniência experimental.

    Dimensionamento via Lei de Little (1961): L = λW.
    Para λ_burst = 5.800 eps e tempo de serviço médio W ≈ 23 ms,
    cada consumer processa ~43 eps. Com 14 consumers/célula × 10 células
    = 140 total, a capacidade é ~6.090 eps → ρ ≈ 0,95 durante burst.
    Isso garante estabilidade (ρ < 1) com queuing visível.

    References
    ----------
    .. [1] Little (1961). DOI: 10.1287/opre.9.3.383
    .. [2] Abadi (2012). DOI: 10.1109/MC.2012.33
    """

    seed: int = 42
    sim_duration_ms: int = 60_000
    nominal_rate_eps: float = 578.0
    burst_rate_eps: float = 5_800.0
    burst_start_ms: int = 15_000
    burst_end_ms: int = 45_000
    num_cells: int = 10
    consumers_per_cell: int = 14
    flink_latency_mean_ms: float = 8.0
    flink_latency_sigma: float = 0.5
    iceberg_commit_ms: float = 15.0
    sla_target_ms: float = 300_000.0
    partition_enabled: bool = True
    partition_probability: float = 0.033
    partition_duration_ms: float = 2_000.0
    partition_latency_multiplier: float = 50.0
    tail_latency_probability: float = 0.003
    tail_latency_multiplier: float = 20.0
    throughput_bin_ms: int = 1_000


@dataclass
class EventRecord:
    """Registro de um evento processado pelo pipeline."""

    event_id: int
    cell_id: int
    arrival_time_ms: float
    processing_start_ms: float
    completion_time_ms: float
    end_to_end_latency_ms: float
    was_during_partition: bool
    was_tail_latency: bool


@dataclass
class PartitionEvent:
    """Registro de uma partição de rede injetada."""

    start_ms: float
    end_ms: float
    affected_cell: int
