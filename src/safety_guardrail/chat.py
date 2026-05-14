import os
import google.generativeai as genai
from dotenv import load_dotenv
from engine import SafetyGuardrail

load_dotenv()

# Setup Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')
guard = SafetyGuardrail()
SYSTEM_INSTRUCTION = """
You are a professional bio writer. 
CRITICAL RULES:
1. ONLY use the specific placeholders provided in the user prompt (e.g., <PERSON_0>, <EMAIL_ADDRESS_1>).
2. For any information NOT provided in the prompt (like Job Title, Skills, or Years of Experience), do NOT create new placeholders. Instead, invent realistic, high-level professional details that fit the context.
"""

def safe_chat(user_prompt: str):
    # 1. Mask PII
    masked_prompt = guard.protect(user_prompt)
    print(f"\n[INTERNAL] Sent to AI: {masked_prompt}")

    # 2. Call Gemini
    # We tell the model to respect the placeholders via SYSTEM_INSTRUCTION
    chat = model.start_chat(history=[])
    response = chat.send_message([
        SYSTEM_INSTRUCTION,
        f"User Prompt: {masked_prompt}"
    ])

    ai_raw_response = response.text
    print(f"[INTERNAL] AI Raw Response: {ai_raw_response}")

    # 3. Reveal PII
    final_output = guard.reveal(ai_raw_response)
    return final_output

if __name__ == "__main__":
    prompt = "My name is John Wick and my email is boogeyman@continental.com. Can you write a professional bio for me?"
    print(f"User Request: {prompt}")
    
    result = safe_chat(prompt)
    print(f"\nFINAL OUTPUT:\n{result}")