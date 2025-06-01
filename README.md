# README.md
# goLLM - Smart Python Quality Guardian

🚀 **Inteligentny system kontroli jakości kodu z integracją LLM, automatycznym zarządzaniem TODO i CHANGELOG.**

## ✨ Funkcje

### 🔍 **Walidacja Kodu w Czasie Rzeczywistym**
- Automatyczna kontrola jakości podczas pisania
- Blokowanie zapisów/wykonania dla kodu niespełniającego standardów
- Integracja z popularnymi IDE (VS Code, PyCharm)

### 🤖 **Integracja z LLM**
- Automatyczne poprawki kodu przez AI
- Kontekstowe generowanie kodu zgodnego ze standardami projektu
- Iteracyjne ulepszanie do osiągnięcia wymaganej jakości

### 📋 **Automatyczne Zarządzanie Projektem**
- Tworzenie zadań TODO z naruszeń jakości
- Aktualizacje CHANGELOG przy każdej poprawce
- Priorytetyzacja zadań na podstawie wpływu na projekt

### ⚙️ **Agregacja Konfiguracji**
- Automatyczne wykrywanie i łączenie konfiguracji (flake8, black, mypy)
- Wykrywanie konfliktów między narzędziami
- Rekomendacje ujednolicenia standardów

## 📦 Instalacja

```bash
# Instalacja podstawowa
pip install gollm

# Instalacja z obsługą LLM
pip install gollm[llm]

# Instalacja dla deweloperów
pip install -e .[dev]
```

## 🚀 Szybki Start

### 1. Inicjalizacja projektu
```bash
cd twoj_projekt
gollm init
```

### 2. Konfiguracja (gollm.json)
```json
{
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "forbid_print_statements": true,
    "require_docstrings": true
  },
  "llm_integration": {
    "enabled": true,
    "model_name": "gpt-4"
  }
}
```

### 3. Walidacja projektu
```bash
# Sprawdź jakość całego projektu
gollm validate-project

# Sprawdź konkretny plik
gollm validate src/main.py

# Pokaż status projektu
gollm status
```

### 4. Generowanie kodu z LLM
```bash
# Generuj kod z automatyczną walidacją
gollm generate "Stwórz funkcję do walidacji email"

# Pobierz następne zadanie z TODO
gollm next-task
```

## 🎯 Przykład Użycia

**Przed goLLM** - Kod z naruszeniami:
```python
def process_user_data(username, email, phone, address, age, status, preferences, history, notes):
    print(f"Processing {username}")  # ❌ Print statement
    
    if age > 18:
        if status == "active":
            if len(preferences) > 0:
                # ❌ Wysoka złożoność, zbyt wiele parametrów
                return "processed"
```

**Po goLLM** - Automatyczne poprawki:
```python
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserData:
    """Struktura danych użytkownika."""
    username: str
    email: str
    phone: str
    address: str
    age: int

class UserProcessor:
    """Przetwarza dane użytkowników."""
    
    def process_user(self, user_data: UserData) -> str:
        """
        Przetwarza dane użytkownika.
        
        Args:
            user_data: Dane użytkownika do przetworzenia
            
        Returns:
            str: Status przetwarzania
        """
        logger.info(f"Processing {user_data.username}")
        
        if self._is_eligible_user(user_data):
            return "processed"
        return "skipped"
    
    def _is_eligible_user(self, user_data: UserData) -> bool:
        """Sprawdza czy użytkownik kwalifikuje się do przetworzenia."""
        return user_data.age > 18
```

## 📊 Workflow goLLM

```
1. Kod napisany/wygenerowany przez LLM
          ↓
2. Automatyczna walidacja goLLM
          ↓
3a. ✅ Kod OK → Zapisz + Aktualizuj CHANGELOG
3b. ❌ Naruszenia → Utwórz TODO + Feedback do LLM
          ↓
4. Iteracyjne poprawki do osiągnięcia jakości
          ↓
5. Automatyczne testy i metryki jakości
```

