# Streaming odpowiedzi w goLLM

## Wprowadzenie

Streaming odpowiedzi to nowa funkcjonalność w goLLM, która znacząco poprawia wydajność generowania kodu poprzez wykorzystanie modularnego adaptera Ollama. Dzięki temu rozwiązaniu, odpowiedzi z modelu LLM są przetwarzane strumieniowo, co pozwala na:

- Szybsze generowanie kodu
- Zmniejszenie liczby błędów timeout
- Lepszą ekstrakcję kodu z odpowiedzi
- Bardziej responsywne działanie aplikacji

## Jak to działa?

Modularny adapter Ollama implementuje obsługę streamingu, która pozwala na przetwarzanie odpowiedzi z modelu LLM w czasie rzeczywistym, bez konieczności oczekiwania na całą odpowiedź. Proces wygląda następująco:

1. Zapytanie jest wysyłane do modelu LLM
2. Odpowiedź jest przetwarzana strumieniowo, w miarę jak jest generowana
3. Każdy fragment odpowiedzi jest natychmiast przetwarzany i dodawany do pełnej odpowiedzi
4. Po zakończeniu generowania, pełna odpowiedź jest walidowana i zwracana

## Jak używać streamingu?

### Przez CLI

Aby włączyć streaming w interfejsie wiersza poleceń, użyj parametru `--adapter-type modular`:

```bash
# Generowanie kodu ze streamingiem
gollm generate "Stwórz klasę użytkownika" --adapter-type modular
```

Streaming jest domyślnie włączony w modularnym adapterze, więc nie ma potrzeby dodatkowej konfiguracji.

### Przez API

Jeśli korzystasz z API goLLM w swoim kodzie, możesz włączyć streaming w następujący sposób:

```python
from gollm.main import GollmCore

# Inicjalizacja goLLM
gollm = GollmCore()

# Generowanie kodu ze streamingiem
result = await gollm.handle_code_generation(
    "Stwórz klasę użytkownika",
    context={
        'adapter_type': 'modular',
        'use_streaming': True
    }
)
```

## Konfiguracja

Możesz skonfigurować domyślne zachowanie streamingu w pliku konfiguracyjnym `gollm.json`:

```json
{
  "llm": {
    "provider": "ollama",
    "adapter_type": "modular",
    "use_streaming": true
  }
}
```

## Zalety streamingu

- **Szybsza responsywność**: Odpowiedzi są przetwarzane w czasie rzeczywistym, co eliminuje długie oczekiwanie na całą odpowiedź.
- **Mniej błędów timeout**: Dzięki strumieniowemu przetwarzaniu, ryzyko przekroczenia limitu czasu jest znacznie mniejsze.
- **Lepsza ekstrakcja kodu**: Modularny adapter lepiej radzi sobie z ekstrakcją kodu z odpowiedzi, co prowadzi do wyższej jakości generowanego kodu.
- **Mniejsze zużycie pamięci**: Przetwarzanie strumieniowe zmniejsza zużycie pamięci, co jest szczególnie ważne przy dużych odpowiedziach.

## Rozwiązywanie problemów

### Adapter nie przełącza się na modularny

Jeśli mimo użycia parametru `--adapter-type modular` adapter nie przełącza się na modularny, sprawdź:

1. Czy masz zainstalowane wszystkie zależności: `pip install gollm[llm]`
2. Czy zmienna środowiskowa `OLLAMA_ADAPTER_TYPE` nie jest ustawiona na inną wartość
3. Czy w pliku konfiguracyjnym `gollm.json` nie ma konfliktujących ustawień

### Problemy z wydajnością

Jeśli mimo włączenia streamingu nadal występują problemy z wydajnością:

1. Upewnij się, że używasz najnowszej wersji Ollama
2. Sprawdź, czy model LLM jest odpowiednio skonfigurowany
3. Rozważ użycie mniejszego modelu, jeśli masz ograniczone zasoby

## Kompatybilność

Streaming jest obecnie obsługiwany tylko przez modularny adapter Ollama. Inne adaptery (HTTP, gRPC) nie obsługują streamingu i będą działać w trybie standardowym.
