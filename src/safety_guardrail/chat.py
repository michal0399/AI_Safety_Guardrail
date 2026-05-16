import os
import google.generativeai as genai
from dotenv import load_dotenv
from engine import SafetyGuardrail

load_dotenv()

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')
guard = SafetyGuardrail()

def load_system_rules(filepath: str = None) -> str:
    """Loads the static safety rules from an external text file."""
    if filepath is None:
        # Construct path to safety_rules.txt at project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        filepath = os.path.join(project_root, "safety_rules.txt")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"[WARNING] Config file {filepath} not found. Running without base safety rules.")
        return ""

def safe_chat(user_prompt: str, task_instruction: str = "You are a helpful assistant."):
    # 1. Mask PII locally
    masked_prompt = guard.protect(user_prompt)
    print(f"\n[INTERNAL] Sent to AI: {masked_prompt}")

    # 2. Load the system rules from external config
    base_safety_rules = load_system_rules()
    full_system_instruction = f"{task_instruction}\n\n{base_safety_rules}"

    # 3. Call Gemini
    response = model.generate_content([
        full_system_instruction,
        f"User Prompt: {masked_prompt}"
    ])

    ai_raw_response = response.text
    print(f"[INTERNAL] AI Raw Response: {ai_raw_response}")

    # 4. Reveal PII locally
    final_output = guard.reveal(ai_raw_response)
    return final_output

if __name__ == "__main__":
    prompt = "My name is John Wick and my email is boogeyman@continental.com. Can you write a professional bio for me?"
    task = "You are an expert executive resume writer and biographer."
    
    print(safe_chat(prompt, task_instruction=task))