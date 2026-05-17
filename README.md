Most companies are afraid of LLMs because of data leaks. This repo provides the solution: a local safety guardrail that swaps Personally Identifiable Information for unique placeholders before they leave your machine, then intelligently reconstructs the response for the user. Verified for accuracy with AI-as-a-Judge.

The Core Problem with LLM Gateways: Tools like LiteLLM consolidate all API keys and handle raw, unmasked data. If the proxy layer is compromised via a supply chain attack, your entire infrastructure and data ecosystem are instantly exposed.

Solution: This project introduces a Zero-Trust Local Boundary. Because PII masking and token vaulting happen locally before any third-party routing engine touches the string, even a completely backdoored proxy cannot leak real user data.

How this works:

[Client Application] 
       │
       ▼ (1. Sends Raw Prompt: "I am Jack Smith...")
[FastAPI Middleware] ─── (2. Local Presidio Scrubbing & Token Mapping Vault)
       │
       ▼ (3. Sends Masked Prompt: "I am <PERSON_0>...")
[LiteLLM Routing Layer]
       │
       ▼ (4. Dispatches to Gemini, OpenAI, or Anthropic API)
   [LLM Provider]
       │
       ▼ (5. Returns Masked Response: "Hello <PERSON_0>...")
[FastAPI Middleware] ─── (6. Local Rehydration via Token Mapping Vault)
       │
       ▼ (7. Returns Real Response: "Hello Jack Smith...")
[Client Application]

Test-Driven Development with:

📊 AI-as-a-Judge Evaluation (DeepEval) to guarantee the local masking engine completely eliminates PII leakage without degrading the LLM's performance, the system is benchmarked using DeepEval (G-Eval) with a gemini-2.5-flash evaluation judge.