from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class SafetyGuardrail:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.mapping_vault = {}

    def protect(self, text: str):
        # Input validation and sanitization
        if text is None:
            raise TypeError("Input text cannot be None. Expected a string.")

        if not isinstance(text, str):
            raise TypeError(f"Input text must be a string, got {type(text).__name__}")

        # Sanitize: strip leading/trailing whitespace
        text = text.strip()

        # Handle empty strings
        if not text:
            return text

        # 1. Analyze - detect comprehensive PII types
        entities = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "LOCATION",
            "DATE_TIME",
            "CREDIT_CARD",
            "URL",
            "IP_ADDRESS",
        ]
        results = self.analyzer.analyze(text=text, entities=entities, language="en")

        # 2. Define custom masking to create unique IDs
        operators = {
            "PERSON": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 0, "from_end": False}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        }

        # For a professional portfolio, we'll manually map them to keep it simple but effective
        anonymized_text = text
        for i, res in enumerate(results):
            original_val = text[res.start : res.end]
            placeholder = f"<{res.entity_type}_{i}>"

            # Store in our vault
            self.mapping_vault[placeholder] = original_val
            # Swap in text
            anonymized_text = anonymized_text.replace(original_val, placeholder)

        return anonymized_text

    def reveal(self, AI_response: str):
        # Input validation
        if AI_response is None:
            raise TypeError("AI response cannot be None. Expected a string.")

        if not isinstance(AI_response, str):
            raise TypeError(f"AI response must be a string, got {type(AI_response).__name__}")

        # Swap placeholders back to real data
        revealed_text = AI_response
        for placeholder, original_val in self.mapping_vault.items():
            revealed_text = revealed_text.replace(placeholder, original_val)
        return revealed_text


# --- Test the Loop ---
if __name__ == "__main__":
    guard = SafetyGuardrail()

    user_input = "Tell John Doe to contact me at john.doe@gmail.com"
    protected_input = guard.protect(user_input)

    print(f"To AI: {protected_input}")

    # Simulating an AI response that mentions the placeholder
    ai_reply = f"I have processed the request for {list(guard.mapping_vault.keys())[0]}."
    print(f"AI Response (Raw): {ai_reply}")

    final_output = guard.reveal(ai_reply)
    print(f"User sees: {final_output}")
