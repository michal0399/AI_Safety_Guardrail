FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using uv (or pip if uv is not available)
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir fastapi uvicorn

# Expose API port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "src.safety_guardrail.main:app", "--host", "0.0.0.0", "--port", "8000"]
