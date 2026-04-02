FROM python:3.12-slim

# System deps for building native extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Re-install in editable mode so the CLI entrypoint picks up local code
RUN pip install --no-cache-dir -e .

# Default results directory
RUN mkdir -p /app/reports
ENV TRADINGAGENTS_RESULTS_DIR=/app/reports

ENTRYPOINT ["tradingagents"]
CMD ["--help"]
