"""
Test Harness - Suíte de Testes Automatizados do TaskAnalyzer.

Traduz diretamente os Cenários de Aceite BDD (Dado-Quando-Então) definidos
em specs/task_analyzer_spec.md para testes automatizados com pytest.

Cobertura:
    - Cenário 1 (Caminho Feliz): Validação de todas as métricas calculadas.
    - Cenário 2 (Dados Corrompidos): Validação do disparo de TaskValidationError.
    - Casos de Borda: Listas vazias, somente pendentes, divisão por zero.

Author: Rafael Fernandes Durães (RA: 22452499)
"""

import pytest
from datetime import datetime

import sys
import os

# Garante que o pacote src seja encontrado independente do diretório de execução
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from task_analyzer import analyze_tasks, TaskValidationError


# ---------------------------------------------------------------------------
# Fixtures de dados reutilizáveis
# ---------------------------------------------------------------------------
@pytest.fixture
def tarefas_validas_mistas() -> list[dict]:
    """Fixture: lista com tarefas válidas de prioridades e status variados.

    Composição:
        - Tarefa 1 (alta, concluida): 48h de duração, entregue no prazo.
        - Tarefa 2 (media, concluida): 24h de duração, entregue com atraso.
        - Tarefa 3 (baixa, pendente): sem data de conclusão.
        - Tarefa 4 (alta, concluida): 72h de duração, sem data_limite.
    """
    return [
        {
            "id": 1,
            "titulo": "Implementar autenticação JWT",
            "prioridade": "alta",
            "data_criacao": datetime(2024, 1, 1, 8, 0),
            "data_conclusao": datetime(2024, 1, 3, 8, 0),  # 48h depois
            "data_limite": datetime(2024, 1, 4, 8, 0),     # dentro do prazo
            "status": "concluida",
        },
        {
            "id": 2,
            "titulo": "Refatorar módulo de relatórios",
            "prioridade": "media",
            "data_criacao": datetime(2024, 1, 5, 9, 0),
            "data_conclusao": datetime(2024, 1, 6, 9, 0),  # 24h depois
            "data_limite": datetime(2024, 1, 5, 18, 0),    # atrasada
            "status": "concluida",
        },
        {
            "id": 3,
            "titulo": "Documentar API pública",
            "prioridade": "baixa",
            "data_criacao": datetime(2024, 1, 7, 10, 0),
            "data_conclusao": None,
            "status": "pendente",
        },
        {
            "id": 4,
            "titulo": "Otimizar queries do banco de dados",
            "prioridade": "alta",
            "data_criacao": datetime(2024, 1, 2, 6, 0),
            "data_conclusao": datetime(2024, 1, 5, 6, 0),  # 72h depois
            "status": "concluida",
        },
    ]


@pytest.fixture
def tarefa_data_inconsistente() -> dict:
    """Fixture: tarefa com data_conclusao anterior a data_criacao."""
    return {
        "id": 99,
        "titulo": "Tarefa com dado corrompido",
        "prioridade": "alta",
        "data_criacao": datetime(2024, 3, 10, 12, 0),
        "data_conclusao": datetime(2024, 3, 8, 12, 0),  # 2 dias ANTES da criação
        "status": "concluida",
    }


