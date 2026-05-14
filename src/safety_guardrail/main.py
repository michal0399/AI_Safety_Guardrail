from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

def mask_pii(text: str):
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    
    # 1. Detect
    results = analyzer.analyze(text=text, entities=["PERSON", "EMAIL_ADDRESS"], language='en')
    
    # 2. Mask
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    
    return anonymized_result.text

def detect_pii(text: str):
    # Initialize the engine
    analyzer = AnalyzerEngine()
    
    # Define what we are looking for
    target_entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"]
    
    # Run analysis
    results = analyzer.analyze(text=text, entities=target_entities, language='en')
    
    print(f"--- Analysis for: '{text}' ---")
    if not results:
        print("No PII detected.")
    for res in results:
        print(f"Found: {res.entity_type} | Start: {res.start} | End: {res.end} | Confidence: {res.score:.2f}")

if __name__ == "__main__":
    raw_input = "Tell John Doe to email me at john.doe@gmail.com"
    safe_output = mask_pii(raw_input)
    
    print(f"Raw: {raw_input}")
    print(f"Safe: {safe_output}")