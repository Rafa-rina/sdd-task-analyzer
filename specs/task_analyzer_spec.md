# TaskAnalyzer — Especificação Técnica e Contrato SDD

**Módulo:** TaskAnalyzer  
**Autor:** Rafael Fernandes Durães (RA: 22452499)  
**Curso:** Ciência da Computação — CEUB (Asa Norte)  
**Versão:** 2.0 (Fase 2 — Bootcamp III)

---

## 1. Propósito do Módulo

O `TaskAnalyzer` é o núcleo de métricas e produtividade do sistema. Recebe uma lista de tarefas brutas e transforma os dados em indicadores úteis para gestão de projetos:

- Tempo médio de conclusão (geral e por prioridade)
- Taxa de atraso percentual
- Indicadores segmentados por prioridade (`baixa`, `media`, `alta`)

---

## 2. Contrato de Interface (Executável)

### 2.1 Entrada — `tarefas: list[dict]`

| Campo | Tipo | Regras |
|---|---|---|
| `id` | `int \| str` | Obrigatório; não pode ser `None` |
| `titulo` | `str` | Nome descritivo da tarefa |
| `prioridade` | `str` | Apenas: `'baixa'`, `'media'`, `'alta'` |
| `data_criacao` | `datetime` | Data de registro (YYYY-MM-DD HH:MM) |
| `data_conclusao` | `datetime \| None` | Obrigatório ser `>= data_criacao` se informado |
| `status` | `str` | Apenas: `'pendente'`, `'concluida'` |
| `data_limite` | `datetime \| None` | Opcional; referência para cálculo de atraso |

### 2.2 Saída — `dict`

| Chave | Tipo | Cálculo |
|---|---|---|
| `total_tarefas` | `int` | `len(tarefas)` |
| `total_concluidas` | `int` | Count de `status == 'concluida'` |
| `total_pendentes` | `int` | Count de `status == 'pendente'` |
| `tempo_medio_conclusao_horas` | `float` | Média de `(data_conclusao - data_criacao)` em horas; apenas concluídas; `0.0` se nenhuma |
| `taxa_atraso_percentual` | `float` | `(concluídas após data_limite / total com data_limite) * 100`; `0.0` se sem prazo |
| `indicadores_prioridade` | `dict` | Sub-dicionário por `'alta'`, `'media'`, `'baixa'` |

#### Estrutura de `indicadores_prioridade[prioridade]`:

```python
{
    "total": int,
    "concluidas": int,
    "pendentes": int,
    "soma_horas_conclusao": float,     # acumulador interno
    "tempo_medio_conclusao_horas": float,
}
```

---

## 3. Restrições Críticas de Negócio

1. **`tempo_medio_conclusao_horas`** considera **apenas** tarefas com `status == 'concluida'`.
2. **Divisão por zero** deve ser prevenida: retornar `0.0` se não houver tarefas em uma categoria.
3. **Inconsistência temporal** (`data_conclusao < data_criacao`) invalida a tarefa e dispara `TaskValidationError`.
4. Todo processamento ocorre **em memória** — nenhuma persistência em disco é permitida.

---

## 4. Cenários de Aceite BDD (Dado-Quando-Então)

### Cenário 1 — Caminho Feliz

```
Dado  que envio uma lista com tarefas válidas misturando prioridades e status
       (algumas pendentes, outras concluídas, algumas com data_limite)
Quando o TaskAnalyzer processar os dados
Então deve retornar:
       - total_tarefas    = len(lista)
       - total_concluidas = count(status='concluida')
       - total_pendentes  = count(status='pendente')
       - tempo_medio_conclusao_horas = média das horas de conclusão (só concluídas)
       - taxa_atraso_percentual = (atrasadas / com_prazo) * 100
       - indicadores_prioridade com totais e médias corretos por categoria
```

### Cenário 2 — Dados Corrompidos

```
Dado  que a lista contém uma tarefa com data_conclusao < data_criacao
Quando o TaskAnalyzer tentar processar
Então deve levantar TaskValidationError com mensagem clara contendo o task_id
      E NÃO deve travar a aplicação silenciosamente
```

### Cenário de Borda — Lista Vazia

```
Dado  que a lista de tarefas está vazia []
Quando o TaskAnalyzer processar
Então deve retornar todas as métricas numéricas como 0 ou 0.0
      E NÃO deve levantar nenhuma exceção
```

### Cenário de Borda — Somente Pendentes

```
Dado  que todas as tarefas têm status='pendente'
Quando o TaskAnalyzer processar
Então tempo_medio_conclusao_horas deve ser 0.0
      E taxa_atraso_percentual deve ser 0.0
      E NÃO deve levantar nenhuma exceção
```

---

## 5. Exceção de Negócio: `TaskValidationError`

```python
class TaskValidationError(Exception):
    def __init__(self, mensagem: str, task_id: int | str | None = None) -> None:
        ...
```

**Disparada quando:**
- `data_conclusao < data_criacao`
- `prioridade` fora de `{'baixa', 'media', 'alta'}`
- `status` fora de `{'pendente', 'concluida'}`
- `id` é `None`

---

## 6. Função Principal

```python
def analyze_tasks(tarefas: list[dict]) -> dict:
    """Analisa lista de tarefas e retorna métricas consolidadas."""
    ...
```

**Assinatura imutável** — o nome `analyze_tasks` e o parâmetro `tarefas` não podem ser alterados.

---

## 7. Estrutura de Arquivos

```
sdd-task-analyzer/
├── README.md
├── CONTEXT_RULES.md
├── requirements.txt
├── .gitignore
├── specs/
│   └── task_analyzer_spec.md   ← este arquivo
├── tests/
│   └── test_harness.py
└── src/
    └── task_analyzer.py
```