# ---------------------------------------------------------------------------
# CENÁRIO 1 — Caminho Feliz (Happy Path)
# ---------------------------------------------------------------------------
class TestCenario1CaminhoFeliz:
    """Valida o cálculo correto de todas as métricas para dados válidos."""

    def test_total_tarefas(self, tarefas_validas_mistas: list[dict]) -> None:
        """Dado tarefas válidas, o total deve ser igual ao tamanho da lista."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        assert resultado["total_tarefas"] == 4

    def test_total_concluidas(self, tarefas_validas_mistas: list[dict]) -> None:
        """Dado tarefas mistas, deve contar apenas as com status 'concluida'."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        assert resultado["total_concluidas"] == 3

    def test_total_pendentes(self, tarefas_validas_mistas: list[dict]) -> None:
        """Dado tarefas mistas, deve contar apenas as com status 'pendente'."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        assert resultado["total_pendentes"] == 1

    def test_tempo_medio_conclusao_horas(self, tarefas_validas_mistas: list[dict]) -> None:
        """O tempo médio deve ser (48 + 24 + 72) / 3 = 48.0 horas."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        esperado = (48.0 + 24.0 + 72.0) / 3  # 48.0h
        assert resultado["tempo_medio_conclusao_horas"] == pytest.approx(esperado, rel=1e-6)

    def test_taxa_atraso_percentual(self, tarefas_validas_mistas: list[dict]) -> None:
        """Taxa de atraso: 1 de 2 tarefas com data_limite atrasadas = 50.0%."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        assert resultado["taxa_atraso_percentual"] == pytest.approx(50.0, rel=1e-6)

    def test_indicadores_prioridade_alta(self, tarefas_validas_mistas: list[dict]) -> None:
        """Prioridade 'alta' deve ter 2 concluídas, média de (48+72)/2 = 60h."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        alta = resultado["indicadores_prioridade"]["alta"]
        assert alta["total"] == 2
        assert alta["concluidas"] == 2
        assert alta["pendentes"] == 0
        assert alta["tempo_medio_conclusao_horas"] == pytest.approx(60.0, rel=1e-6)

    def test_indicadores_prioridade_media(self, tarefas_validas_mistas: list[dict]) -> None:
        """Prioridade 'media' deve ter 1 concluída com média de 24h."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        media = resultado["indicadores_prioridade"]["media"]
        assert media["total"] == 1
        assert media["concluidas"] == 1
        assert media["pendentes"] == 0
        assert media["tempo_medio_conclusao_horas"] == pytest.approx(24.0, rel=1e-6)

    def test_indicadores_prioridade_baixa(self, tarefas_validas_mistas: list[dict]) -> None:
        """Prioridade 'baixa' deve ter 0 concluídas e média 0.0h (sem divisão por zero)."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        baixa = resultado["indicadores_prioridade"]["baixa"]
        assert baixa["total"] == 1
        assert baixa["concluidas"] == 0
        assert baixa["pendentes"] == 1
        assert baixa["tempo_medio_conclusao_horas"] == pytest.approx(0.0, abs=1e-9)

    def test_estrutura_chaves_resultado(self, tarefas_validas_mistas: list[dict]) -> None:
        """O resultado deve conter exatamente as chaves definidas no contrato SDD."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        chaves_esperadas = {
            "total_tarefas",
            "total_concluidas",
            "total_pendentes",
            "tempo_medio_conclusao_horas",
            "taxa_atraso_percentual",
            "indicadores_prioridade",
        }
        assert set(resultado.keys()) == chaves_esperadas

    def test_indicadores_prioridade_contem_todas_as_prioridades(
        self, tarefas_validas_mistas: list[dict]
    ) -> None:
        """indicadores_prioridade deve conter as chaves 'alta', 'media' e 'baixa'."""
        resultado = analyze_tasks(tarefas_validas_mistas)
        assert set(resultado["indicadores_prioridade"].keys()) == {"alta", "media", "baixa"}


# ---------------------------------------------------------------------------
# CENÁRIO 2 — Dados Corrompidos / Exceções de Negócio
# ---------------------------------------------------------------------------
class TestCenario2DadosCorrempidos:
    """Valida que TaskValidationError é disparado para dados inválidos."""

    def test_data_conclusao_anterior_a_criacao_levanta_excecao(
        self, tarefa_data_inconsistente: dict
    ) -> None:
        """Dado data_conclusao < data_criacao, deve levantar TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            analyze_tasks([tarefa_data_inconsistente])

        assert "Inconsistência temporal" in str(exc_info.value)

    def test_excecao_contem_id_da_tarefa_corrompida(
        self, tarefa_data_inconsistente: dict
    ) -> None:
        """A mensagem de erro deve identificar o ID da tarefa problemática."""
        with pytest.raises(TaskValidationError) as exc_info:
            analyze_tasks([tarefa_data_inconsistente])

        assert "99" in str(exc_info.value)

    def test_prioridade_invalida_levanta_excecao(self) -> None:
        """Dado prioridade fora do domínio, deve levantar TaskValidationError."""
        tarefa_invalida = {
            "id": 10,
            "titulo": "Tarefa com prioridade errada",
            "prioridade": "urgente",  # valor fora do domínio
            "data_criacao": datetime(2024, 2, 1),
            "data_conclusao": datetime(2024, 2, 2),
            "status": "concluida",
        }
        with pytest.raises(TaskValidationError):
            analyze_tasks([tarefa_invalida])

    def test_status_invalido_levanta_excecao(self) -> None:
        """Dado status fora do domínio, deve levantar TaskValidationError."""
        tarefa_invalida = {
            "id": 11,
            "titulo": "Tarefa com status errado",
            "prioridade": "alta",
            "data_criacao": datetime(2024, 2, 1),
            "data_conclusao": datetime(2024, 2, 2),
            "status": "em_andamento",  # valor fora do domínio
        }
        with pytest.raises(TaskValidationError):
            analyze_tasks([tarefa_invalida])

    def test_id_nulo_levanta_excecao(self) -> None:
        """Dado id=None, deve levantar TaskValidationError."""
        tarefa_invalida = {
            "id": None,
            "titulo": "Tarefa sem ID",
            "prioridade": "media",
            "data_criacao": datetime(2024, 2, 1),
            "data_conclusao": datetime(2024, 2, 2),
            "status": "concluida",
        }
        with pytest.raises(TaskValidationError):
            analyze_tasks([tarefa_invalida])

    def test_excecao_e_instancia_de_exception(
        self, tarefa_data_inconsistente: dict
    ) -> None:
        """TaskValidationError deve ser subclasse de Exception (boa prática)."""
        with pytest.raises(Exception):
            analyze_tasks([tarefa_data_inconsistente])


