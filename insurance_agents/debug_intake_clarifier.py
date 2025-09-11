#!/usr/bin/env python3
"""
Debug script to test Intake Clarifier directly
"""

import asyncio
import requests
import json

async def test_intake_clarifier():
    print("🔍 Testing Intake Clarifier directly...")
    
    url = 'http://localhost:8002'
    request_data = {
        'text': '''Compare claim data with extracted patient data:
Claim ID: OP-03

Fetch documents from:
- claim_details container (claim_id: OP-03)
- extracted_patient_data container (claim_id: OP-03)

Compare: patient_name, bill_amount, bill_date, diagnosis vs medical_condition
If mismatch: Update status to 'marked for rejection' with reason
If match: Update status to 'marked for approval'
'''
    }
    
    try:
        response = requests.post(url, json=request_data, timeout=30)
        print(f'✅ Status Code: {response.status_code}')
        print(f'📄 Response Text: {response.text}')
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f'📋 JSON Response:')
                print(json.dumps(json_response, indent=2))
            except:
                print("Response is not JSON format")
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_intake_clarifier())