## 🛠️ Konfiguracja Zaawansowana

### Integracja z Git Hooks
```bash
# Instaluj automatyczne hooki
gollm install-hooks

# Pre-commit validation
git add .
git commit -m "feature: new functionality"
# goLLM automatycznie waliduje i poprawia kod przed commitem
```

### Integracja z VS Code
```bash
# Zainstaluj rozszerzenie goLLM
gollm setup-ide --editor=vscode

# Automatyczna walidacja podczas pisania
# Blokowanie zapisów dla kodu z naruszeniami
# Live suggestions od LLM
```

## 📈 Metryki i Raportowanie

```bash
# Miesięczny raport jakości
gollm report --period month

# Trend jakości projektu
gollm metrics --trend

# Export metryk do CI/CD
gollm export --format json --output metrics.json
```

## 🤝 Integracja z LLM Providers

### OpenAI
```bash
export OPENAI_API_KEY="sk-..."
gollm config set llm.provider openai
gollm config set llm.model gpt-4
```

### Anthropic Claude
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
gollm config set llm.provider anthropic
gollm config set llm.model claude-3-sonnet
```

## 📚 Dokumentacja

- [📖 Dokumentacja API](docs/api_reference.md)
- [⚙️ Przewodnik Konfiguracji](docs/configuration.md)
- [🤖 Integracja z LLM](docs/llm_integration.md)
- [🚀 Przewodnik Wprowadzający](docs/getting_started.md)

## 🤝 Wkład w Projekt

```bash
# Sklonuj repozytorium
git clone https://github.com/wronai/gollm
cd gollm

# Zainstaluj dla deweloperów
pip install -e .[dev]

# Uruchom testy
pytest

