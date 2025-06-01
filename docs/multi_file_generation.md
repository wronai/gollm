# Generowanie projektów wieloplikiowych w goLLM

goLLM oferuje zaawansowane możliwości generowania kompletnych projektów z wieloma plikami. Dzięki integracji z modelami językowymi, możesz łatwo tworzyć całe struktury projektów, takie jak strony internetowe, aplikacje webowe i biblioteki Pythona.

## 🚀 Szybki start

### Generowanie pojedynczego pliku

```bash
gollm generate "funkcja obliczająca silnię" -o math_utils.py
```

### Generowanie projektu strony internetowej

```bash
gollm generate "strona Flask z Reactem" -o moja_strona
```

### Generowanie złożonej aplikacji

```bash
gollm generate "aplikacja FastAPI z bazą danych i interfejsem użytkownika" -o moja_aplikacja
```

## 📁 Struktura generowanych projektów

goLLM automatycznie wykrywa typ projektu i generuje odpowiednią strukturę plików. Oto przykładowa struktura dla aplikacji webowej:

```
moja_aplikacja/
├── app.py                # Główna aplikacja
├── requirements.txt      # Zależności Pythona
├── static/              # Pliki statyczne (CSS, JS, obrazy)
│   ├── css/
│   └── js/
├── templates/           # Szablony HTML
│   ├── base.html
│   └── index.html
└── README.md            # Dokumentacja
```

## 🔍 Obsługiwane typy projektów

### Strony internetowe
- Generuje kompletne strony z HTML, CSS i JavaScript
- Obsługa popularnych frameworków frontendowych (React, Vue, itp.)
- Integracja z backendem (Flask, FastAPI, Django)

### Aplikacje webowe
- Pełna struktura projektu z podziałem na warstwy
- Gotowe endpointy API
- Przykładowe widoki i komponenty

### Biblioteki Pythona
- Struktura pakietu zgodna z najlepszymi praktykami
- Automatyczne generowanie `setup.py`/`pyproject.toml`
- Testy jednostkowe i dokumentacja

## ⚙️ Konfiguracja

Możesz dostosować generowanie projektów przez plik konfiguracyjny `gollm.json`:

```json
{
  "llm_integration": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4",
    "providers": {
      "openai": {
        "api_key": "twój_klucz_api"
      },
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "codellama:7b"
      }
    }
  }
}
```

## 📝 Przykłady użycia

### 1. Generowanie prostej strony

```bash
gollm generate "strona informacyjna o firmie z formularzem kontaktowym" -o strona_firmowa
```

### 2. Tworzenie API REST

```bash
gollm generate "API REST do zarządzania zadaniami z autentykacją JWT" -o task_manager_api
```

### 3. Budowa biblioteki Pythona

```bash
gollm generate "biblioteka do obsługi plików CSV z walidacją danych" -o csv_validator
```

## 🔄 Aktualizacja istniejących projektów

goLLM może również rozszerzać istniejące projekty o nowe funkcjonalności:

```bash
# Przejdź do katalogu projektu
cd istniejący_projekt

# Dodaj nową funkcjonalność
gollm generate "dodaj endpoint API do przetwarzania zdjęć"
```

## 🛠️ Rozwiązywanie problemów

### Brakujące zależności
Upewnij się, że masz zainstalowane wszystkie wymagane pakiety:

```bash
pip install gollm[llm]
```

### Problemy z generowaniem
Jeśli generowanie nie działa poprawnie:
1. Sprawdź połączenie z internetem
2. Upewnij się, że podałeś poprawny klucz API
3. Sprawdź logi błędów w konsoli

## 📚 Dodatkowe zasoby

- [Dokumentacja API](https://gollm.readthedocs.io)
- [Przykładowe projekty](https://github.com/wronai/gollm/examples)
- [Zgłaszanie błędów](https://github.com/wronai/gollm/issues)

---

**goLLM** - Twój asystent w generowaniu wysokiej jakości kodu! 🚀
