
# Dockerfile
FROM python:3.11-slim

# Ustaw metadane
LABEL maintainer="SPYQ Team <team@spyq.dev>"
LABEL description="SPYQ - Smart Python Quality Guardian"
LABEL version="0.1.0"

# Zainstaluj systemowe zależności
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Utwórz użytkownika roboczego
RUN useradd -m -s /bin/bash spyq
USER spyq
WORKDIR /home/spyq

# Skopiuj pliki projektu
COPY --chown=spyq:spyq . /home/spyq/spyq/

# Przejdź do katalogu projektu
WORKDIR /home/spyq/spyq

# Zainstaluj SPYQ w trybie deweloperskim
RUN pip install --user -e .[dev]

# Dodaj ścieżkę do PATH
ENV PATH="/home/spyq/.local/bin:${PATH}"

# Utwórz strukturę katalogów SPYQ
RUN mkdir -p .spyq/{cache,templates,hooks}

# Ustaw zmienne środowiskowe
ENV PYTHONPATH="/home/spyq/spyq/src"
ENV SPYQ_CONFIG="/home/spyq/spyq/spyq.json"

# Sprawdź instalację
RUN python -c "import spyq; print('SPYQ imported successfully')"

# Domyślna komenda
CMD ["spyq", "--help"]