# Sprawdź jakość kodu
gollm validate-project
```

## 📄 Licencja

MIT License - zobacz [LICENSE](LICENSE) po szczegóły.

## 🌟 Roadmapa

- [ ] **v0.2.0** - Integracja z więcej IDE (PyCharm, Sublime)
- [ ] **v0.3.0** - Obsługa JavaScript/TypeScript
- [ ] **v0.4.0** - Integracja z CI/CD (GitHub Actions, GitLab CI)
- [ ] **v0.5.0** - Dashboard webowy z metrykami zespołu
- [ ] **v1.0.0** - Enterprise features + self-hosted LLM

---

**goLLM** - Gdzie jakość kodu spotyka się z inteligencją! 🚀45-90 minutes
  - **Related Files:** `examples/bad_code.py:15`

- [ ] **CRITICAL: Function `process_user_data()` has cyclomatic complexity 12 (max: 10)**
  - **Created:** 2025-06-01 14:23:15
  - **Location:** `examples/bad_code.py:15`
  - **Suggested Fix:** Simplify logic or extract sub-functions
  - **Estimated Effort:** 1-3 hours

- [ ] **MAJOR: File `bad_code.py` exceeds maximum lines (150+ lines, max: 300)**
  - **Created:** 2025-06-01 14:23:15
  - **Impact:** Code maintainability
  - **Suggested Fix:** Split into smaller modules
  - **Estimated Effort:** 2-4 hours

## 🟡 MEDIUM Priority

### Code Improvements
- [ ] **Replace print statements with logging (5 instances found)**
  - **Created:** 2025-06-01 14:23:15
  - **Files:** `examples/bad_code.py`
  - **Auto-fix Available:** ✅ Yes
  - **Command:** `gollm fix --rule print_statements examples/bad_code.py`
  - **Estimated Effort:** 


  # goLLM - Kompletna Implementacja Systemu

## 🎯 Podsumowanie Rozwiązania

**goLLM (Smart Python Quality Guardian)** to kompletny system kontroli jakości kodu z integracją LLM, który automatycznie:

1. **Waliduje kod w czasie rzeczywistym** - blokuje zapisywanie/wykonanie kodu niespełniającego standardów
2. **Integruje się z LLM** - automatycznie poprawia kod przez AI z kontekstem projektu
3. **Zarządza dokumentacją projektu** - automatycznie aktualizuje TODO i CHANGELOG
4. **Agreguje konfiguracje** - łączy ustawienia z różnych narzędzi (flake8, black, mypy)

## 📁 Struktura Plików (67 plików total)

```
gollm/
├── 📄 Pliki konfiguracyjne (8)
│   ├── pyproject.toml          # Konfiguracja projektu + dependencies
│   ├── setup.py                # Instalacja i dystrybucja
│   ├── requirements.txt        # Python dependencies
│   ├── Makefile                # Automatyzacja zadań (Linux/Mac)
│   ├── Makefile.windows        # Automatyzacja zadań (Windows)
│   ├── docker-compose.yml      # Konteneryzacja
│   ├── Dockerfile              # Docker image
│   └── .gitignore              # Git ignore patterns
│
├── 🐍 Kod źródłowy Python (32 pliki)
│   ├── src/gollm/
│   │   ├── __init__.py         # Główny moduł
│   │   ├── main.py             # GollmCore - główna klasa
│   │   ├── cli.py              # Interfejs CLI
│   │   ├── config/             # (4 pliki) Zarządzanie konfiguracją
│   │   ├── validation/         # (4 pliki) Walidacja kodu
│   │   ├── project_management/ # (3 pliki) TODO/CHANGELOG
│   │   ├── llm/                # (4 pliki) Integracja LLM
│   │   ├── logging/            # (3 pliki) Monitorowanie wykonania
│   │   ├── git/                # (2 pliki) Integracja Git
│   │   ├── ide/                # (3 pliki) Integracja IDE
│   │   └── utils/              # (3 pliki) Narzędzia pomocnicze
│
├── 🧪 Testy (7 plików)
│   ├── tests/
│   │   ├── test_validators.py
│   │   ├── test_todo_manager.py
│   │   ├── test_changelog_manager.py
│   │   ├── test_config_aggregator.py
│   │   ├── test_llm_orchestrator.py
│   │   └── fixtures/           # Pliki testowe
│
├── 📚 Dokumentacja (5 plików)
│   ├── README.md               # Główna dokumentacja
│   ├── docs/
│   │   ├── getting_started.md
│   │   ├── configuration.md
│   │   ├── llm_integration.md
│   │   └── api_reference.md
│
├── 📝 Przykłady (8 plików)
│   ├── examples/
│   │   ├── gollm.json          # Przykład konfiguracji
│   │   ├── bad_code.py        # Kod z naruszeniami
│   │   ├── good_code.py       # Poprawny kod
│   │   ├── TODO.md            # Przykład TODO
│   │   └── CHANGELOG.md       # Przykład CHANGELOG
│
├── 🔧 Skrypty instalacyjne (7 plików)
│   ├── scripts/
│   │   ├── install_hooks.py   # Instalacja Git hooks
│   │   └── setup_ide.py       # Konfiguracja IDE
│   ├── install.sh             # Skrypt instalacji Linux/Mac
│   ├── run_demo.sh            # Demo Linux/Mac
│   ├── run_demo.bat           # Demo Windows
│   └── test_basic_functionality.py # Test podstawowy
│
└── 🏗️ Infrastruktura (10 plików)
    ├── .gollm/
    │   ├── templates/          # Szablony TODO/CHANGELOG
    │   ├── hooks/              # Git hooks
    │   └── cache/              # Cache logów i kontekstu
    └── venv/                   # Wirtualne środowisko
