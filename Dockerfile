
# Dockerfile
FROM python:3.11-slim

# Ustaw metadane
LABEL maintainer="goLLM Team <team@gollm.dev>"
LABEL description="goLLM - Go Learn, Lead, Master!"
LABEL version="0.1.0"

# Zainstaluj systemowe zależności
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Utwórz użytkownika roboczego
RUN useradd -m -s /bin/bash gollm
USER gollm
WORKDIR /home/gollm

# Skopiuj pliki projektu
COPY --chown=gollm:gollm . /home/wronai/gollm/

# Przejdź do katalogu projektu
WORKDIR /home/wronai/gollm

# Zainstaluj goLLM w trybie deweloperskim
RUN pip install --user -e .[dev]

# Dodaj ścieżkę do PATH
ENV PATH="/home/gollm/.local/bin:${PATH}"

# Utwórz strukturę katalogów goLLM
RUN mkdir -p .gollm/{cache,templates,hooks}

# Ustaw zmienne środowiskowe
ENV PYTHONPATH="/home/wronai/gollm/src"
ENV goLLM_CONFIG="/home/wronai/gollm/gollm.json"

# Sprawdź instalację
RUN python -c "import gollm; print('goLLM imported successfully')"

# Domyślna komenda
CMD ["gollm", "--help"]