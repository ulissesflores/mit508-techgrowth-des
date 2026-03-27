FROM python:3.11-slim

LABEL maintainer="Carlos Ulisses Flores"
LABEL description="TechGrowth DES — Simulação Estocástica Pipeline Kafka→Flink→Iceberg"
LABEL course="MIT-508 Data Platform Engineering (AGTU)"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p output

CMD ["python", "-m", "src.main"]