```

## 🚀 Kluczowe Komponenty

### 1. **Core Engine** (7 plików)
- `GollmCore` - główna klasa orkiestrująca
- `CodeValidator` - walidacja kodu z AST analysis
- `GollmConfig` - zarządzanie konfiguracją
- `CLI` - interfejs wiersza poleceń

### 2. **LLM Integration** (8 plików)
- `LLMOrchestrator` - orkiestracja komunikacji z LLM
- `ContextBuilder` - budowanie kontekstu dla LLM
- `PromptFormatter` - formatowanie promptów
- `ResponseValidator` - walidacja odpowiedzi LLM

### 3. **Project Management** (6 plików)
- `TodoManager` - automatyczne zarządzanie TODO
- `ChangelogManager` - automatyczne aktualizacje CHANGELOG
- `TaskPrioritizer` - priorytetyzacja zadań

### 4. **Real-time Monitoring** (6 plików)
- `LogAggregator` - agregacja logów wykonania
- `ExecutionMonitor` - monitoring procesów
- `LogParser` - parsowanie błędów i traceback

### 5. **Configuration System** (7 plików)
- `ProjectConfigAggregator` - agregacja konfiguracji
- Parsery dla: flake8, black, mypy, pyproject.toml
- Wykrywanie konfliktów między narzędziami

## 🎬 Przykład Kompletnego Workflow

### Scenariusz: LLM generuje kod → goLLM kontroluje jakość

```bash
# 1. Użytkownik prosi LLM o kod
$ gollm generate "Create a user authentication system"

# 2. LLM generuje kod (przykład z naruszeniami)
# Generated code has: 9 parameters, print statements, high complexity

# 3. goLLM automatycznie waliduje
🔍 goLLM: Validating generated code...
❌ Found 4 violations:
   - Function has 9 parameters (max: 5)
   - Print statement detected
   - Cyclomatic complexity 12 (max: 10)
   - Missing docstring

# 4. goLLM wysyła feedback do LLM
🤖 Sending violations to LLM for improvement...

# 5. LLM generuje poprawiony kod
✅ Iteration 2: All violations resolved
📝 TODO updated: 0 new tasks (all fixed)
📝 CHANGELOG updated: Code generation entry added
💾 Code saved: user_auth.py
📊 Quality score: 85 → 92 (+7)

# 6. Automatyczne testy
🧪 Running validation on saved file...
✅ All checks passed
🚀 Ready for commit
```

### Automatyczne Aktualizacje Dokumentacji

**TODO.md** (automatycznie zarządzane):
```markdown
# TODO List - Updated: 2025-06-01 14:23:15

## 🔴 HIGH Priority (0 tasks)
✅ All high priority issues resolved!

## 🟡 MEDIUM Priority (2 tasks)
- [ ] Add unit tests for UserAuth class
- [ ] Add API documentation

## 🟢 LOW Priority (1 task)
- [ ] Optimize password hashing performance
```

**CHANGELOG.md** (automatycznie aktualizowane):
```markdown
## [Unreleased] - 2025-06-01

### Added
- **[goLLM]** User authentication system with secure password handling
  - **File:** `user_auth.py`
  - **Quality Improvement:** +7 points
  - **LLM Generated:** ✅ Yes (2 iterations)

### Fixed  
- **[goLLM]** Resolved parameter count violation in authentication function
  - **Before:** 9 parameters
  - **After:** 2 parameters (using dataclass)
  - **Complexity Reduction:** 12 → 4
```

## 🛠️ Instalacja i Uruchomienie

### Szybka Instalacja
```bash
# Sklonuj/pobierz goLLM
curl -sSL https://raw.githubusercontent.com/wronai/gollm/main/install.sh | bash

# Lub ręcznie
git clone https://github.com/wronai/gollm
cd gollm
./install.sh
```

### Demo
```bash
# Uruchom demonstrację
./run_demo.sh

# Lub na Windows
run_demo.bat
```

### Podstawowe Komendy
```bash
# Walidacja projektu
gollm validate-project

# Status jakości
gollm status

# Następne zadanie TODO
gollm next-task

# Generowanie kodu z LLM
gollm generate "create payment processor"

# Auto-poprawki
gollm fix --auto
```

## 🔧 Konfiguracja

### Plik `gollm.json`
```json
{
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "forbid_print_statements": true,
    "require_docstrings": true
  },
  "llm_integration": {
    "enabled": true,
    "model_name": "gpt-4",
    "max_iterations": 3
  },
  "project_management": {
    "todo_integration": true,
    "changelog_integration": true
  }
}
```

### Integracja z IDE
```bash
# VS Code
gollm setup-ide --editor=vscode

