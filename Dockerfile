FROM python:3.13

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using uv (or pip if uv is not available)
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir fastapi uvicorn

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the FastAPI application
CMD ["uvicorn", "src.safety_guardrail.main:app", "--host", "0.0.0.0", "--port", "8000"]
