#!/usr/bin/env python3
"""
Test LLM URL extraction directly
"""

import os
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_llm_url_extraction():
    """Test LLM URL extraction with sample text"""
    
    sample_text = """Process documents and create extracted_patient_data for:
Claim ID: OP-04
Category: Outpatient

Extract from documents and create document in extracted_patient_data container:
- Patient name, Bill amount, Bill date, Medical condition
- Document ID should be: OP-04

Document URLs to process:
- Document 1: https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-04/OP-04_Medical_Bill.pdf 
- Document 2: https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-04/OP-04_Memo.pdf"""

    print("🧪 Testing URL Extraction Methods")
    print("=" * 50)
    print(f"📝 Sample text:\n{sample_text}\n")
    
    # Test 1: Fixed regex extraction
    print("🔍 TEST 1: Fixed Regex Extraction")
    url_pattern = r'https?://[^\s]+\.(?:pdf|jpg|jpeg|png|tiff|bmp)'
    urls_regex = re.findall(url_pattern, sample_text, re.IGNORECASE)
    print(f"📎 Regex extracted: {urls_regex}")
    print()
    
    # Test 2: LLM extraction
    print("🧠 TEST 2: LLM Extraction")
    try:
        from openai import AzureOpenAI
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        )
        
        # Create a prompt for URL extraction
        extraction_prompt = f"""
Extract all document URLs from the following text. Look for:
- Full HTTP/HTTPS URLs ending in .pdf, .jpg, .jpeg, .png, .tiff, .bmp
- Blob storage URLs
- Any attachment URLs mentioned

Text to analyze:
{sample_text}

Return ONLY a JSON array of URLs, no other text. Example format:
["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]

If no URLs found, return: []
"""

        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are a precise document URL extractor. Return only valid JSON arrays of URLs."},
                {"role": "user", "content": extraction_prompt}
            ],
            max_tokens=500,
            temperature=0
        )
        
        result_text = response.choices[0].message.content.strip()
        print(f"🧠 LLM raw response: {result_text}")
        
        # Parse the JSON response
        urls_llm = json.loads(result_text)
        print(f"📎 LLM extracted: {urls_llm}")
        
        if isinstance(urls_llm, list):
            # Filter out invalid URLs and ensure they're strings
            valid_urls = []
            for url in urls_llm:
                if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
                    valid_urls.append(url)
            
            print(f"✅ Valid URLs: {valid_urls}")
            return valid_urls
        else:
            print("❌ LLM returned non-list response")
            return []
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse LLM JSON response: {e}")
        return []
    except Exception as e:
        print(f"❌ LLM URL extraction error: {e}")
        return []

if __name__ == "__main__":
    test_llm_url_extraction()
