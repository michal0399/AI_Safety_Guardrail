"""Enhanced Safety Guardrail with multi-language and custom format support."""

import re
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class EnhancedSafetyGuardrail:
    """
    Enhanced PII detection with:
    - Multi-language support (en, es, fr, de, pt, etc.)
    - International phone formats (US, UK, Germany, France, Spain, China, Japan, etc.)
    - Custom ID formats (SSN, IBAN, Passport, Tax ID)
    - Regex-based pattern matching for structured data
    """

    def __init__(self, languages=None, enable_custom_formats=True):
        """
        Initialize with multi-language and custom format support.

        Args:
            languages: List of language codes ['en', 'es', 'fr', 'de', 'pt']. Default: ['en']
            enable_custom_formats: If True, add regex-based recognizers for phones, IDs, etc.
        """
        self.languages = languages or ['en']
        # Use default AnalyzerEngine which includes spaCy NLP for PERSON detection
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.mapping_vault = {}

        if enable_custom_formats:
            self._register_custom_formats()
        self.anonymizer = AnonymizerEngine()
        self.mapping_vault = {}

    def _register_custom_formats(self):
        """Register custom regex-based recognizers for international formats."""

        # Access the analyzer's registry to add custom recognizers
        registry = self.analyzer.registry

        # ========== INTERNATIONAL PHONE FORMATS ==========
        phone_patterns = [
            # ===== LOCAL/PLAIN FORMATS =====
            # Plain US/local: 555-123-4567, (555) 123-4567, 555.123.4567
            r'\b\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b',

            # US/Canada: +1 (555) 123-4567, +1-555-123-4567, (555) 123-4567, 555-123-4567
            r'\+?1[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b',

            # UK: +44 20 XXXX XXXX, 020 XXXX XXXX, +44(0)20 XXXX XXXX
            r'\+?44[\s.-]?0?20[\s.-]?\d{4}[\s.-]?\d{4}\b',
            r'\+?44[\s.-]?0?20[\s.-]?\d{3,4}[\s.-]?\d{4,5}\b',

            # Germany: +49 30 XXXX XXXX, 030 XXXX XXXX, +49 (0)30 XXXX XXXX
            r'\+?49[\s.-]?0?30[\s.-]?\d{3,4}[\s.-]?\d{4,5}\b',
            r'\+?49[\s.-]?0?\d{2,5}[\s.-]?\d{3,9}\b',

            # France: +33 1 XXXX XXXX, 01 XXXX XXXX, +33 (0)1 XXXX XXXX
            r'\+?33[\s.-]?0?[1-9][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b',

            # Spain: +34 9XX XXXXX or +34 X XXXX XXXX
            r'\+?34[\s.-]?[689]\d{2}[\s.-]?\d{2}[\s.-]?\d{3}\b',
            r'\+?34[\s.-]?[1-9][\s.-]?\d{4}[\s.-]?\d{4}\b',

            # Italy: +39 06 XXXX XXXX, 06 XXXX XXXX
            r'\+?39[\s.-]?06[\s.-]?\d{4}[\s.-]?\d{4}\b',
            r'\+?39[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b',

            # Netherlands: +31 6 XXXX XXXX, 06 XXXX XXXX
            r'\+?31[\s.-]?6[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2,3}\b',
            r'\+?31[\s.-]?0?[1-9][\s.-]?\d{2,3}[\s.-]?\d{4,6}\b',

            # Belgium: +32 2 XXXX XXXX, 02 XXXX XXXX
            r'\+?32[\s.-]?0?2[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b',

            # China: +86 10 XXXX XXXX, 010 XXXX XXXX
            r'\+?86[\s.-]?10[\s.-]?\d{4}[\s.-]?\d{4}\b',
            r'\+?86[\s.-]?0?[1-9]\d{1,2}[\s.-]?\d{4}[\s.-]?\d{4}\b',

            # Japan: +81 3 XXXX XXXX, 03 XXXX XXXX, +81 (0)3 XXXX XXXX
            r'\+?81[\s.-]?0?3[\s.-]?\d{4}[\s.-]?\d{4}\b',
            r'\+?81[\s.-]?0?\d{1,4}[\s.-]?\d{2,4}[\s.-]?\d{4}\b',

            # Australia: +61 2 XXXX XXXX, 02 XXXX XXXX
            r'\+?61[\s.-]?0?2[\s.-]?\d{4}[\s.-]?\d{4}\b',
            r'\+?61[\s.-]?0?[1-9][\s.-]?\d{3,4}[\s.-]?\d{3,4}\b',

            # Brazil: +55 11 XXXX XXXX, (11) XXXX XXXX
            r'\+?55[\s.-]?\(?0?1\d\)?[\s.-]?\d{4}[\s.-]?\d{4}\b',

            # India: +91 XX XXXX XXXX, +91 XXXXXXXXXX
            r'\+?91[\s.-]?\d{10}\b',
            r'\+?91[\s.-]?\d{2}[\s.-]?\d{4}[\s.-]?\d{4}\b',

            # Mexico: +52 XX XXXX XXXX
            r'\+?52[\s.-]?\d{2,3}[\s.-]?\d{4}[\s.-]?\d{4}\b',

            # Generic international: +XXX XXX XXX XXX (catch-all)
            r'\+\d{1,3}[\s.-]?\d{1,5}[\s.-]?\d{1,5}[\s.-]?\d{1,9}\b',
        ]

        phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[Pattern(name="phone", regex=pattern, score=0.8) for pattern in phone_patterns],
            name="international_phone"
        )
        registry.add_recognizer(phone_recognizer)

        # ========== IDENTIFICATION NUMBERS ==========

        # US Social Security Number: 123-45-6789 or 123456789
        ssn_recognizer = PatternRecognizer(
            supported_entity="SSN",
            patterns=[
                Pattern(name="ssn_dashes", regex=r'\b\d{3}-\d{2}-\d{4}\b', score=0.9),
                Pattern(name="ssn_spaces", regex=r'\b\d{3}\s\d{2}\s\d{4}\b', score=0.9),
                Pattern(name="ssn_valid", regex=r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0{4})\d{4}\b', score=0.95),
            ]
        )
        registry.add_recognizer(ssn_recognizer)

        # EU IBAN: GB82WEST12345698765432
        iban_recognizer = PatternRecognizer(
            supported_entity="IBAN",
            patterns=[
                Pattern(name="iban_spaced", regex=r'\b[A-Z]{2}\d{2}[\s.-]?[A-Z0-9]{4}[\s.-]?[A-Z0-9]{4}[\s.-]?[A-Z0-9]{4}[\s.-]?[A-Z0-9]{2,3}\b', score=0.9),
                Pattern(name="iban_unspaced", regex=r'\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b', score=0.8),
            ]
        )
        registry.add_recognizer(iban_recognizer)

        # Passport: US123456789, AB123456789
        passport_recognizer = PatternRecognizer(
            supported_entity="PASSPORT",
            patterns=[
                Pattern(name="passport_long", regex=r'\b[A-Z]{1,2}\d{6,9}\b', score=0.8),
                Pattern(name="passport_short", regex=r'\b[A-Z]{1,3}\d{5,8}\b', score=0.7),
            ]
        )
        registry.add_recognizer(passport_recognizer)

        # US Tax ID (EIN): 12-3456789
        tax_id_recognizer = PatternRecognizer(
            supported_entity="TAX_ID",
            patterns=[
                Pattern(name="tax_id_dashes", regex=r'\b\d{2}-\d{7}\b', score=0.9),
                Pattern(name="tax_id_nodashes", regex=r'\b\d{9}\b', score=0.6),
            ]
        )
        registry.add_recognizer(tax_id_recognizer)

        # Driver's License: ABC123456 (varies by state)
        drivers_license_recognizer = PatternRecognizer(
            supported_entity="DRIVERS_LICENSE",
            patterns=[
                Pattern(name="dl_alpha_num", regex=r'\b[A-Z]{1,3}\d{5,8}\b', score=0.7),
                Pattern(name="dl_num", regex=r'\b\d{5,8}[A-Z]?\b', score=0.6),
            ]
        )
        registry.add_recognizer(drivers_license_recognizer)

        # UK National Insurance Number: AB 12 34 56 C
        ni_recognizer = PatternRecognizer(
            supported_entity="NI_NUMBER",
            patterns=[
                Pattern(name="ni_number", regex=r'\b[A-Z]{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?[A-Z]{1}\b', score=0.9),
            ]
        )
        registry.add_recognizer(ni_recognizer)

        # ========== ENHANCED CREDIT CARDS ==========
        cc_recognizer = PatternRecognizer(
            supported_entity="CREDIT_CARD",
            patterns=[
                Pattern(name="cc_spaced", regex=r'\b(?:\d{4}[\s.-]?){3}\d{4}\b', score=0.9),
                Pattern(name="cc_unspaced", regex=r'\b\d{13,19}\b', score=0.7),
            ]
        )
        registry.add_recognizer(cc_recognizer)

        # ========== ADDRESSES (Street numbers + street names) ==========
        address_recognizer = PatternRecognizer(
            supported_entity="LOCATION",
            patterns=[
                # Street address: 123 Main Street, 456 Oak Avenue, etc.
                Pattern(name="street_address", regex=r'\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way|Parkway|Pkwy)\b', score=0.85),
                # Simpler: Number + Street name
                Pattern(name="simple_address", regex=r'\b\d{1,5}\s+[A-Z][a-z\s]+\s+(St|Ave|Rd|Blvd|Dr|Ln|Ct|Way)\b', score=0.75),
            ]
        )
        registry.add_recognizer(address_recognizer)

        # ========== DATES (More comprehensive date formats) ==========
        date_recognizer = PatternRecognizer(
            supported_entity="DATE_TIME",
            patterns=[
                # Full date with month name: January 15, 1990 or 15 January 1990
                Pattern(name="date_month_name", regex=r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', score=0.9),
                Pattern(name="date_month_name_alt", regex=r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', score=0.9),
                # Short month names
                Pattern(name="date_month_short", regex=r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b', score=0.85),
                # Numeric dates: 01/15/1990, 15-01-1990, 2023-05-20
                Pattern(name="date_numeric_slash", regex=r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', score=0.75),
                Pattern(name="date_numeric_dash", regex=r'\b\d{1,2}-\d{1,2}-\d{2,4}\b', score=0.75),
                Pattern(name="date_iso", regex=r'\b\d{4}-\d{1,2}-\d{1,2}\b', score=0.80),
            ]
        )
        registry.add_recognizer(date_recognizer)

    def protect(self, text, language=None):
        """
        Protect text by detecting and masking PII.

        Args:
            text: Input text to protect
            language: Language code ('en', 'es', 'fr', etc.). Uses first configured language if not specified.

        Returns:
            Masked text with PII replaced by placeholders
        """
        # Input validation
        if text is None:
            raise TypeError("Input text cannot be None. Expected a string.")

        if not isinstance(text, str):
            raise TypeError(f"Input text must be a string, got {type(text).__name__}")

        # Sanitize
        text = text.strip()
        if not text:
            return text

        # Use specified language or first configured language
        lang = language or self.languages[0]

        # Detect all entity types
        entities = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
            "DATE_TIME", "CREDIT_CARD", "URL", "IP_ADDRESS",
            "SSN", "IBAN", "PASSPORT", "TAX_ID", "DRIVERS_LICENSE", "NI_NUMBER"
        ]

        # Analyze
        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language=lang
        )

        # Mask PII
        anonymized_text = text
        for i, res in enumerate(results):
            original_val = text[res.start:res.end]
            placeholder = f"<{res.entity_type}_{i}>"

            # Store in vault
            self.mapping_vault[placeholder] = original_val
            # Replace in text
            anonymized_text = anonymized_text.replace(original_val, placeholder, 1)

        return anonymized_text

    def reveal(self, ai_response):
        """
        Reveal original PII from placeholders.

        Args:
            ai_response: AI response with placeholders

        Returns:
            Text with PII restored
        """
        # Input validation
        if ai_response is None:
            raise TypeError("AI response cannot be None. Expected a string.")

        if not isinstance(ai_response, str):
            raise TypeError(f"AI response must be a string, got {type(ai_response).__name__}")

        # Swap placeholders back
        revealed_text = ai_response
        for placeholder, original_val in self.mapping_vault.items():
            revealed_text = revealed_text.replace(placeholder, original_val)

        return revealed_text

    def clear_vault(self):
        """Clear the PII mapping vault."""
        self.mapping_vault.clear()


# Backward compatibility - use enhanced version by default
SafetyGuardrail = EnhancedSafetyGuardrail


if __name__ == "__main__":
    # Example: Multi-language with custom formats
    guard = EnhancedSafetyGuardrail(languages=['en', 'es', 'fr'], enable_custom_formats=True)

    # Test examples
    examples = [
        # Phone numbers
        "Call me at +1 (555) 123-4567",
        "Or reach me at 020 7946 0958 (UK)",
        "German: +49 30 12345678",

        # ID numbers
        "My SSN is 123-45-6789",
        "Passport: US123456789",
        "IBAN: GB82 WEST 1234 5698 7654 32",
        "Tax ID: 12-3456789",

        # Combined
        "Contact John at john@example.com, +1-555-123-4567 or john.doe@company.com",
    ]

    for example in examples:
        print(f"\n📝 Original: {example}")
        protected = guard.protect(example)
        print(f"🔐 Protected: {protected}")
        guard.clear_vault()  # Clear for next example
