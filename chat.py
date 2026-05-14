import os
import google.generativeai as genai
from dotenv import load_dotenv
from engine import SafetyGuardrail

load_dotenv()

# Setup Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')
guard = SafetyGuardrail()

def safe_chat(user_prompt: str):
    # 1. Mask PII
    masked_prompt = guard.protect(user_prompt)
    print(f"\n[INTERNAL] Sent to AI: {masked_prompt}")

    # 2. Call Gemini
    # We tell the model to respect the placeholders
    chat = model.start_chat(history=[])
    response = chat.send_message(
        f"You are a helpful assistant. Use the placeholders like <PERSON_0> exactly as they appear. \n\nPrompt: {masked_prompt}"
    )

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