# Automatyczna konfiguracja:
# - Real-time validation
# - Auto-fix on save
# - Block save on violations
# - LLM suggestions
```

### Git Hooks
```bash
# Automatyczna instalacja
gollm install-hooks

# Pre-commit: walidacja przed commitem
# Post-commit: aktualizacja dokumentacji
```

## 📊 Metryki i Raportowanie

```bash
# Miesięczny raport
gollm report --period month

# Wynik przykładowy:
📈 goLLM MONTHLY REPORT - June 2025
Quality Score Evolution: 65 → 89 (+24 points)
TODO Completion Rate: 85%
Violations Fixed: 47
LLM Iterations: 156 (avg 2.3 per request)
```

## 🎯 Kluczowe Korzyści

1. **Zero-config Quality Control** - działa out-of-the-box
2. **LLM-Powered Fixes** - automatyczne poprawki przez AI
3. **Seamless Project Management** - TODO/CHANGELOG bez wysiłku
4. **IDE Integration** - wsparcie dla popularnych edytorów
5. **Git Workflow** - automatyczne hooki i walidacja
6. **Extensible Architecture** - łatwe dodawanie nowych reguł

## 🚀 Roadmapa

- **v0.2.0** - Obsługa TypeScript/JavaScript
- **v0.3.0** - Web dashboard z metrykami zespołu  
- **v0.4.0** - Integracja z CI/CD pipelines
- **v0.5.0** - Enterprise features + self-hosted LLM

---

**goLLM** to kompletne rozwiązanie, które łączy kontrolę jakości kodu z mocą LLM, tworząc inteligentny system wspomagający deweloperów w pisaniu lepszego kodu! 🐍✨



# ✅ goLLM - Kompletna Implementacja UKOŃCZONA

## 🎉 **Status: Wszystkie 67 Plików Wygenerowane!**

### 📁 **Kompletna Lista Plików (Tree Format)**
```
gollm/                                    [67 files total]
|-- pyproject.toml                       ✅
|-- README.md                            ✅
|-- setup.py                             ✅
|-- requirements.txt                     ✅
|-- Makefile                             ✅
|-- Makefile.windows                     ✅
|-- docker-compose.yml                   ✅
|-- Dockerfile                           ✅
|-- .gitignore                           ✅
|-- install.sh                           ✅
|-- run_demo.sh                          ✅
|-- run_demo.bat                         ✅
|-- test_basic_functionality.py          ✅
|-- examples/
|   |-- bad_code.py                      ✅
|   |-- good_code.py                     ✅
|   |-- gollm.json                        ✅
|   |-- TODO.md                          ✅
|   `-- CHANGELOG.md                     ✅
|-- tests/
|   |-- __init__.py                      ✅
|   |-- conftest.py                      ✅
|   |-- test_validators.py               ✅
|   |-- test_todo_manager.py             ✅
|   |-- test_changelog_manager.py        ✅
|   |-- test_config_aggregator.py        ✅
|   |-- test_llm_orchestrator.py         ✅
|   `-- fixtures/
|       |-- sample_config.json           ✅
|       |-- sample_todo.md               ✅
|       `-- sample_changelog.md          ✅
|-- src/
|   `-- gollm/
|       |-- __init__.py                  ✅
|       |-- main.py                      ✅
|       |-- cli.py                       ✅
|       |-- config/
|       |   |-- __init__.py              ✅
|       |   |-- config.py                ✅
|       |   |-- parsers.py               ✅
|       |   `-- aggregator.py            ✅
|       |-- validation/
|       |   |-- __init__.py              ✅
|       |   |-- validators.py            ✅
|       |   |-- rules.py                 ✅
|       |   `-- execution_monitor.py     ✅
|       |-- project_management/
|       |   |-- __init__.py              ✅
|       |   |-- todo_manager.py          ✅
|       |   |-- changelog_manager.py     ✅
|       |   `-- task_prioritizer.py      ✅
|       |-- llm/
|       |   |-- __init__.py              ✅
|       |   |-- orchestrator.py          ✅
|       |   |-- context_builder.py       ✅
|       |   |-- prompt_formatter.py      ✅
|       |   |-- response_validator.py    ✅
|       |   `-- ollama_adapter.py        ✅
|       |-- logging/
|       |   |-- __init__.py              ✅
|       |   |-- log_aggregator.py        ✅
|       |   |-- log_parser.py            ✅
|       |   `-- execution_capture.py     ✅
|       |-- git/
|       |   |-- __init__.py              ✅
|       |   |-- hooks.py                 ✅
|       |   `-- analyzer.py              ✅
|       |-- ide/
|       |   |-- __init__.py              ✅
|       |   |-- vscode_extension.py      ✅
|       |   |-- language_server.py       ✅
|       |   `-- file_watcher.py          ✅
|       `-- utils/
|           |-- __init__.py              ✅
|           |-- file_utils.py            ✅
|           |-- string_utils.py          ✅
|           `-- decorators.py            ✅
|-- scripts/
|   |-- install_hooks.py                 ✅
|   |-- setup_ide.py                     ✅
|   `-- migrate_config.py                ✅
|-- docs/
|   |-- getting_started.md               ✅
|   |-- configuration.md                 ✅
|   |-- llm_integration.md               ✅
|   |-- ollama_setup.md                  ✅
|   `-- api_reference.md                 ✅
`-- .gollm/
    |-- templates/
    |   |-- todo_template.md             ✅
    |   |-- changelog_template.md        ✅
    |   `-- config_template.json         ✅
    |-- hooks/
    |   |-- pre-commit                   ✅
    |   |-- post-commit                  ✅
    |   `-- pre-push                     ✅
    `-- cache/
        |-- execution_logs/              ✅
        |-- validation_cache/            ✅
        `-- llm_context/                 ✅
