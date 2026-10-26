"""
Módulo TaskAnalyzer - Núcleo de métricas e produtividade.

Este módulo recebe uma lista de tarefas brutas e as transforma em
indicadores úteis para gestão, calculando tempo médio de conclusão,
taxa de atraso e agrupamentos por prioridade.

Gerado via assistente de IA (Gemini/Claude) com base no contrato SDD
definido em specs/task_analyzer_spec.md e nas regras de governança
em CONTEXT_RULES.md.

Author: Rafael Fernandes Durães (RA: 22452499)
"""

import logging
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Configuração de logging estruturado (proibido usar print)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de negócio
# ---------------------------------------------------------------------------
PRIORIDADES_VALIDAS: frozenset[str] = frozenset({"baixa", "media", "alta"})
STATUS_VALIDOS: frozenset[str] = frozenset({"pendente", "concluida"})
STATUS_CONCLUIDA: str = "concluida"
SEGUNDOS_POR_HORA: int = 3600


# ---------------------------------------------------------------------------
# Exceções de negócio
# ---------------------------------------------------------------------------
class TaskValidationError(Exception):
    """Exceção disparada quando uma tarefa viola as regras de negócio do SDD.

    Attributes:
        mensagem: Descrição clara da violação encontrada.
        task_id: Identificador da tarefa que originou o erro.
    """

    def __init__(self, mensagem: str, task_id: int | str | None = None) -> None:
        """Inicializa TaskValidationError com contexto detalhado.

        Args:
            mensagem: Descrição da violação de negócio.
            task_id: Identificador opcional da tarefa problemática.
        """
        self.task_id = task_id
        prefixo = f"[Task ID: {task_id}] " if task_id is not None else ""
        super().__init__(f"{prefixo}{mensagem}")
        logger.error("TaskValidationError gerado: %s", str(self))


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------
Tarefa = dict[str, Any]
MetricasPrioridade = dict[str, dict[str, float | int]]
ResultadoAnalise = dict[str, Any]

type ResultadoAnalise = dict[str, Any]


# ---------------------------------------------------------------------------
# Funções auxiliares (SRP: cada função resolve um único problema)
# ---------------------------------------------------------------------------
def _validar_tarefa(tarefa: Tarefa) -> None:
    """Valida os campos obrigatórios e as regras de negócio de uma tarefa.

    Verifica se o identificador está presente, se os campos de prioridade
    e status são valores permitidos, e se a consistência temporal é mantida
    (data_conclusao >= data_criacao).

    Args:
        tarefa: Dicionário representando uma tarefa do sistema.

    Raises:
        TaskValidationError: Se qualquer regra de negócio for violada.
    """
    task_id: int | str | None = tarefa.get("id")

    if task_id is None:
        raise TaskValidationError("Campo 'id' é obrigatório e não pode ser nulo.")

    prioridade: str | None = tarefa.get("prioridade")
    if prioridade not in PRIORIDADES_VALIDAS:
        raise TaskValidationError(
            f"Prioridade '{prioridade}' inválida. Valores aceitos: {sorted(PRIORIDADES_VALIDAS)}.",
            task_id=task_id,
        )

    status: str | None = tarefa.get("status")
    if status not in STATUS_VALIDOS:
        raise TaskValidationError(
            f"Status '{status}' inválido. Valores aceitos: {sorted(STATUS_VALIDOS)}.",
            task_id=task_id,
        )

    data_criacao: datetime | None = tarefa.get("data_criacao")
    data_conclusao: datetime | None = tarefa.get("data_conclusao")

    if data_conclusao is not None and data_criacao is not None:
        if data_conclusao < data_criacao:
            raise TaskValidationError(
                f"Inconsistência temporal: data_conclusao ({data_conclusao}) "
                f"é anterior a data_criacao ({data_criacao}).",
                task_id=task_id,
            )

    logger.debug("Tarefa ID=%s validada com sucesso.", task_id)


def _calcular_tempo_conclusao_horas(tarefa: Tarefa) -> float:
    """Calcula o tempo de conclusão de uma tarefa em horas.

    Args:
        tarefa: Dicionário de uma tarefa com status 'concluida' e ambas
                as datas preenchidas.

    Returns:
        Tempo decorrido entre criação e conclusão, em horas (float).
    """
    data_criacao: datetime = tarefa["data_criacao"]
    data_conclusao: datetime = tarefa["data_conclusao"]
    delta_segundos: float = (data_conclusao - data_criacao).total_seconds()
    return delta_segundos / SEGUNDOS_POR_HORA


def _inicializar_bucket_prioridade() -> dict[str, float | int]:
    """Cria a estrutura de dados inicial para um bucket de prioridade.

    Returns:
        Dicionário com contadores e acumuladores zerados para uma prioridade.
    """
    return {
        "total": 0,
        "concluidas": 0,
        "pendentes": 0,
        "soma_horas_conclusao": 0.0,
        "tempo_medio_conclusao_horas": 0.0,
    }


def _calcular_media_segura(soma: float, quantidade: int) -> float:
    """Calcula a média prevenindo divisão por zero.

    Args:
        soma: Valor acumulado total.
        quantidade: Número de itens contabilizados.

    Returns:
        Média calculada ou 0.0 se quantidade for zero.
    """
    if quantidade == 0:
        return 0.0
    return soma / quantidade


