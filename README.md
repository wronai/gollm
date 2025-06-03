![goLLM Logo](gollm.svg)

# goLLM - Go Learn, Lead, Master!

[![PyPI Version](https://img.shields.io/pypi/v/gollm?style=for-the-badge&logo=pypi&logoColor=white&label=version)](https://pypi.org/project/gollm/)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/wronai/gollm/actions)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen?style=for-the-badge&logo=read-the-docs&logoColor=white)](https://gollm.readthedocs.io)

> **Dlaczego goLLM?** - Bo wierzymy, że jakość kodu to nie luksus, a standard. goLLM to więcej niż narzędzie - to twój asystent w dążeniu do doskonałości programistycznej.

## 🚀 O projekcie

goLLM to zaawansowany system kontroli jakości kodu Python zintegrowany z modelami językowymi (LLM), który przekształca proces programowania w płynne doświadczenie, gdzie jakość kodu jest gwarantowana od pierwszego znaku.

## 📚 Dokumentacja

Pełna dokumentacja dostępna jest w języku angielskim:

- [Rozpoczęcie pracy](/docs/getting-started/installation.md) - Instalacja i szybki start
- [Funkcje](/docs/features/overview.md) - Przegląd funkcji
- [Użycie](/docs/features/usage.md) - Jak korzystać z goLLM
- [Przykłady](/docs/examples/README.md) - Przykłady użycia
- [Dokumentacja API](/docs/api/reference.md) - Szczegóły techniczne
- [Rozwój](/docs/development/contributing.md) - Jak współtworzyć projekt

## 💫 Najważniejsze funkcje

- 🔥 **Generowanie kodu** - Tworzenie kodu na podstawie opisu w języku naturalnym
- 🔍 **Walidacja kodu** - Automatyczne sprawdzanie jakości i poprawności kodu
- 📈 **Metryki jakości** - Śledzenie postępów i trendów
- 🚀 **Szybkie odpowiedzi** - Generowanie kodu z wykorzystaniem lokalnych modeli LLM
- 🤖 **Integracja z IDE** - Wsparcie dla VS Code i PyCharm
- 🔄 **Automatyczne poprawki** - Inteligentne sugestie napraw błędów

## ⚡ Szybki start

```bash
# Instalacja
pip install gollm[llm]

# Generowanie kodu
gollm generate "Napisz funkcję w Pythonie, która oblicza silnię"
```

## ⚙️ Użycie z parametrami (Usage with Parameters)

`gollm` oferuje szereg parametrów, które pozwalają dostosować proces generowania kodu do Twoich potrzeb.

### Podstawowe parametry generowania

-   **`--output-path <ścieżka>` lub `-o <ścieżka>`**: Określa ścieżkę, gdzie mają być zapisane wygenerowane pliki. Domyślnie tworzony jest katalog na podstawie Twojego zapytania.
    ```bash
    gollm generate "Stwórz klasę User" -o ./my_user_class
    ```

-   **`--iterations <liczba>` lub `-i <liczba>`**: Ustawia liczbę iteracji dla procesu generowania i poprawiania kodu. Wyższa liczba może prowadzić do lepszej jakości kodu, ale wydłuża czas generowania. Domyślnie: 6.
    ```bash
    gollm generate "Zaimplementuj algorytm sortowania bąbelkowego" -i 10
    ```

-   **`--fast`**: Tryb szybki. Używa minimalnej liczby iteracji (1) i uproszczonej walidacji, aby szybko uzyskać wynik. Przydatne do prostych zadań.
    ```bash
    gollm generate "Prosta funkcja dodająca dwie liczby" --fast
    ```

### Kontrola testów

-   **`--tests` / `--no-tests`**: Włącza lub wyłącza automatyczne generowanie testów jednostkowych dla wygenerowanego kodu. Domyślnie włączone (`--tests`).
    ```bash
    gollm generate "Klasa Kalkulator z podstawowymi operacjami" --no-tests
    ```

### Automatyczne uzupełnianie i poprawki

-   **`--auto-complete` / `--no-auto-complete`**: Włącza lub wyłącza automatyczne uzupełnianie niekompletnych funkcji. Domyślnie włączone (`--auto-complete`).
    ```bash
    gollm generate "Stwórz szkielet klasy do obsługi API" --no-auto-complete
    ```

-   **`--execute-test` / `--no-execute-test`**: Włącza lub wyłącza automatyczne testowanie wykonania wygenerowanego kodu. Domyślnie włączone (`--execute-test`).
    ```bash
    gollm generate "Skrypt przetwarzający pliki tekstowe" --no-execute-test
    ```

-   **`--auto-fix` / `--no-auto-fix`**: Włącza lub wyłącza automatyczne próby naprawy błędów wykrytych podczas testowania wykonania. Domyślnie włączone (`--auto-fix`).
    ```bash
    gollm generate "Funkcja operująca na listach, która może rzucać wyjątki" --no-auto-fix
    ```

-   **`--max-fix-attempts <liczba>`**: Maksymalna liczba prób automatycznej naprawy błędów wykonania. Domyślnie: 5.
    ```bash
    gollm generate "Skomplikowany algorytm z potencjalnymi błędami" --max-fix-attempts 10
    ```

### Konfiguracja modelu LLM

-   **`--adapter-type <typ>`**: Wybiera typ adaptera LLM (np. `ollama`, `openai`, `http`, `modular`). Domyślnie skonfigurowany w ustawieniach globalnych.
    ```bash
    gollm generate "Funkcja w JavaScript" --adapter-type openai
    ```

-   **`--model <nazwa_modelu>`**: Określa konkretny model LLM do użycia (np. `gpt-4`, `llama3`). Domyślnie skonfigurowany w ustawieniach globalnych lub adaptera.
    ```bash
    gollm generate "Stwórz wyrażenie regularne" --adapter-type ollama --model llama3:latest
    ```

-   **`--temperature <wartość>`**: Ustawia temperaturę dla generowania kodu (wpływa na kreatywność odpowiedzi). Wartość od 0.0 do 2.0.
    ```bash
    gollm generate "Napisz wiersz o programowaniu" --temperature 1.2
    ```

### Inne przydatne parametry

-   **`--context-files <plik1> <plik2> ...` lub `-c <plik1> <plik2> ...`**: Dołącza zawartość podanych plików jako kontekst do zapytania LLM.
    ```bash
    gollm generate "Dodaj nową metodę do istniejącej klasy" -c existing_class.py
    ```

-   **`--verbose` lub `-v`**: Włącza tryb szczegółowy, wyświetlając więcej informacji o procesie generowania.
    ```bash
    gollm generate "Debuguj ten fragment kodu" -v
    ```

Aby zobaczyć pełną listę dostępnych opcji, użyj polecenia:
```bash
gollm generate --help
```

## 🤝 Współtworzenie

Zapraszamy do współtworzenia projektu! Szczegóły znajdziesz w [przewodniku dla współtwórców](/docs/development/contributing.md).

## 📝 Licencja

Ten projekt jest dostępny na licencji Apache 2.0 - szczegóły w pliku [LICENSE](LICENSE).

## 🔗 Przydatne linki

- [Strona projektu](https://github.com/wronai/gollm)
- [Dokumentacja](https://gollm.readthedocs.io)
- [Zgłaszanie błędów](https://github.com/wronai/gollm/issues)
- [Dyskusje](https://github.com/wronai/gollm/discussions)

## 🤖 Wsparcie dla modeli

goLLM wspiera różne modele językowe, w tym:

- Lokalne modele przez Ollama (zalecane)
- OpenAI GPT-4/GPT-3.5
- Inne kompatybilne modele z interfejsem API

## 📦 Wymagania systemowe

- Python 3.8+
- 4GB+ wolnej pamięci RAM (więcej dla większych modeli)
- Połączenie z internetem (opcjonalne, tylko dla niektórych funkcji)

## 🌍 Wsparcie społeczności

Dołącz do naszej społeczności, aby zadawać pytania i dzielić się swoimi doświadczeniami:

- [GitHub Discussions](https://github.com/wronai/gollm/discussions)
- [Discord](https://discord.gg/example) (jeśli dostępny)

## 🔄 Ostatnie zmiany

Sprawdź [historię zmian](CHANGELOG.md), aby zobaczyć najnowsze aktualizacje i nowe funkcje.

## 📚 Dokumentacja

Pełna dokumentacja dostępna jest w [dokumentacji online](https://gollm.readthedocs.io).

### 📖 Przewodniki
- [Wprowadzenie](./docs/guides/getting_started.md) - Pierwsze kroki z goLLM
- [Konfiguracja projektu](./docs/configuration/README.md) - Szczegóły konfiguracji
- [Integracja z Ollama](./docs/guides/ollama_setup.md) - Jak używać lokalnych modeli LLM
- [Generowanie wielu plików](./docs/guides/multi_file_generation.md) - Zarządzanie złożonymi projektami
- [Streaming odpowiedzi](./docs/guides/streaming.md) - Szybsze generowanie kodu z modularnym adapterem

### 🛠️ API
- [Podstawowe funkcje](./docs/api/core.md) - Główne komponenty goLLM
- [Rozszerzenia](./docs/api/extensions.md) - Jak rozszerzać funkcjonalność
- [Interfejs wiersza poleceń](./docs/api/cli.md) - Pełna dokumentacja CLI

## 🛠️ Rozwój

### Konfiguracja środowiska deweloperskiego

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/wronai/gollm.git
   cd gollm
   ```

2. Utwórz i aktywuj środowisko wirtualne:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   # lub
   .\venv\Scripts\activate  # Windows
   ```

3. Zainstaluj zależności deweloperskie:
   ```bash
   pip install -e .[dev]
   ```

### Uruchamianie testów

```bash
# Uruchom wszystkie testy
pytest

# Uruchom testy z pokryciem kodu
pytest --cov=src tests/

# Wygeneruj raport HTML z pokryciem
pytest --cov=src --cov-report=html tests/
```

## 🤝 Współpraca

Wszelkie wkłady są mile widziane! Zobacz [przewodnik dla współpracowników](CONTRIBUTING.md), aby dowiedzieć się, jak możesz pomóc w rozwoju projektu.

## 📄 Licencja

Projekt jest dostępny na licencji [Apache 2.0](LICENSE).
```

## 📊 Korzyści z używania goLLM

### Dla programistów
- **Oszczędność czasu** - Automatyczne poprawki i sugestie
- **Nauka najlepszych praktyk** - Natychmiastowy feedback jakości kodu
- **Mniejsze obciążenie code review** - Mniej błędów trafia do recenzji

### Dla zespołów
- **Spójność kodu** - Jednolite standardy w całym projekcie
- **Łatwiejsze wdrażanie nowych członków** - Automatyczne egzekwowanie standardów
- **Lepsza jakość kodu** - Systematyczne eliminowanie antywzorców

### Dla firmy
- **Niższe koszty utrzymania** - Lepsza jakość kodu = mniej bugów
- **Szybsze wdrażanie** - Zautomatyzowane procesy kontroli jakości
- **Większa wydajność zespołu** - Mniej czasu na poprawki, więcej na rozwój

## 🔄 Jak to działa?

goLLM działa w oparciu o zaawansowany system analizy kodu, który łączy w sobie:

1. **Statyczną analizę kodu** - Wykrywanie potencjalnych błędów i antywzorców
2. **Dynamiczną analizę** - Śledzenie wykonania kodu w czasie rzeczywistym
3. **Integrację z LLM** - Kontekstowe sugestie i automatyzacja zadań
4. **Automatyczne raportowanie** - Kompleksowe metryki jakości kodu

### Przykładowy workflow

```mermaid
graph TD
    A[Nowy kod] --> B{Analiza goLLM}
    B -->|Błędy| C[Automatyczne poprawki]
    B -->|Ostrzeżenia| D[Sugestie ulepszeń]
    B -->|Krytyczne| E[Blokada zapisu]
    C --> F[Ponowna analiza]
    D --> G[Recenzja programisty]
    F -->|OK| H[Zatwierdź zmiany]
    G -->|Zaakceptowano| H
    H --> I[Aktualizacja CHANGELOG]
    I --> J[Integracja z systemem CI/CD]
```

## ⚙️ Konfiguracja

goLLM oferuje elastyczną konfigurację dopasowaną do potrzeb Twojego projektu. Podstawowa konfiguracja znajduje się w pliku `gollm.json`.

### Przykładowa konfiguracja

```json
{
  "version": "0.2.0",
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "max_cyclomatic_complexity": 10,
    "max_function_params": 5,
    "max_line_length": 88,
    "forbid_print_statements": true,
    "forbid_global_variables": true,
    "require_docstrings": true,
    "require_type_hints": false,
    "naming_convention": "snake_case"
  },
  "project_management": {
    "todo_integration": true,
    "auto_create_tasks": true,
    "changelog_integration": true
  },
  "llm_integration": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4"
  }
}
```

### Integracja z narzędziami deweloperskimi

#### Integracja z Narzędziami

GoLLM można zintegrować z istniejącymi narzędziami deweloperskimi poprzez konfigurację w pliku `gollm.json`. Aby uzyskać więcej informacji, sprawdź dokumentację konfiguracji.

```bash
# Sprawdź aktualną konfigurację
gollm config list

# Zmień ustawienia konfiguracji
gollm config set <klucz> <wartość>
```

#### CI/CD
```yaml
# Przykład dla GitHub Actions
name: goLLM Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install goLLM
      run: pip install gollm[llm]
    - name: Run validation
      run: gollm validate .
```

## 📊 Metryki i analiza

goLLM dostarcza szczegółowych metryk i analiz, które pomagają śledzić jakość kodu w czasie.

### Dostępne komendy

#### Metryki jakości kodu
```bash
# Pokaż aktualne metryki jakości kodu
gollm metrics
```

#### Trendy jakości w czasie
```bash
# Pokaż trendy jakości kodu w określonym okresie
gollm trend --period month
```

#### Status projektu
```bash
# Sprawdź aktualny status projektu i zdrowia kodu
gollm status
```

### Przykładowe metryki
- **Jakość kodu** - Ocena 0-100%
- **Pokrycie testami** - Procent kodu objętego testami
- **Złożoność cyklomatyczna** - Średnia złożoność metod
- **Dług techniczny** - Szacowany czas potrzebny na poprawę jakości

## 🤖 Integracja z modelami językowymi

goLLM może współpracować z różnymi dostawcami modeli językowych:

### OpenAI GPT
```bash
export OPENAI_API_KEY="twój-klucz"
gollm config set llm.provider openai
gollm config set llm.model gpt-4
```

### Anthropic Claude
```bash
export ANTHROPIC_API_KEY="twój-klucz"
gollm config set llm.provider anthropic
gollm config set llm.model claude-3-opus
```

### Ollama (lokalny)
```bash
gollm config set llm.provider ollama
gollm config set llm.model codellama:13b
```

## 🌐 Wsparcie społeczności

### Gdzie uzyskać pomoc?
- [Dokumentacja](https://gollm.readthedocs.io)
- [Issue Tracker](https://github.com/wronai/gollm/issues)
- [Dyskusje](https://github.com/wronai/gollm/discussions)
- [Przykłady użycia](https://github.com/wronai/gollm/examples)

### Jak możesz pomóc?
1. Zgłaszaj błędy i propozycje funkcji
2. Udostępniaj przykłady użycia
3. Pomagaj w tłumaczeniu dokumentacji
4. Rozwijaj projekt przez pull requesty

## 📜 Licencja

Projekt goLLM jest dostępny na licencji [Apache 2.0](LICENSE).

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

**goLLM (Go Learn, Lead, Master!)** to kompletny system kontroli jakości kodu z integracją LLM, który automatycznie:

1. **Waliduje kod w czasie rzeczywistym** - blokuje zapisywanie/wykonanie kodu niespełniającego standardów
2. **Integruje się z LLM** - automatycznie poprawia kod przez AI z kontekstem projektu
3. **Zarządza dokumentacją projektu** - automatycznie aktualizuje TODO i CHANGELOG
4. **Agreguje konfiguracje** - łączy ustawienia z różnych narzędzi (flake8, black, mypy)


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
gollm generate "create website simple with frontend, api and backend"

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

### Integracja z IDE i Narzędziami

GoLLM można zintegrować z IDE i narzędziami deweloperskimi poprzez konfigurację w pliku `gollm.json`.

```bash
# Sprawdź aktualną konfigurację
gollm config list

# Zmień ustawienia konfiguracji
gollm config set <klucz> <wartość>
```

Możliwe integracje:
- Walidacja kodu w czasie rzeczywistym
- Automatyczne poprawki przy zapisie
- Sugestie LLM w edytorze
- Integracja z systemem kontroli wersji

## 📊 Metryki i Raportowanie

```bash
# Pokaż aktualne metryki jakości kodu
gollm metrics

# Pokaż trendy jakości kodu w określonym okresie
gollm trend --period month

# Sprawdź status projektu i zdrowia kodu
gollm status

# Przykładowy wynik:
Quality Score: 89/100
Code Coverage: 78%
Cyclomatic Complexity: 2.4 (Good)
Technical Debt: 3.2 days
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
- **Ollama CodeLlama 13B** dla większości projektów (prywatność + jakość)
- **OpenAI GPT-4** dla maksymalnej jakości (rozwiązania enterprise)

## 💡 **Kluczowe Komendy**

```bash
# Podstawowe
gollm validate-project     # Waliduj cały projekt
gollm status              # Pokaż status jakości
gollm next-task           # Pokaż następne zadanie TODO
gollm fix --auto          # Automatyczna naprawa problemów

# Integracja z LLM
gollm generate "zadanie"  # Generuj kod z pomocą AI
gollm fix --llm plik.py  # Napraw kod z pomocą AI

# Więcej informacji
gollm --help              # Wyświetl dostępne komendy
```
