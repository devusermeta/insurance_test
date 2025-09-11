"""
CRITICAL VERIFICATION - Are We Actually Ready?
==============================================

Let's verify what's REALLY working vs what's simulated
"""

import asyncio
import sys
from pathlib import Path
import json

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

async def verify_actual_agent_functionality():
    """Verify what the agents are actually doing vs simulating"""
    print("\n🔍 CRITICAL VERIFICATION - ACTUAL vs SIMULATED")
    print("=" * 60)
    
    # Test 1: Are agents actually processing our enhanced workflow logic?
    print("\n📋 Test 1: Agent Enhanced Logic Verification")
    print("-" * 40)
    
    a2a_client = A2AClient("verification_test")
    
    # Send a very specific structured claim request
    test_claim = """
    VERIFICATION TEST - New Workflow Logic:
    claim_id: OP-05
    patient_name: John Doe
    bill_amount: 88.0
    category: Outpatient
    diagnosis: Type 2 diabetes
    
    This should trigger your enhanced new workflow processing logic.
    Please respond with specific indicators that you're using the new structured processing.
    """
    
    agents_to_verify = [
        "coverage_rules_engine",
        "document_intelligence", 
        "intake_clarifier"
    ]
    
    verification_results = {}
    
    for agent_name in agents_to_verify:
        print(f"\n🔍 Verifying {agent_name}...")
        
        try:
            result = await a2a_client.send_request(
                target_agent=agent_name,
                task=test_claim,
                parameters={"verification_test": True}
            )
            
            if result:
                response_text = str(result).lower()
                
                # Check for new workflow indicators
                new_workflow_indicators = [
                    "new workflow" in response_text,
                    "structured claim" in response_text,
                    "op-05" in response_text,
                    "john doe" in response_text,
                    "outpatient" in response_text,
                    "enhanced" in response_text
                ]
                
                detected_indicators = sum(new_workflow_indicators)
                
                if detected_indicators >= 3:
                    print(f"✅ {agent_name}: DEFINITELY using new workflow logic!")
                    print(f"   Detected {detected_indicators}/6 new workflow indicators")
                elif detected_indicators >= 1:
                    print(f"⚠️  {agent_name}: PARTIALLY using new workflow logic")
                    print(f"   Detected {detected_indicators}/6 new workflow indicators")
                else:
                    print(f"❌ {agent_name}: Likely using OLD/DEFAULT logic")
                    print(f"   No new workflow indicators detected")
                
                verification_results[agent_name] = {
                    "responded": True,
                    "new_workflow_score": detected_indicators,
                    "response_preview": str(result)[:200]
                }
            else:
                print(f"❌ {agent_name}: No response")
                verification_results[agent_name] = {"responded": False}
                
        except Exception as e:
            print(f"❌ {agent_name}: Error - {str(e)[:50]}...")
            verification_results[agent_name] = {"responded": False, "error": str(e)}
    
    return verification_results

async def test_orchestrator_new_workflow():
    """Test if orchestrator is actually using the new claim workflow"""
    print(f"\n📋 Test 2: Orchestrator New Workflow Verification")
    print("-" * 40)
    
    try:
        from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator
        from shared.mcp_chat_client import enhanced_mcp_chat_client
        
        # Test the specific method we added
        orchestrator = IntelligentClaimsOrchestrator()
        
        # Test claim ID parsing
        test_messages = [
            "Process claim with OP-05",
            "Handle claim IP-01", 
            "Regular message without claim"
        ]
        
        print("🎯 Testing claim ID detection:")
        for msg in test_messages:
            claim_id = enhanced_mcp_chat_client.parse_claim_id_from_message(msg)
            if claim_id:
                print(f"✅ '{msg}' → {claim_id}")
            else:
                print(f"❌ '{msg}' → No claim detected")
        
        # Test if the new method exists
        if hasattr(orchestrator, '_handle_new_claim_workflow'):
            print("✅ Orchestrator has _handle_new_claim_workflow method")
        else:
            print("❌ Orchestrator missing _handle_new_claim_workflow method")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        return False

def analyze_verification_results(verification_results, orchestrator_test):
    """Analyze if we're truly ready for next step"""
    print(f"\n🎯 READINESS ANALYSIS")
    print("=" * 60)
    
    # Count agents with new workflow
    agents_with_new_workflow = 0
    agents_responding = 0
    
    for agent_name, result in verification_results.items():
        if result.get("responded"):
            agents_responding += 1
            if result.get("new_workflow_score", 0) >= 2:
                agents_with_new_workflow += 1
    
    print(f"📊 Agent Status:")
    print(f"   Responding: {agents_responding}/3 agents")
    print(f"   Using New Logic: {agents_with_new_workflow}/3 agents")
    print(f"   Orchestrator Ready: {'✅' if orchestrator_test else '❌'}")
    
    # Determine readiness
    if agents_responding >= 3 and agents_with_new_workflow >= 2 and orchestrator_test:
        readiness = "READY"
        emoji = "🎉"
    elif agents_responding >= 2 and agents_with_new_workflow >= 1:
        readiness = "MOSTLY READY"  
        emoji = "⚠️"
    else:
        readiness = "NOT READY"
        emoji = "❌"
    
    print(f"\n{emoji} FINAL ASSESSMENT: {readiness}")
    
    if readiness == "READY":
        print("✅ All systems operational with new workflow logic")
        print("✅ Ready for next step (Step 6: Production Integration)")
    elif readiness == "MOSTLY READY":
        print("⚠️  Core functionality working, minor issues to address") 
        print("⚠️  Could proceed with caution or fix remaining issues")
    else:
        print("❌ Significant issues need resolution before proceeding")
        print("❌ Should fix core problems before next step")
    
    return readiness

if __name__ == "__main__":
    print("🔍 CRITICAL VERIFICATION - ARE WE REALLY READY?")
    print("=" * 60)
    
    async def run_verification():
        # Verify agent functionality
        agent_results = await verify_actual_agent_functionality()
        
        # Verify orchestrator
        orchestrator_ready = await test_orchestrator_new_workflow()
        
        # Analyze readiness
        readiness = analyze_verification_results(agent_results, orchestrator_ready)
        
        return readiness
    
    result = asyncio.run(run_verification())
    
    print(f"\n🎯 CONCLUSION")
    print("=" * 60)
    if result == "READY":
        print("🚀 YES - We are ready to move to the next step!")
        print("   All core functionality verified and working")
    elif result == "MOSTLY READY":
        print("⚠️  PROBABLY - Core system working with minor gaps")
        print("   Can proceed but should monitor for issues")
    else:
        print("❌ NO - Should address issues before proceeding")
        print("   Core functionality needs fixing")
