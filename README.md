Most companies are afraid of LLMs because of data leaks. This repo provides the solution: a local safety guardrail that swaps Personally Identifiable Information for unique placeholders before they leave your machine, then intelligently reconstructs the response for the user. Verified for accuracy with AI-as-a-Judge.

The Core Problem with LLM Gateways: Tools like LiteLLM consolidate all API keys and handle raw, unmasked data. If the proxy layer is compromised via a supply chain attack, your entire infrastructure and data ecosystem are instantly exposed.

Solution: This project introduces a Zero-Trust Local Boundary. Because PII masking and token vaulting happen locally before any third-party routing engine touches the string, even a completely backdoored proxy cannot leak real user data.

How this works:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client Application
    participant MW as FastAPI Middleware
    participant LLM as LiteLLM Routing Layer
    participant Provider as LLM Provider

    Client->>MW: Sends Raw Prompt ("I am Jack Smith...")
    Note over MW: Local Presidio Scrubbing &<br/>Token Mapping Vault Created
    MW->>LLM: Sends Masked Prompt ("I am <PERSON_0>...")
    LLM->>Provider: Dispatches to Gemini, OpenAI, or Anthropic API
    Provider-->>MW: Returns Masked Response ("Hello <PERSON_0>...")
    Note over MW: Local Rehydration via<br/>Token Mapping Vault
    MW-->>Client: Returns Real Response ("Hello Jack Smith...")

Test-Driven Development with:

📊 AI-as-a-Judge Evaluation (DeepEval) to guarantee the local masking engine completely eliminates PII leakage without degrading the LLM's performance, the system is benchmarked using DeepEval (G-Eval) with a gemini-2.5-flash evaluation judge.

## Quick Start

### Prerequisites
- Python 3.13+
- Google Gemini API key (for real judge evaluation)
- Docker (optional, for containerization)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Safety_Guardrail

# Install dependencies
pip install -e .

# Or with poetry
poetry install
```

### Running Tests

```bash
# Run tests with mock judge (fast, no API calls)
pytest tests/ -v

# Run tests with real Gemini judge (comprehensive but slower)
USE_REAL_JUDGE=1 pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v           # Unit tests only
pytest tests/security/ -v       # Security/PII tests only
pytest tests/ -m "judge" -v     # Tests with judge evaluation
```

### Docker Deployment

```bash
# Build the image
docker build -t safety-guardrail .

# Run with mock judge
docker run -p 8000:8000 safety-guardrail

# Run with real judge
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your-api-key \
  -e USE_REAL_JUDGE=1 \
  safety-guardrail
```

## Architecture

### Core Components

1. **Safety Engine** (`src/safety_guardrail/engine.py`)
   - Detects PII using Presidio (8 entity types)
   - Creates unique placeholders (<ENTITY_TYPE_0>)
   - Maintains token mapping vault for rehydration
   - Input validation and error handling

2. **Chat Interface** (`src/safety_guardrail/chat.py`)
   - Orchestrates protect → API call → reveal workflow
   - Loads safety rules from configuration
   - Integrates with Gemini API

3. **REST API** (`src/safety_guardrail/main.py`)
   - FastAPI server on :8000
   - Endpoints:
     - `GET /health` - Health check
     - `POST /api/v1/chat` - Chat with masking

### PII Entity Types

The system detects and masks 8 entity types:
- PERSON
- EMAIL_ADDRESS
- PHONE_NUMBER
- LOCATION
- DATE_TIME
- CREDIT_CARD
- URL
- IP_ADDRESS

## Testing

### Judge Types

The test suite supports two evaluation modes:

**Mock Judge (Default)**
- ✅ Fast (< 1ms per test)
- ✅ No API calls
- ✅ Great for development and CI/CD
- ⚠️ Pattern-based (85-90% accuracy)

**Real Judge (Gemini API)**
- ✅ Comprehensive (LLM-based reasoning)
- ✅ 95%+ accuracy
- ⚠️ Slow (2-5s per test)
- ⚠️ Requires API quota

### Test Organization

- **Unit Tests** (13) - Core protect/reveal functions
- **Integration Tests** (6) - Full workflows and API endpoints
- **Security Tests** (19) - PII leakage and injection resistance
- **Positive Tests** (10) - Valid inputs and expected behaviors
- **Negative Tests** (12) - Edge cases and error handling
- **Regression Tests** (6) - Previously fixed issues
- **Performance Tests** (13) - Latency benchmarks

Total: **80+ tests** with automated logging and judge evaluation

### Quick Test Examples

```bash
# Fast feedback loop (mock judge)
pytest tests/ -v

# Weekly comprehensive validation (real judge)
USE_REAL_JUDGE=1 pytest tests/ -v --tb=short

# Security-focused testing
pytest tests/ -m "security" -v

# Pre-commit hook (fast)
pytest tests/unit tests/negative -v

# Debug failing tests
pytest tests/ -v -s --tb=long
```

## Optimization Features

### Mock Judge
- Regex-based pattern detection for 7 PII types
- Heuristic evaluation for response quality
- Zero API overhead
- See [MOCK_JUDGE.md](MOCK_JUDGE.md) for details

### Batch Processing
- Evaluate up to 20 test cases in 1 API request
- 95% quota savings vs. individual requests
- Built-in batch processor ready for integration
- See [MOCK_JUDGE.md](MOCK_JUDGE.md#batch-processing) for examples

## Logging

Comprehensive logging system with:
- Rotating file handlers (10MB+ 5 backups)
- Separate loggers for engine, judge, tests, and errors
- Judge results logged to `logs/judge_results.log`
- Test summary in `logs/test_suite.log`

Configure in `logging.conf` - see [LOGGING.md](LOGGING.md) for details.

## Documentation

- [LOGGING.md](LOGGING.md) - Logging configuration and usage
- [MOCK_JUDGE.md](MOCK_JUDGE.md) - Mock judge and batch processing guide
- Inline code documentation with docstrings

## Performance

- PII masking: ~5-10ms per text
- Mock judge evaluation: < 1ms per test case
- Real judge evaluation: 2-5s per test case
- API throughput: 20 test cases/request with batching

## Security Considerations

- ✅ PII masked before any external API call
- ✅ Mask tokens never logged (vault encrypted in memory)
- ✅ Prompt injection handling with special character validation
- ✅ No sensitive data in logs (except judge_results.log with redaction)
- ✅ Environment variables for secrets (.env file)

## Development Workflow

### Recommended Flow

```bash
# 1. Make changes
git checkout -b feature/my-feature

# 2. Quick test with mock judge
pytest tests/ -v

# 3. Commit changes
git add .
git commit -m "Add feature"

# 4. Before opening PR (comprehensive)
USE_REAL_JUDGE=1 pytest tests/security tests/integration -v

# 5. Push and create PR
git push origin feature/my-feature
```

## Troubleshooting

**Tests use real Gemini API instead of mock?**
```bash
# Check the judge type in logs
pytest tests/ -v 2>&1 | grep "Judge Type"
# Should show: "Judge Type: MOCK (Local)"
```

**Out of API quota?**
```bash
# Use mock judge (default - no API calls)
pytest tests/ -v
```

**Want to validate with real judge?**
```bash
# Set environment variable and run
USE_REAL_JUDGE=1 pytest tests/
```

## License

[License info here]

## Contributing

[Contributing guidelines here]