# ---------------------------------------------------------------------------
# CASOS DE BORDA — Entradas Extremas / Divisão por Zero
# ---------------------------------------------------------------------------
class TestCasosDeBorda:
    """Valida comportamento estável em entradas extremas, sem exceções indevidas."""

    def test_lista_vazia_retorna_zeros(self) -> None:
        """Dado lista vazia, todas as métricas numéricas devem ser zero."""
        resultado = analyze_tasks([])

        assert resultado["total_tarefas"] == 0
        assert resultado["total_concluidas"] == 0
        assert resultado["total_pendentes"] == 0
        assert resultado["tempo_medio_conclusao_horas"] == pytest.approx(0.0, abs=1e-9)
        assert resultado["taxa_atraso_percentual"] == pytest.approx(0.0, abs=1e-9)

    def test_lista_vazia_nao_levanta_excecao(self) -> None:
        """Dado lista vazia, a função não deve levantar nenhuma exceção."""
        try:
            analyze_tasks([])
        except Exception as erro:
            pytest.fail(f"analyze_tasks([]) levantou exceção inesperada: {erro}")

    def test_somente_pendentes_tempo_medio_zero(self) -> None:
        """Dado apenas tarefas pendentes, tempo_medio deve ser 0.0 sem exceção."""
        tarefas_pendentes = [
            {
                "id": i,
                "titulo": f"Tarefa pendente {i}",
                "prioridade": "alta",
                "data_criacao": datetime(2024, 1, i + 1),
                "data_conclusao": None,
                "status": "pendente",
            }
            for i in range(1, 4)
        ]
        resultado = analyze_tasks(tarefas_pendentes)

        assert resultado["total_tarefas"] == 3
        assert resultado["total_concluidas"] == 0
        assert resultado["total_pendentes"] == 3
        assert resultado["tempo_medio_conclusao_horas"] == pytest.approx(0.0, abs=1e-9)

    def test_somente_pendentes_taxa_atraso_zero(self) -> None:
        """Dado apenas tarefas pendentes (sem data_limite), taxa_atraso deve ser 0.0."""
        tarefas_pendentes = [
            {
                "id": 1,
                "titulo": "Tarefa pendente única",
                "prioridade": "baixa",
                "data_criacao": datetime(2024, 1, 1),
                "data_conclusao": None,
                "status": "pendente",
            }
        ]
        resultado = analyze_tasks(tarefas_pendentes)
        assert resultado["taxa_atraso_percentual"] == pytest.approx(0.0, abs=1e-9)

    def test_tarefa_unica_concluida_no_mesmo_instante(self) -> None:
        """Dado data_criacao == data_conclusao, tempo_medio deve ser 0.0h."""
        tarefa = {
            "id": 50,
            "titulo": "Tarefa instantânea",
            "prioridade": "media",
            "data_criacao": datetime(2024, 6, 15, 10, 0),
            "data_conclusao": datetime(2024, 6, 15, 10, 0),  # mesmo instante
            "status": "concluida",
        }
        resultado = analyze_tasks([tarefa])
        assert resultado["tempo_medio_conclusao_horas"] == pytest.approx(0.0, abs=1e-9)
        assert resultado["total_concluidas"] == 1

    def test_sem_tarefas_com_prazo_taxa_atraso_zero(self) -> None:
        """Dado tarefas concluídas sem data_limite, taxa_atraso deve ser 0.0."""
        tarefa = {
            "id": 60,
            "titulo": "Tarefa sem prazo",
            "prioridade": "alta",
            "data_criacao": datetime(2024, 7, 1),
            "data_conclusao": datetime(2024, 7, 5),
            "status": "concluida",
        }
        resultado = analyze_tasks([tarefa])
        assert resultado["taxa_atraso_percentual"] == pytest.approx(0.0, abs=1e-9)

    def test_indicadores_prioridade_sem_tarefas_na_categoria(self) -> None:
        """Dado apenas tarefas 'alta', as categorias 'media' e 'baixa' devem ter zeros."""
        tarefa = {
            "id": 70,
            "titulo": "Apenas alta",
            "prioridade": "alta",
            "data_criacao": datetime(2024, 8, 1),
            "data_conclusao": datetime(2024, 8, 2),
            "status": "concluida",
        }
        resultado = analyze_tasks([tarefa])
        media = resultado["indicadores_prioridade"]["media"]
        baixa = resultado["indicadores_prioridade"]["baixa"]

        assert media["total"] == 0
        assert media["tempo_medio_conclusao_horas"] == pytest.approx(0.0, abs=1e-9)
        assert baixa["total"] == 0
        assert baixa["tempo_medio_conclusao_horas"] == pytest.approx(0.0, abs=1e-9)