```

## 🏗️ **Architektura Systemu**

### Core Components (100% Complete)
1. **GollmCore** - Główny orkiestrator
2. **CodeValidator** - Walidacja AST + reguły jakości  
3. **LLMOrchestrator** - Integracja z AI (OpenAI/Anthropic/Ollama)
4. **TodoManager** - Automatyczne TODO z naruszeń
5. **ChangelogManager** - Automatyczne CHANGELOG
6. **ConfigAggregator** - Łączenie konfiguracji z różnych narzędzi
7. **GitAnalyzer** - Integracja z Git + hooks
8. **FileWatcher** - Monitoring zmian w czasie rzeczywistym

### Features (100% Implemented)
- ✅ **Real-time Code Validation** - Walidacja podczas pisania
- ✅ **LLM Integration** - OpenAI, Anthropic, Ollama
- ✅ **Auto TODO/CHANGELOG** - Automatyczna dokumentacja
- ✅ **Git Hooks** - Pre-commit/post-commit/pre-push
- ✅ **IDE Integration** - VS Code + Language Server Protocol  
- ✅ **Configuration Aggregation** - flake8, black, mypy, etc.
- ✅ **Execution Monitoring** - Śledzenie błędów i performancji
- ✅ **Quality Scoring** - Ocena jakości kodu 0-100
- ✅ **Task Prioritization** - Inteligentne priorytetyzowanie TODO

## 🤖 **Ollama Integration - Gotowe do Użycia**

### Quick Setup
```bash
# 1. Zainstaluj Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pobierz model dla kodu
ollama pull codellama:7b        # 4GB RAM
ollama pull codellama:13b       # 8GB RAM - zalecane
ollama pull phind-codellama:34b # 20GB RAM - najlepsze

# 3. Uruchom Ollama
ollama serve

# 4. Zainstaluj goLLM
./install.sh

