"""Prompts for document validation."""

ANOMALY_DETECTION_PROMPT = """Analyze the following extracted invoice data and identify any anomalies or potential issues:

Extracted Data:
{extracted_data}

Check for the following issues:
1. VAT calculation errors (net + VAT should equal gross)
2. Invalid VAT rates (UK standard: 20%, reduced: 5%, zero: 0%)
3. Invalid VAT number format (UK: GB followed by 9 or 12 digits)
4. Unusual amounts (very large or very small)
5. Missing required fields
6. Date inconsistencies (future dates, dates too far in past)
7. Currency mismatches
8. Suspicious patterns

Return a JSON response with the following structure:
{{
    "is_valid": true/false,
    "anomalies": [
        {{
            "field": "field_name",
            "issue": "description of the issue",
            "severity": "high/medium/low",
            "suggestion": "recommended action"
        }}
    ],
    "confidence_score": 0.0-1.0,
    "summary": "Brief summary of findings"
}}"""

CHASER_EMAIL_PROMPT = """Generate a professional, polite email requesting missing VAT evidence documents.

Context:
- Recipient: {recipient_name}
- Missing documents: {missing_items}
- Due date: {due_date}
- Company name: Nova VAT Services

Requirements:
1. Professional but friendly tone
2. Clear list of what's needed
3. Mention the due date
4. Offer to help if they have questions
5. Keep it concise (under 200 words)

Do not include subject line. Start directly with the greeting."""

DUPLICATE_DETECTION_PROMPT = """Compare these two documents and determine if they are duplicates:

Document 1:
{doc1}

Document 2:
{doc2}

Consider:
1. Same invoice number
2. Same amounts
3. Same dates
4. Same parties (supplier/customer)
5. Similar descriptions

Return JSON:
{{
    "is_duplicate": true/false,
    "confidence": 0.0-1.0,
    "matching_fields": ["list", "of", "matching", "fields"],
    "differences": ["list", "of", "differences"],
    "reasoning": "explanation"
}}"""
