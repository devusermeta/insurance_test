"""
Test LLM-Based Document Extraction
Compare pattern-based vs LLM-based extraction approaches
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_llm_extraction():
    """Test LLM extraction with sample document content"""
    print("🧠 Testing LLM-Based Document Extraction")
    print("=" * 60)
    
    # Sample document content from different sources
    test_documents = [
        {
            "type": "discharge_summary_doc",
            "content": """
            REGIONAL MEDICAL CENTER
            DISCHARGE SUMMARY
            
            Patient: Sarah Johnson
            DOB: 03/15/1985
            MRN: 12345678
            
            Admission Date: August 1, 2025
            Discharge Date: August 5, 2025
            
            Attending Physician: Dr. Michael Chen
            
            FINAL DIAGNOSIS: Acute community-acquired pneumonia
            
            HOSPITAL COURSE:
            The patient was admitted with symptoms of fever, cough, and shortness of breath.
            Chest X-ray confirmed pneumonia. Patient responded well to antibiotic therapy.
            
            DISCHARGE INSTRUCTIONS:
            Continue prescribed antibiotics for 7 days.
            Follow up with primary care physician in 1 week.
            """,
            "kv_pairs": {
                "Patient Name": "Sarah Johnson",
                "Admission": "August 1, 2025",
                "Discharge": "August 5, 2025"
            }
        },
        {
            "type": "medical_bill_doc", 
            "content": """
            MERCY HOSPITAL BILLING DEPARTMENT
            STATEMENT OF CHARGES
            
            Patient: Robert Davis
            Account #: ACC-789456
            Service Date: September 1, 2025
            
            CHARGES:
            Emergency Room Visit.........$450.00
            Laboratory Tests.............$125.00
            Radiology (X-ray)...........$275.00
            Medications..................$78.50
            
            TOTAL AMOUNT DUE: $928.50
            
            Please remit payment within 30 days.
            """,
            "kv_pairs": {
                "Patient": "Robert Davis",
                "Service Date": "09/01/2025",
                "Total": "$928.50"
            }
        },
        {
            "type": "memo_doc",
            "content": """
            PHYSICIAN'S NOTE
            
            Patient: Maria Rodriguez
            Date: September 10, 2025
            
            Chief Complaint: Follow-up for diabetes management
            
            Assessment: Patient's Type 2 diabetes mellitus is well controlled
            with current medication regimen. HbA1c levels have improved significantly.
            
            Plan: Continue current metformin dosage. Schedule next appointment
            in 3 months for routine monitoring.
            
            Dr. Lisa Thompson, MD
            Endocrinology Department
            """,
            "kv_pairs": {
                "Patient Name": "Maria Rodriguez",
                "Condition": "Type 2 diabetes mellitus"
            }
        }
    ]
    
    try:
        from openai import AzureOpenAI
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        print("✅ Azure OpenAI client initialized")
        
        for i, doc in enumerate(test_documents, 1):
            print(f"\n📄 Test Document {i}: {doc['type']}")
            print("-" * 40)
            
            # Create extraction prompt
            prompt = create_extraction_prompt(doc['content'], doc['kv_pairs'], doc['type'])
            
            # Call LLM
            print("🧠 Calling LLM for extraction...")
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini-deployment"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert medical document analyst. Extract specific information from medical documents and return ONLY valid JSON. Be precise and only extract information that is clearly present in the document."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            llm_result = response.choices[0].message.content.strip()
            if llm_result.startswith("```json"):
                llm_result = llm_result.replace("```json", "").replace("```", "").strip()
            
            try:
                extracted = json.loads(llm_result)
                print("✅ LLM Extraction Result:")
                print(json.dumps(extracted, indent=2))
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Raw response: {llm_result}")
                
    except ImportError:
        print("❌ OpenAI package not installed. Install with: pip install openai")
    except Exception as e:
        print(f"❌ Error during LLM testing: {e}")

def create_extraction_prompt(content: str, kv_pairs: dict, doc_type: str) -> str:
    """Create extraction prompt (same logic as in agent)"""
    kv_text = "\n".join([f"- {k}: {v}" for k, v in kv_pairs.items()]) if kv_pairs else "None found"
    
    if doc_type == 'discharge_summary_doc':
        return f"""
Extract the following information from this hospital discharge summary:

DOCUMENT CONTENT:
{content}

KEY-VALUE PAIRS FOUND:
{kv_text}

Extract these fields and return as JSON:
{{
    "patient_name": "Full patient name",
    "hospital_name": "Hospital or medical facility name", 
    "admit_date": "Admission date in YYYY-MM-DD format",
    "discharge_date": "Discharge date in YYYY-MM-DD format",
    "medical_condition": "Primary diagnosis or medical condition"
}}

Rules:
- Only include fields where you can find clear information
- Use YYYY-MM-DD format for dates
- If a field is not found, omit it from the JSON
- Return ONLY the JSON object, no explanations
"""

    elif doc_type == 'medical_bill_doc':
        return f"""
Extract the following information from this medical bill:

DOCUMENT CONTENT:
{content}

KEY-VALUE PAIRS FOUND:
{kv_text}

Extract these fields and return as JSON:
{{
    "patient_name": "Full patient name",
    "bill_date": "Bill or service date in YYYY-MM-DD format", 
    "bill_amount": 123.45
}}

Rules:
- Only include fields where you can find clear information
- Use YYYY-MM-DD format for dates
- Return bill_amount as a number (not string)
- If a field is not found, omit it from the JSON
- Return ONLY the JSON object, no explanations
"""

    elif doc_type == 'memo_doc':
        return f"""
Extract the following information from this medical memo/note:

DOCUMENT CONTENT:
{content}

KEY-VALUE PAIRS FOUND:
{kv_text}

Extract these fields and return as JSON:
{{
    "patient_name": "Full patient name",
    "medical_condition": "Medical condition or diagnosis mentioned"
}}

Rules:
- Only include fields where you can find clear information
- If a field is not found, omit it from the JSON
- Return ONLY the JSON object, no explanations
"""

def compare_approaches():
    """Compare LLM vs Pattern-based approaches"""
    print("\n🔬 LLM vs Pattern-Based Comparison")
    print("=" * 60)
    
    print("📊 FLEXIBILITY:")
    print("  🧠 LLM: Adapts to any document format, understands context")
    print("  📝 Patterns: Rigid, breaks with format changes")
    
    print("\n📊 ACCURACY:")
    print("  🧠 LLM: High semantic understanding, medical knowledge")
    print("  📝 Patterns: Good for exact matches, misses variations")
    
    print("\n📊 MAINTENANCE:")
    print("  🧠 LLM: Self-improving, no manual pattern updates")
    print("  📝 Patterns: Requires manual regex updates for each format")
    
    print("\n📊 COST:")
    print("  🧠 LLM: Small API cost per document (very affordable)")
    print("  📝 Patterns: Free but high development/maintenance cost")
    
    print("\n📊 RELIABILITY:")
    print("  🧠 LLM: Consistent with fallback to patterns")
    print("  📝 Patterns: Reliable for known formats only")

if __name__ == "__main__":
    test_llm_extraction()
    compare_approaches()
    
    print(f"\n🎯 RECOMMENDATION:")
    print("✅ Use LLM-based extraction as primary method")
    print("✅ Keep pattern-based as fallback for reliability") 
    print("✅ Best of both worlds: Intelligence + Reliability")
