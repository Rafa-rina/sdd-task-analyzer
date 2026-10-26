# TaskAnalyzer

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![pytest](https://img.shields.io/badge/tested%20with-pytest-brightgreen.svg)](https://pytest.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Núcleo de métricas e produtividade para análise de tarefas de projetos.  
> Desenvolvido como projeto cumulativo do **Bootcamp III — Ciência da Computação (CEUB)**.

---

## 📋 Sobre o Projeto

O **TaskAnalyzer** recebe uma lista de tarefas brutas e as transforma em indicadores úteis para a gestão de projetos:

- ⏱️ **Tempo médio de conclusão** (geral e segmentado por prioridade)
- 📊 **Taxa de atraso percentual** (tarefas entregues após o prazo)
- 🗂️ **Indicadores por prioridade** (`baixa`, `media`, `alta`)

Todo o código foi gerado com auxílio de assistentes de IA (**Gemini / Claude**), guiados pelas regras de governança definidas em [`CONTEXT_RULES.md`](CONTEXT_RULES.md) e pelo contrato SDD em [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md).

---

## 🗂️ Estrutura do Repositório

```
sdd-task-analyzer/
├── README.md                    # Este arquivo
├── CONTEXT_RULES.md             # Regras de governança para agentes de IA
├── requirements.txt             # Dependências (pytest)
├── .gitignore                   # Arquivos ignorados pelo Git
├── specs/
│   └── task_analyzer_spec.md   # Contrato SDD completo
├── tests/
│   └── test_harness.py         # Suíte de testes automatizados (pytest)
└── src/
    └── task_analyzer.py        # Código-fonte gerado via IA e homologado
```

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11 ou superior
- pip

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/sdd-task-analyzer.git
cd sdd-task-analyzer
```

### 2. Crie e ative um ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute os testes

```bash
pytest tests/test_harness.py -v
```

Resultado esperado: **100% passed** ✅

---

## 📦 Docker

```bash
# Build image
docker build -t taskanalyzer .
# Run tests inside container
docker compose run taskanalyzer
```

## 🐳 Docker Compose

```bash
docker compose up --build
```

## 🤖 GitHub Actions CI

The workflow `.github/workflows/ci.yml` runs on pushes and pull requests to `main` and `develop` using Python 3.11 and executes the test suite.

## 📄 Relatório de Governança de IA

Consulte `docs/relatorio_governanca_ia.pdf` para detalhes sobre as regras de contexto, validação humana e rastreabilidade.

## 🧪 Exemplo de Uso

```python
from datetime import datetime
from src.task_analyzer import analyze_tasks

tarefas = [
    {
        "id": 1,
        "titulo": "Implementar autenticação",
        "prioridade": "alta",
        "data_criacao": datetime(2024, 1, 1, 8, 0),
        "data_conclusao": datetime(2024, 1, 3, 8, 0),  # 48h
        "data_limite": datetime(2024, 1, 4, 8, 0),
        "status": "concluida",
    },
    {
        "id": 2,
        "titulo": "Documentar API",
        "prioridade": "baixa",
        "data_criacao": datetime(2024, 1, 5),
        "data_conclusao": None,
        "status": "pendente",
    },
]

resultado = analyze_tasks(tarefas)
print(resultado)
# {
#   'total_tarefas': 2,
#   'total_concluidas': 1,
#   'total_pendentes': 1,
#   'tempo_medio_conclusao_horas': 48.0,
#   'taxa_atraso_percentual': 0.0,
#   'indicadores_prioridade': { 'alta': {...}, 'media': {...}, 'baixa': {...} }
# }
```

---

## 📐 Arquitetura e Decisões Técnicas

| Decisão | Justificativa |
|---|---|
| Python 3.11+ | Suporte a `type` aliases nativos e melhorias de performance |
| `logging` em vez de `print` | Rastreamento estruturado e configurável conforme CONTEXT_RULES |
| `TaskValidationError` customizada | Exceção de negócio clara, com `task_id` para diagnóstico |
| Divisão por zero preventiva | Função `_calcular_media_segura()` centraliza a proteção |
| Sem dependências de terceiros | Todo o código usa apenas a stdlib do Python |

---

## 🧾 Fases do Projeto

| Fase | Status | Descrição |
|---|---|---|
| Fase 1 | ✅ Concluída | Especificação SDD, Cenários BDD, CONTEXT_RULES, Vídeo |
| **Fase 2** | 🔄 **Atual** | Repositório GitHub, código via IA, Test Harness, PRs |
| Fase 3 | ⏳ Pendente | CI/CD (GitHub Actions), Docker, Relatório de Governança |

---

## 👤 Autor

**Rafael Fernandes Durães**  
RA: 22452499  
Ciência da Computação — CEUB (Asa Norte)  
📧 rafael.duraes@sempreceub.com