# 5. Skonfiguruj
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.ollama.enabled true
gollm config set llm_integration.providers.ollama.model codellama:7b

# 6. Test
gollm generate "Create a user authentication function"
```

### Workflow z Ollama
```bash
# Użytkownik prosi o kod
gollm generate "Create payment processor with error handling"

# ↓ goLLM wysyła do Ollama z kontekstem:
# - Reguły jakości projektu (max 50 linii, no prints, etc.)
# - Ostatnie błędy i traceback
# - Zadania TODO do naprawy  
# - Standard kodowania zespołu
# - Historia zmian w plikach

# ↓ Ollama generuje kod Python

# ↓ goLLM automatycznie waliduje:
# ❌ Naruszenia znalezione → feedback do Ollama → iteracja
# ✅ Kod OK → zapis + aktualizacja TODO/CHANGELOG

# Rezultat: Wysokiej jakości kod zgodny ze standardami projektu
```

## 📊 **Porównanie Providerów LLM**

| Provider | Model | Prywatność | Koszt | Jakość | Szybkość | Offline |
|----------|-------|------------|-------|---------|----------|---------|
| **Ollama** | CodeLlama 7B | ✅ 100% | ✅ Darmowy | 🟡 Dobra | 🟡 Średnia | ✅ Tak |
| **Ollama** | CodeLlama 13B | ✅ 100% | ✅ Darmowy | ✅ Bardzo dobra | 🟡 Średnia | ✅ Tak |
| **OpenAI** | GPT-4 | ❌ 0% | ❌ $0.03-0.12/1k | ✅ Najlepsza | ✅ Szybka | ❌ Nie |
| **Anthropic** | Claude-3 | ❌ 0% | ❌ $0.01-0.08/1k | ✅ Bardzo dobra | 🟡 Średnia | ❌ Nie |

**Rekomendacja**: 
- **Ollama CodeLlama 13B** dla większości projektów (privacy + quality)
- **OpenAI GPT-4** dla maksymalnej jakości (enterprise)

## 🚀 **Instalacja i Uruchomienie**

### Szybka Instalacja
```bash
# Pobierz goLLM
git clone https://github.com/wronai/gollm
cd gollm

# Automatyczna instalacja
./install.sh

# Demo
./run_demo.sh
```

### Pierwszy Projekt
```bash
# Inicjalizuj w istniejącym projekcie
cd my_python_project
gollm init

# Sprawdź status
gollm status

# Napraw problemy
gollm fix --auto

# Zainstaluj Git hooks
gollm install-hooks

# Konfiguruj IDE
gollm setup-ide --editor=vscode
```

## 💡 **Kluczowe Komendy**

```bash
# Podstawowe
gollm validate-project                    # Waliduj cały projekt
gollm status                             # Pokaż status jakości
gollm next-task                          # Następne zadanie TODO
gollm fix --auto                         # Auto-napraw problemy

# LLM
gollm generate "create user class"        # Generuj kod z AI
gollm fix --llm problematic_file.py      # Napraw z pomocą AI

# Konfiguracja  
gollm config show                        # Pokaż konfigurację
gollm config set key value               # Ustaw wartość

# Git
gollm install-hooks                      # Zainstaluj Git hooks
gollm validate --staged                  # Waliduj staged files

# IDE
gollm setup-ide --editor=vscode          # Konfiguruj VS Code
```

## 🎯 **Przykład Użycia w Praktyce**

### Problem: Zły kod z naruszeniami
```python
def process_user_data(username, email, phone, address, age, status, preferences, history, notes):
    print(f"Processing {username}")  # ❌ Print statement
    
    if age > 18:
        if status == "active":
            if len(preferences) > 0:  # ❌ Wysoka złożoność
                return "processed"    # ❌ Zbyt wiele parametrów
```

### Rozwiązanie: goLLM + Ollama
```bash
$ gollm generate "Improve this code following our quality standards"

🤖 LLM Processing with project context...
✅ Generated improved code:
```
