# Presidio Configuration Guide

## Current Limitations

The current setup uses:
- English language only (`language='en'`)
- Default built-in recognizers
- Limited format support for phone numbers

## How to Enhance Presidio

### 1. Multi-Language Support

Presidio uses spaCy models. You can add support for multiple languages:

```bash
# Install language models
python -m spacy download es_core_news_sm  # Spanish
python -m spacy download fr_core_news_sm  # French
python -m spacy download de_core_news_sm  # German
python -m spacy download pt_core_news_sm  # Portuguese
```

Then use in code:
```python
from presidio_analyzer import AnalyzerEngine

# English
analyzer_en = AnalyzerEngine()
results_en = analyzer_en.analyze(text="My name is John", language="en")

# Spanish
analyzer_es = AnalyzerEngine()
results_es = analyzer_es.analyze(text="Mi nombre es Juan", language="es")

# Auto-detect (processes all available models)
analyzer_multi = AnalyzerEngine()
results = analyzer_multi.analyze(text="John and Juan", language="en")  # May catch both
```

### 2. Add Custom Regex Recognizers

Presidio allows custom patterns for phone numbers, national IDs, etc.

```python
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry
import re

# Create custom recognizer for US phone patterns
phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=[
        re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # 123-456-7890 or 123.456.7890
        re.compile(r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'),  # (123) 456-7890
        re.compile(r'\+1\s*\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # +1 123-456-7890
        re.compile(r'\+\d{1,3}\s*\d{1,14}\b'),  # International format
    ]
)

# Create registry and add recognizer
registry = RecognizerRegistry()
registry.add_recognizer(phone_recognizer)

# Use with analyzer
analyzer = AnalyzerEngine(registry=registry)
results = analyzer.analyze(text="Call me at (555) 123-4567", entities=["PHONE_NUMBER"], language="en")
```

### 3. International Phone Formats

Add patterns for different countries:

```python
import re
from presidio_analyzer import PatternRecognizer, RecognizerRegistry

def create_international_phone_recognizer():
    """Recognizer for international phone formats."""
    patterns = [
        # US: +1 (555) 123-4567, +1-555-123-4567, 555-123-4567
        re.compile(r'\+?1[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b'),

        # UK: +44 20 XXXX XXXX, 020 XXXX XXXX
        re.compile(r'\+?44[\s.-]?20[\s.-]?\d{4}[\s.-]?\d{4}\b'),

        # Germany: +49 30 XXXX XXXX, 030 XXXX XXXX
        re.compile(r'\+?49[\s.-]?\d{2,5}[\s.-]?\d{3,9}\b'),

        # France: +33 1 XXXX XXXX, 01 XXXX XXXX
        re.compile(r'\+?33[\s.-]?[1-9][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b'),

        # Spain: +34 9XX XXXXX, +34 X XXXX XXXX
        re.compile(r'\+?34[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{3}\b'),

        # China: +86 10 XXXX XXXX, 010 XXXX XXXX
        re.compile(r'\+?86[\s.-]?10[\s.-]?\d{4}[\s.-]?\d{4}\b'),

        # Japan: +81 3 XXXX XXXX, 03 XXXX XXXX
        re.compile(r'\+?81[\s.-]?3[\s.-]?\d{4}[\s.-]?\d{4}\b'),

        # Australia: +61 2 XXXX XXXX, 02 XXXX XXXX
        re.compile(r'\+?61[\s.-]?2[\s.-]?\d{4}[\s.-]?\d{4}\b'),

        # Generic international: +XXX XXX XXX XXX
        re.compile(r'\+\d{1,3}[\s.-]?\d{1,5}[\s.-]?\d{1,5}[\s.-]?\d{1,9}\b'),
    ]

    return PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=patterns,
        name="international_phone"
    )

# Usage
registry = RecognizerRegistry()
registry.add_recognizer(create_international_phone_recognizer())
analyzer = AnalyzerEngine(registry=registry)
```

### 4. Add Custom ID Formats

```python
def create_id_recognizers():
    """Add recognizers for various national ID formats."""
    recognizers = []

    # US Social Security Number: 123-45-6789
    ssn = PatternRecognizer(
        supported_entity="SSN",
        patterns=[
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        ]
    )
    recognizers.append(ssn)

    # Credit card patterns (already in Presidio, but can be enhanced)
    cc = PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[
            re.compile(r'\b(?:\d{4}[\s.-]?){3}\d{4}\b'),  # 1234 5678 9012 3456
            re.compile(r'\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b'),  # Various spacing
        ]
    )
    recognizers.append(cc)

    # EU IBAN: GB82WEST12345698765432
    iban = PatternRecognizer(
        supported_entity="IBAN",
        patterns=[
            re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b'),
        ]
    )
    recognizers.append(iban)

    # US Tax ID: 12-3456789
    tax_id = PatternRecognizer(
        supported_entity="TAX_ID",
        patterns=[
            re.compile(r'\b\d{2}-\d{7}\b'),
        ]
    )
    recognizers.append(tax_id)

    return recognizers

registry = RecognizerRegistry()
for recognizer in create_id_recognizers():
    registry.add_recognizer(recognizer)
```

### 5. Enhanced Engine Configuration