def _consolidar_metricas_prioridade(
    buckets: dict[str, dict[str, float | int]],
) -> MetricasPrioridade:
    """Finaliza o cálculo de tempo médio em cada bucket de prioridade.

    Args:
        buckets: Dicionário de buckets com dados acumulados por prioridade.

    Returns:
        Dicionário atualizado com tempo_medio_conclusao_horas calculado.
    """
    for prioridade, dados in buckets.items():
        soma: float = float(dados["soma_horas_conclusao"])
        quantidade: int = int(dados["concluidas"])
        dados["tempo_medio_conclusao_horas"] = _calcular_media_segura(soma, quantidade)
        logger.debug(
            "Prioridade '%s' → %d concluída(s), média=%.2fh",
            prioridade,
            quantidade,
            dados["tempo_medio_conclusao_horas"],
        )
    return buckets


# ---------------------------------------------------------------------------
# Função principal do contrato SDD
# ---------------------------------------------------------------------------
def analyze_tasks(tarefas: list[Tarefa]) -> ResultadoAnalise:
    """Analisa uma lista de tarefas e retorna métricas consolidadas de produtividade.

    Esta é a função principal do módulo TaskAnalyzer. Processa as tarefas de
    entrada validando cada registro, calculando tempo médio de conclusão (geral
    e por prioridade) e a taxa de atraso percentual.

    Args:
        tarefas: Lista de dicionários representando as tarefas do sistema.
                 Cada dicionário deve conter os campos definidos no contrato SDD:
                 id, titulo, prioridade, data_criacao, data_conclusao, status.

    Returns:
        Dicionário com as seguintes métricas:
            - total_tarefas (int): Quantidade total de tarefas recebidas.
            - total_concluidas (int): Número de tarefas com status 'concluida'.
            - total_pendentes (int): Número de tarefas com status 'pendente'.
            - tempo_medio_conclusao_horas (float): Média de horas entre criação
              e conclusão, considerando apenas tarefas concluídas.
            - taxa_atraso_percentual (float): Percentual de tarefas entregues
              após o prazo (data_conclusao > data_limite, quando informado).
            - indicadores_prioridade (dict): Métricas segmentadas por prioridade
              ('baixa', 'media', 'alta'), cada uma contendo total, concluidas,
              pendentes e tempo_medio_conclusao_horas.

    Raises:
        TaskValidationError: Se qualquer tarefa violar as regras de negócio
                             do contrato SDD (ex.: data_conclusao < data_criacao,
                             prioridade inválida, status inválido, id nulo).

    Example:
        >>> from datetime import datetime
        >>> tarefas = [
        ...     {
        ...         "id": 1,
        ...         "titulo": "Implementar login",
        ...         "prioridade": "alta",
        ...         "data_criacao": datetime(2024, 1, 1),
        ...         "data_conclusao": datetime(2024, 1, 3),
        ...         "status": "concluida",
        ...     }
        ... ]
        >>> resultado = analyze_tasks(tarefas)
        >>> resultado["total_tarefas"]
        1
        >>> resultado["total_concluidas"]
        1
    """
    logger.info("Iniciando analyze_tasks com %d tarefa(s).", len(tarefas))

    # Estruturas de acumulação
    total_tarefas: int = len(tarefas)
    total_concluidas: int = 0
    total_pendentes: int = 0
    soma_horas_conclusao_geral: float = 0.0
    total_com_atraso: int = 0
    total_com_prazo: int = 0

    buckets_prioridade: dict[str, dict[str, float | int]] = {
        prioridade: _inicializar_bucket_prioridade()
        for prioridade in PRIORIDADES_VALIDAS
    }

    for tarefa in tarefas:
        _validar_tarefa(tarefa)

        prioridade: str = tarefa["prioridade"]
        status: str = tarefa["status"]
        bucket = buckets_prioridade[prioridade]
        bucket["total"] = int(bucket["total"]) + 1

        if status == STATUS_CONCLUIDA:
            total_concluidas += 1
            bucket["concluidas"] = int(bucket["concluidas"]) + 1

            horas: float = _calcular_tempo_conclusao_horas(tarefa)
            soma_horas_conclusao_geral += horas
            bucket["soma_horas_conclusao"] = float(bucket["soma_horas_conclusao"]) + horas

            # Verifica atraso em relação ao campo data_limite (opcional)
            data_limite: datetime | None = tarefa.get("data_limite")
            data_conclusao: datetime = tarefa["data_conclusao"]
            if data_limite is not None:
                total_com_prazo += 1
                if data_conclusao > data_limite:
                    total_com_atraso += 1
                    logger.warning(
                        "Tarefa ID=%s entregue com atraso (conclusão=%s, limite=%s).",
                        tarefa["id"],
                        data_conclusao,
                        data_limite,
                    )
        else:
            total_pendentes += 1
            bucket["pendentes"] = int(bucket["pendentes"]) + 1

    tempo_medio_conclusao_horas: float = _calcular_media_segura(
        soma_horas_conclusao_geral, total_concluidas
    )
    taxa_atraso_percentual: float = _calcular_media_segura(
        total_com_atraso * 100.0, total_com_prazo
    )

    indicadores_prioridade: MetricasPrioridade = _consolidar_metricas_prioridade(
        buckets_prioridade
    )

    resultado: ResultadoAnalise = {
        "total_tarefas": total_tarefas,
        "total_concluidas": total_concluidas,
        "total_pendentes": total_pendentes,
        "tempo_medio_conclusao_horas": tempo_medio_conclusao_horas,
        "taxa_atraso_percentual": taxa_atraso_percentual,
        "indicadores_prioridade": indicadores_prioridade,
    }

    logger.info(
        "analyze_tasks concluído: total=%d, concluídas=%d, pendentes=%d, "
        "tempo_médio=%.2fh, taxa_atraso=%.2f%%.",
        total_tarefas,
        total_concluidas,
        total_pendentes,
        tempo_medio_conclusao_horas,
        taxa_atraso_percentual,
    )
    return resultado
