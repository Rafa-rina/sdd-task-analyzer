# TaskAnalyzer — Regras de Governança para Agentes de IA

## Identificação

- **Autor:** Rafael Fernandes Durães (RA: 22452499)
- **Disciplina:** Bootcamp III — Ciência da Computação (CEUB - Asa Norte)
- **Versão:** 2.0 (Fase 2)

---

## 1. Propósito deste Arquivo

Este arquivo define o **AI Harness** — o conjunto de regras restritivas injetadas como contexto em qualquer assistente de IA (Gemini, ChatGPT, GitHub Copilot, Claude) que for utilizado para gerar ou modificar código neste repositório.

> **Princípio Central:** O assistente de IA é um gerador de código guiado por contrato. Ele **não** toma decisões de arquitetura por conta própria. Toda geração deve ser fiel ao contrato SDD em `specs/task_analyzer_spec.md`.

---

## 2. Diretrizes Arquiteturais (OBRIGATÓRIAS)

| Diretriz | Regra |
|---|---|
| **Linguagem** | Python 3.11+ como versão mínima e inegociável |
| **Tipagem Estática** | `type hints` em **100%** das funções, parâmetros e retornos |
| **Estilo** | PEP 8 rigoroso; linhas máx. 100 caracteres |
| **SRP** | Cada função resolve **um único problema**; funções pequenas e coesas |
| **Documentação** | Docstrings padrão **Google Style** obrigatórias em módulos, classes e funções públicas |
| **Logs** | Usar **exclusivamente** a biblioteca `logging` da stdlib; `print()` é proibido |
| **Nomenclatura** | Variáveis com nomes descritivos e semânticos; nenhuma letra solta (ex.: `x`, `i` só em loops explícitos) |
| **Tratamento de Erros** | Exceções específicas com mensagens claras; nunca `except Exception` genérico sem re-raise |

---

## 3. Restrições Explícitas — O Que É PROIBIDO

```
❌ NÃO importar bibliotecas de terceiros não autorizadas.
   Autorizadas: pytest (apenas em tests/), stdlib padrão (datetime, logging, typing, etc.)

❌ NÃO alterar, atalhar ou suavizar os cenários de teste em tests/test_harness.py.

❌ NÃO bagunçar a árvore de diretórios definida em specs/task_analyzer_spec.md.

❌ NÃO codificar persistência (arquivos locais, banco de dados, cache em disco).
   Tudo roda exclusivamente em memória.

❌ NÃO renomear funções ou parâmetros do contrato SDD:
   - Função principal: analyze_tasks(tarefas: list[dict]) -> dict
   - Exceção: TaskValidationError

❌ NÃO inserir código redundante, over-engineered ou gerar rotinas sem testes.

❌ NÃO deduzir ou inventar comportamentos não documentados no contrato SDD.

❌ NÃO usar f-strings de múltiplas linhas sem necessidade — prefira variáveis intermediárias.

❌ NÃO gerar código com divisão sem tratamento preventivo de zero.
```

---

## 4. Contrato de Interface Resumido (referência rápida)

### Entrada: `tarefas: list[dict]`

| Campo | Tipo | Regra |
|---|---|---|
| `id` | `int \| str` | Obrigatório, não nulo |
| `titulo` | `str` | Descritivo |
| `prioridade` | `str` | Apenas: `'baixa'`, `'media'`, `'alta'` |
| `data_criacao` | `datetime` | Obrigatória |
| `data_conclusao` | `datetime \| None` | Deve ser `>= data_criacao` se informada |
| `status` | `str` | Apenas: `'pendente'`, `'concluida'` |
| `data_limite` | `datetime \| None` | Opcional; usado para calcular taxa de atraso |

### Saída: `dict`

| Chave | Tipo | Descrição |
|---|---|---|
| `total_tarefas` | `int` | Total de tarefas recebidas |
| `total_concluidas` | `int` | Tarefas com status `'concluida'` |
| `total_pendentes` | `int` | Tarefas com status `'pendente'` |
| `tempo_medio_conclusao_horas` | `float` | Média de horas (apenas concluídas); `0.0` se nenhuma |
| `taxa_atraso_percentual` | `float` | % de tarefas entregues após `data_limite`; `0.0` se sem prazo |
| `indicadores_prioridade` | `dict` | Sub-dict por `'alta'`, `'media'`, `'baixa'` com totais e médias |

---

## 5. Regras Anti-Alucinação

Para **prevenir alucinações** do assistente de IA, o prompt deve sempre incluir:

1. **Ancoragem ao contrato:** "Implemente **exatamente** conforme o contrato SDD. Não adicione campos extras."
2. **Proibição de criatividade arquitetural:** "Não crie classes, módulos ou padrões além dos especificados."
3. **Verificação de tipo explícita:** "Valide tipos antes de qualquer operação aritmética."
4. **Validação pós-geração:** Após receber o código, executar `pytest tests/test_harness.py` — se falhar, o código é **rejeitado** sem merge.

---

## 6. Checklist de Homologação Humana (pré-merge)

Antes de qualquer `git merge` ou aprovação de Pull Request, o revisor humano deve confirmar:

- [ ] `pytest tests/test_harness.py` → **100% passed**
- [ ] Código usa `type hints` em todas as funções
- [ ] Nenhuma biblioteca de terceiros não autorizada importada
- [ ] Docstrings Google Style presentes em todas as funções públicas
- [ ] Nenhum `print()` no código de produção (`src/`)
- [ ] Nomes de funções e parâmetros idênticos ao contrato SDD
- [ ] Divisão por zero tratada em todos os cálculos de média
- [ ] Nenhuma persistência em disco codificada
- [ ] Mensagens de erro claras e identificam a tarefa problemática (com `task_id`)