Create an enhanced version of the engine with multi-language and custom formats:

```python
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry
import re

class EnhancedSafetyGuardrail:
    def __init__(self, languages=None, enable_custom_formats=True):
        """
        Initialize with multi-language and custom format support.

        Args:
            languages: List of language codes ['en', 'es', 'fr', 'de']. Default: ['en']
            enable_custom_formats: If True, add regex-based recognizers
        """
        self.languages = languages or ['en']
        self.registry = RecognizerRegistry()

        if enable_custom_formats:
            self._register_custom_formats()

        self.analyzer = AnalyzerEngine(registry=self.registry)
        self.anonymizer = AnonymizerEngine()
        self.mapping_vault = {}

    def _register_custom_formats(self):
        """Register custom regex-based recognizers."""

        # International phone
        phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[
                # US/Canada
                re.compile(r'\+?1[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b'),
                # International +XX format
                re.compile(r'\+\d{1,3}[\s.-]?\d{1,5}[\s.-]?\d{1,5}[\s.-]?\d{1,9}\b'),
                # EU local formats
                re.compile(r'\b0\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{4,5}\b'),
            ]
        )
        self.registry.add_recognizer(phone_recognizer)

        # Social Security Numbers
        ssn_recognizer = PatternRecognizer(
            supported_entity="SSN",
            patterns=[
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # US
                re.compile(r'\b\d{9}\b'),  # No dashes
            ]
        )
        self.registry.add_recognizer(ssn_recognizer)

        # IBAN
        iban_recognizer = PatternRecognizer(
            supported_entity="IBAN",
            patterns=[
                re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b'),
            ]
        )
        self.registry.add_recognizer(iban_recognizer)

        # Passport
        passport_recognizer = PatternRecognizer(
            supported_entity="PASSPORT",
            patterns=[
                re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'),
            ]
        )
        self.registry.add_recognizer(passport_recognizer)

    def protect(self, text, language=None):
        """Protect text with optional language specification."""
        if text is None:
            raise TypeError("Input text cannot be None")

        if not isinstance(text, str):
            raise TypeError(f"Expected string, got {type(text).__name__}")

        text = text.strip()
        if not text:
            return text

        lang = language or self.languages[0]

        # Detect all entity types (including custom)
        entities = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
            "DATE_TIME", "CREDIT_CARD", "URL", "IP_ADDRESS",
            "SSN", "IBAN", "PASSPORT"
        ]

        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language=lang
        )

        anonymized_text = text
        for i, res in enumerate(results):
            original_val = text[res.start:res.end]
            placeholder = f"<{res.entity_type}_{i}>"
            self.mapping_vault[placeholder] = original_val
            anonymized_text = anonymized_text.replace(original_val, placeholder)

        return anonymized_text

    def reveal(self, ai_response):
        """Reveal original PII from placeholders."""
        if ai_response is None:
            raise TypeError("AI response cannot be None")

        if not isinstance(ai_response, str):
            raise TypeError(f"Expected string, got {type(ai_response).__name__}")

        revealed_text = ai_response
        for placeholder, original_val in self.mapping_vault.items():
            revealed_text = revealed_text.replace(placeholder, original_val)
        return revealed_text

# Usage Examples:
if __name__ == "__main__":
    # US Only
    guard_us = EnhancedSafetyGuardrail(languages=['en'])

    # Multi-language
    guard_multi = EnhancedSafetyGuardrail(languages=['en', 'es', 'fr'])

    # Examples
    examples = [
        "Call me at +1 (555) 123-4567 or +33 1 42 68 53 00",
        "My SSN is 123-45-6789",
        "IBAN: GB82 WEST 1234 5698 7654 32",
        "Passport: US123456789",
    ]

    for text in examples:
        protected = guard_us.protect(text)
        print(f"Original: {text}")
        print(f"Protected: {protected}\n")
```

## Installation Requirements

```bash
# Basic Presidio
pip install presidio-analyzer presidio-anonymizer

# Multi-language support (optional)
pip install spacy
python -m spacy download en_core_news_sm
python -m spacy download es_core_news_sm
python -m spacy download fr_core_news_sm
python -m spacy download de_core_news_sm

# Performance (optional)
pip install gpu-cython  # For faster processing
```

## Performance Tips

1. **Cache the analyzer**: Create it once, reuse it
2. **Batch processing**: Analyze multiple texts in one call
3. **Disable unused languages**: Only load languages you need
4. **Use threshold tuning**: Adjust confidence levels for faster detection

```python
# Confidence threshold (default 0.5)
results = analyzer.analyze(
    text=text,
    entities=entities,
    language='en',
    threshold=0.6  # Higher = fewer false positives, more false negatives
)
```

## Testing Different Configurations

```bash
# Test current vs enhanced
pytest tests/ -v

# Benchmark performance
pytest tests/performance/ -v

# Test multi-language
USE_LANGUAGE=es pytest tests/
```

## Summary

| Feature | Current | Enhanced |
|---------|---------|----------|
| Languages | English only | Multi-language |
| Phone formats | Limited | 20+ international formats |
| Custom IDs | No | SSN, IBAN, Passport, Tax ID |
| Regex support | No | Full pattern customization |
| Performance | Good | Same (cached) |
