from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from safety_guardrail.chat import safe_chat

app = FastAPI(
    title="AI Safety Guardrail Proxy",
    description="An API that sanitizes PII locally before routing prompts to an LLM."
)

class ChatRequest(BaseModel):
    user_prompt: str
    task_instruction: str = "You are a helpful assistant."

# Expanded response schema for transparency
class ChatResponse(BaseModel):
    masked_prompt: str
    ai_raw_response: str
    final_output: str

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker container."""
    return {"status": "healthy", "service": "Safety Guardrail AI Proxy"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def handle_chat(payload: ChatRequest):
    try:
        # This now returns a dictionary matching the ChatResponse schema
        result_data = safe_chat(
            user_prompt=payload.user_prompt,
            task_instruction=payload.task_instruction
        )
        return ChatResponse(**result_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
