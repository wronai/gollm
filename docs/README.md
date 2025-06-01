# 📚 Dokumentacja goLLM

Witaj w dokumentacji goLLM! Ten katalog zawiera szczegółowe przewodniki i referencje dotyczące używania i rozszerzania goLLM.

## 📖 Spis treści

### Przewodniki
- [Wprowadzenie](./guides/getting_started.md) - Pierwsze kroki z goLLM
- [Konfiguracja projektu](./configuration/README.md) - Szczegóły konfiguracji
- [Integracja z Ollama](./guides/ollama_setup.md) - Jak używać lokalnych modeli LLM
- [Generowanie wielu plików](./guides/multi_file_generation.md) - Zarządzanie złożonymi projektami

### 🛠️ API
- [Podstawowe funkcje](./api/core.md) - Główne komponenty goLLM
- [Rozszerzenia](./api/extensions.md) - Jak rozszerzać funkcjonalność
- [Interfejs wiersza poleceń](./api/cli.md) - Pełna dokumentacja CLI

### ⚙️ Konfiguracja
- [Zaawansowane opcje](./configuration/advanced.md) - Szczegółowa konfiguracja
- [Reguły walidacji](./configuration/validation_rules.md) - Dostosowywanie zasad jakości kodu
- [Integracja z LLM](./configuration/llm_integration.md) - Konfiguracja modeli językowych
- [Zarządzanie projektem](./configuration/project_management.md) - Automatyzacja zadań

## 🚀 Szybki start

1. **Zainstaluj goLLM**
   ```bash
   pip install gollm[llm]
   ```

2. **Zainicjuj nowy projekt**
   ```bash
   mkdir moj-projekt
   cd moj-projekt
   gollm init
   ```

3. **Zapoznaj się z dokumentacją**
   - [Przewodnik wprowadzający](./guides/getting_started.md)
   - [Opcje konfiguracyjne](./configuration/README.md)
   - [Dokumentacja API](./api/README.md)

## Konwencje dokumentacji

- **Bloki kodu** pokazują przykłady użycia
- **Pogrubione terminy** oznaczają ważne pojęcia
- `Kod w tekście` reprezentuje polecenia i wartości konfiguracyjne
- 🔹 Ikony pomagają zidentyfikować różne typy treści

## Budowanie dokumentacji

Aby zbudować dokumentację lokalnie:

```bash
# Zainstaluj zależności dokumentacji
pip install -r docs/requirements.txt

# Zbuduj dokumentację
cd docs
make html

# View the docs
open _build/html/index.html
```

## Contributing

We welcome contributions to the documentation! Please see our [Contributing Guide](../CONTRIBUTING.md) for details.

## Need Help?

- [GitHub Issues](https://github.com/wronai/gollm/issues) - Report bugs or request features
- [Discussions](https://github.com/wronai/gollm/discussions) - Ask questions and share ideas
- [Examples](./examples/README.md) - Browse example projects
