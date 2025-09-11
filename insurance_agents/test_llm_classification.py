"""
Test LLM-based Classification for Coverage Rules Engine
Tests the new LLM classification vs the old keyword classification
"""

import asyncio
import json
from datetime import datetime

async def test_llm_classification():
    """Test LLM-based classification vs keyword classification"""
    print("🤖 Testing LLM-based Classification for Coverage Rules Engine")
    print("=" * 70)
    
    # Import the updated coverage rules engine
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'coverage_rules_engine'))
    
    from agents.coverage_rules_engine.coverage_rules_executor_fixed import CoverageRulesExecutorFixed
    
    # Initialize the engine
    engine = CoverageRulesExecutorFixed()
    print("✅ Coverage Rules Engine with LLM classification initialized")
    
    # Test cases with various medical diagnoses
    test_diagnoses = [
        # Eye conditions (should classify as "eye")
        "Cataract surgery",
        "Glaucoma treatment", 
        "Diabetic retinopathy",
        "Macular degeneration",
        "LASIK surgery",
        "Retinal detachment repair",
        
        # Dental conditions (should classify as "dental")
        "Root canal treatment",
        "Dental implants",
        "Tooth extraction",
        "Periodontal disease",
        "Orthodontic treatment",
        "Wisdom tooth removal",
        
        # General conditions (should classify as "general")
        "Pneumonia treatment",
        "Heart surgery",
        "Broken leg",
        "Diabetes management",
        "Cancer treatment",
        "Physical therapy",
        
        # Edge cases (test LLM intelligence)
        "Orbital fracture repair",  # Eye-related but complex
        "Temporomandibular joint disorder",  # Could be dental or general
        "Facial reconstruction surgery",  # Complex case
        "Corneal transplant",  # Clearly eye-related
        "Maxillofacial surgery",  # Dental/facial surgery
        "Migraine with visual disturbances"  # Neurological but mentions vision
    ]
    
    print(f"\n🧪 Testing {len(test_diagnoses)} diagnoses with LLM classification:")
    print("-" * 70)
    
    results = []
    
    for i, diagnosis in enumerate(test_diagnoses, 1):
        print(f"\n📋 Test {i}: '{diagnosis}'")
        
        try:
            # Test LLM classification
            llm_result = engine._classify_claim_type(diagnosis)
            
            # Test keyword fallback classification for comparison
            keyword_result = engine._classify_claim_type_keywords(diagnosis)
            
            # Compare results
            agreement = "✅ MATCH" if llm_result == keyword_result else "🔄 DIFFERENT"
            
            print(f"   LLM Result: {llm_result.upper()}")
            print(f"   Keyword Result: {keyword_result.upper()}")
            print(f"   Agreement: {agreement}")
            
            results.append({
                "diagnosis": diagnosis,
                "llm_classification": llm_result,
                "keyword_classification": keyword_result,
                "agreement": llm_result == keyword_result
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                "diagnosis": diagnosis,
                "error": str(e)
            })
    
    # Summary
    print(f"\n📊 CLASSIFICATION COMPARISON SUMMARY:")
    print("=" * 70)
    
    successful_tests = [r for r in results if "error" not in r]
    total_tests = len(successful_tests)
    agreements = sum(1 for r in successful_tests if r.get('agreement', False))
    
    if total_tests > 0:
        print(f"Total Classifications: {total_tests}")
        print(f"LLM-Keyword Agreement: {agreements}/{total_tests} ({(agreements/total_tests)*100:.1f}%)")
        
        # Show differences for analysis
        differences = [r for r in successful_tests if not r.get('agreement', False)]
        if differences:
            print(f"\n🔄 Cases where LLM and Keywords differed:")
            print("-" * 50)
            for diff in differences:
                print(f"   '{diff['diagnosis']}'")
                print(f"   → LLM: {diff['llm_classification'].upper()}")
                print(f"   → Keywords: {diff['keyword_classification'].upper()}")
                print()
        else:
            print("🎉 Perfect agreement between LLM and keyword classification!")
    
    # Test with a complete claim evaluation
    print(f"\n🧪 TESTING COMPLETE CLAIM EVALUATION WITH LLM:")
    print("-" * 70)
    
    test_claims = [
        {
            "claim_id": "LLM-001",
            "category": "outpatient",
            "diagnosis": "Corneal transplant surgery",  # Complex eye procedure
            "bill_amount": "1500"
        },
        {
            "claim_id": "LLM-002", 
            "category": "outpatient",
            "diagnosis": "Maxillofacial reconstructive surgery",  # Complex dental/facial
            "bill_amount": "800"
        }
    ]
    
    for claim in test_claims:
        print(f"\n📋 Evaluating: {claim['diagnosis']}")
        evaluation = await engine._evaluate_structured_claim(claim)
        print(f"   Classification: {evaluation.get('claim_type', 'unknown').upper()}")
        print(f"   Eligible: {'✅ YES' if evaluation['eligible'] else '❌ NO'}")
        print(f"   Max Allowed: ${evaluation.get('max_allowed', 0)}")
        print(f"   Bill Amount: ${evaluation.get('bill_amount', 0)}")

if __name__ == "__main__":
    asyncio.run(test_llm_classification())
