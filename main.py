from presidio_analyzer import AnalyzerEngine

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
    # Test cases
    detect_pii("My name is Sarah Connor and you can reach me at sarah@sky.net")
    detect_pii("The server is located in London near the main hub.")