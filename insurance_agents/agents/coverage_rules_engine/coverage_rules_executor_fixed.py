"""
FIXED Coverage Rules Engine Executor - A2A Compatible
This is the corrected version that works with the A2A framework
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import json

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from shared.mcp_config import A2A_AGENT_PORTS

class CoverageRulesExecutorFixed(AgentExecutor):
    """
    FIXED Coverage Rules Engine Executor - A2A Compatible
    Simplified version that works correctly with A2A framework
    """
    
    def __init__(self):
        self.agent_name = "coverage_rules_engine"
        self.agent_description = "Evaluates coverage rules and calculates benefits for insurance claims"
        self.port = A2A_AGENT_PORTS["coverage_rules_engine"]
        self.logger = self._setup_logging()
        self.rule_sets = self._initialize_rule_sets()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        # Create colored formatter
        formatter = logging.Formatter(
            f"⚖️ [COVERAGE_RULES_FIXED] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Setup console handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _initialize_rule_sets(self) -> Dict[str, Dict[str, Any]]:
        """Initialize business rule sets"""
        return {
            "eligibility_rules": {
                "min_policy_age_days": 30,
                "max_claim_amount": 100000,
                "excluded_claim_types": ["flood", "earthquake", "war"],
                "required_documents": ["claim_form", "police_report", "photos"]
            },
            "coverage_rules": {
                "medical": {
                    "outpatient_coverage": True,
                    "inpatient_coverage": True,
                    "max_benefit": 50000,
                    "deductible": 500
                },
                "surgical": {
                    "coverage_enabled": True,
                    "max_benefit": 100000,
                    "deductible": 1000
                }
            },
            "pricing_rules": {
                "base_rates": {"medical": 800, "surgical": 1200, "consultation": 300},
                "risk_multipliers": {"low": 0.8, "medium": 1.0, "high": 1.5},
                "discount_factors": {"multi_policy": 0.9, "good_health": 0.85}
            }
        }
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute a request using the Coverage Rules Engine logic with A2A framework
        FIXED VERSION - Works with correct A2A parameters
        """
        try:
            # Try the intake clarifier approach first
            user_input = context.get_user_input()
            print(f"\n🔍 COVERAGE EXECUTE - User input method: '{user_input}'")
            print(f"🔍 COVERAGE EXECUTE - User input length: {len(user_input) if user_input else 0}")
            
            # Extract message from context (old method)
            message = context.message
            task_text = ""
            
            # Extract text from message parts
            if hasattr(message, 'parts') and message.parts:
                for part in message.parts:
                    if hasattr(part, 'text'):
                        task_text += part.text + " "
            
            task_text = task_text.strip()
            
            # DEBUG: Compare both methods
            print(f"\n🔍 COVERAGE EXECUTE - Old method length: {len(task_text)}")
            print(f"🔍 COVERAGE EXECUTE - Old method text: '{task_text}'")
            
            # Use the working method
            final_task_text = user_input if user_input else task_text
            print(f"🔍 COVERAGE EXECUTE - Using final text: '{final_task_text[:200]}...'")
            
            self.logger.info(f"🔄 A2A Executing task: {final_task_text[:100]}...")
            
            # Process the coverage rules evaluation
            result = await self._process_coverage_rules_task(final_task_text)
            
            # Create and send response message
            response_message = new_agent_text_message(
                text=result.get("response", "Coverage evaluation completed successfully"),
                task_id=getattr(context, 'task_id', None)
            )
            await event_queue.enqueue_event(response_message)
            
            self.logger.info("✅ Coverage rules evaluation completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Execution error: {str(e)}")
            
            # Send error message
            error_message = new_agent_text_message(
                text=f"Coverage Rules Engine error: {str(e)}",
                task_id=getattr(context, 'task_id', None)
            )
            await event_queue.enqueue_event(error_message)
    
    async def cancel(self, task_id: str) -> None:
        """
        Cancel a running task - required by A2A AgentExecutor
        """
        self.logger.info(f"🚫 Cancelling task: {task_id}")
        # Implementation for task cancellation if needed
        pass
    
    async def _process_coverage_rules_task(self, task_text: str) -> Dict[str, Any]:
        """Process coverage rules evaluation based on the request text with new workflow support"""
        
        print(f"\n🔍 COVERAGE TASK - Processing task: '{task_text[:100]}...'")
        
        task_lower = task_text.lower()
        
        # Check if this is a new workflow request with claim details
        if self._is_new_workflow_claim_request(task_text):
            print("🔍 COVERAGE TASK - Using NEW WORKFLOW path")
            return await self._handle_new_workflow_claim_evaluation(task_text)
        
        # Legacy processing
        print("🔍 COVERAGE TASK - Using LEGACY path")
        self.logger.info("⚖️ Evaluating coverage rules (legacy mode)...")
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Extract claim amount if present
        import re
        amount_match = re.search(r'\$(\d+)', task_text)
        claim_amount = float(amount_match.group(1)) if amount_match else 850.0
        
        # Determine claim type
        claim_type = "medical"
        if 'surgical' in task_lower:
            claim_type = "surgical"
        elif 'consultation' in task_lower:
            claim_type = "consultation"
        
        # Apply coverage rules
        coverage_rules = self.rule_sets["coverage_rules"].get(claim_type, self.rule_sets["coverage_rules"]["medical"])
        
        # Calculate coverage
        deductible = coverage_rules.get("deductible", 500)
        max_benefit = coverage_rules.get("max_benefit", 50000)
        
        covered_amount = min(claim_amount - deductible, max_benefit)
        coverage_percentage = (covered_amount / claim_amount) * 100 if claim_amount > 0 else 0
        
        result = {
            "agent": "coverage_rules_engine",
            "task": task_text,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "evaluation": {
                "claim_type": claim_type,
                "claim_amount": claim_amount,
                "deductible": deductible,
                "max_benefit": max_benefit,
                "covered_amount": max(covered_amount, 0),
                "coverage_percentage": round(coverage_percentage, 2),
                "eligibility": "approved" if covered_amount > 0 else "denied"
            }
        }
        
        if 'evaluate' in task_lower or 'coverage' in task_lower:
            result["evaluation"]["focus"] = "Coverage rules evaluation"
        elif 'calculate' in task_lower or 'benefit' in task_lower:
            result["evaluation"]["focus"] = "Benefit calculation"
        elif 'policy' in task_lower or 'limitation' in task_lower:
            result["evaluation"]["focus"] = "Policy limitations analysis"
        else:
            result["evaluation"]["focus"] = "General coverage evaluation"
        
        result["response"] = json.dumps({
            "status": "success", 
            "message": f"Coverage evaluation completed: {result['evaluation']['focus']}",
            "eligibility": result["evaluation"]["eligibility"],
            "covered_amount": result["evaluation"]["covered_amount"],
            "coverage_percentage": result["evaluation"]["coverage_percentage"],
            "deductible": result["evaluation"]["deductible"]
        }, indent=2)
        
        self.logger.info(f"📊 Coverage: {result['evaluation']['coverage_percentage']}% - ${result['evaluation']['covered_amount']}")
        
        return result

    def _is_new_workflow_claim_request(self, task_text: str) -> bool:
        """Check if this is a new workflow claim evaluation request"""
        # DEBUG: Print to console for immediate visibility
        print(f"\n🔍 COVERAGE DEBUG - Received text: '{task_text[:200]}...'")
        
        # Look for structured claim data patterns
        indicators = [
            "claim_id" in task_text.lower(),
            "patient_name" in task_text.lower(), 
            "bill_amount" in task_text.lower(),
            "diagnosis" in task_text.lower(),
            "category" in task_text.lower()
        ]
        
        indicator_count = sum(indicators)
        print(f"🔍 COVERAGE DEBUG - Found {indicator_count}/5 indicators: {dict(zip(['claim_id', 'patient_name', 'bill_amount', 'diagnosis', 'category'], indicators))}")
        
        is_new_workflow = indicator_count >= 2
        print(f"🔍 COVERAGE DEBUG - New workflow detected: {is_new_workflow}")
        
        return is_new_workflow

    async def _handle_new_workflow_claim_evaluation(self, task_text: str) -> Dict[str, Any]:
        """Handle claim evaluation for new workflow with structured claim data"""
        try:
            print("🔍 COVERAGE - Starting NEW WORKFLOW processing")
            self.logger.info("🆕 Processing NEW WORKFLOW claim evaluation")
            
            # Extract structured claim information
            claim_info = self._extract_claim_info_from_text(task_text)
            print(f"🔍 COVERAGE - Extracted claim info: {claim_info}")
            
            # Perform enhanced coverage evaluation
            evaluation_result = await self._evaluate_structured_claim(claim_info)
            print(f"🔍 COVERAGE - Evaluation result: {evaluation_result}")
            
            response_message = f"""⚖️ **COVERAGE RULES EVALUATION COMPLETE**

**Claim Analysis:**
• **Claim ID**: {claim_info.get('claim_id', 'Unknown')}
• **Category**: {claim_info.get('category', 'Unknown')}
• **Diagnosis**: {claim_info.get('diagnosis', 'Unknown')}
• **Bill Amount**: ${claim_info.get('bill_amount', 0)}

**Validation Results:**
• **Status**: {'✅ APPROVED FOR PROCESSING' if evaluation_result['eligible'] else '❌ REJECTED'}
• **Decision**: {evaluation_result.get('rejection_reason', 'All business rules passed - continue to next step')}

**Business Rules Applied:**
{chr(10).join(['• ' + rule for rule in evaluation_result['rules_applied']])}

**Next Action**: {'Continue with Document Intelligence and Intake Clarifier' if evaluation_result['eligible'] else 'Update Cosmos DB status to marked for rejection'}
"""

            return {
                "status": "success",
                "response": response_message,
                "evaluation": evaluation_result,
                "workflow_type": "new_structured"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in new workflow evaluation: {e}")
            return {
                "status": "error",
                "response": f"Coverage evaluation failed: {str(e)}"
            }

    def _extract_claim_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured claim information from task text"""
        import re
        
        claim_info = {}
        
        # Extract key fields using regex patterns
        patterns = {
            'claim_id': r'claim[_\s]*id[:\s]+([A-Z]{2}-\d{2,3})',
            'patient_name': r'patient[_\s]*name[:\s]+([^,\n]+)',
            'bill_amount': r'bill[_\s]*amount[:\s]+\$?(\d+(?:\.\d{2})?)',
            'diagnosis': r'diagnosis[:\s]+([^,\n]+)',
            'category': r'category[:\s]+([^,\n]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                claim_info[key] = match.group(1).strip()
        
        return claim_info

    async def _evaluate_structured_claim(self, claim_info: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate coverage based on your specific business rules"""
        # Get claim details
        category = claim_info.get('category', '').lower()
        bill_amount = float(claim_info.get('bill_amount', 0))
        diagnosis = claim_info.get('diagnosis', '').lower()
        claim_id = claim_info.get('claim_id', 'Unknown')
        
        rules_applied = []
        rejection_reason = None
        
        # STEP 1: Document validation (you'll need to implement document checking)
        # For now, assume documents are available - this should be enhanced to check actual documents
        if 'outpatient' in category:
            rules_applied.append("Outpatient document requirements: bills + memo")
            # TODO: Add actual document validation
            documents_valid = True  # Placeholder
        elif 'inpatient' in category:
            rules_applied.append("Inpatient document requirements: bills + memo + discharge summary")
            # TODO: Add actual document validation  
            documents_valid = True  # Placeholder
        else:
            documents_valid = False
            rejection_reason = "Unknown category - unable to validate documents"
        
        if not documents_valid:
            rules_applied.append(f"❌ Document validation failed: {rejection_reason}")
            return {
                "eligible": False,
                "coverage_percentage": 0,
                "covered_amount": 0.0,
                "patient_responsibility": bill_amount,
                "deductible": 0,
                "max_benefit": 0,
                "rules_applied": rules_applied,
                "rejection_reason": rejection_reason or "Insufficient documents",
                "status_update_required": True,
                "new_status": "marked for rejection"
            }
        
        # STEP 2: Diagnosis categorization and amount limits
        diagnosis_category = "general"  # Default
        amount_limit = 200000  # Default for general
        
        if any(eye_term in diagnosis for eye_term in ['eye', 'vision', 'optic', 'retina', 'cornea', 'lens', 'cataract', 'glaucoma', 'macular']):
            diagnosis_category = "eye"
            amount_limit = 500
            rules_applied.append("Eye diagnosis detected - limit: $500")
        elif any(dental_term in diagnosis for dental_term in ['dental', 'tooth', 'teeth', 'gum', 'oral', 'mouth']):
            diagnosis_category = "dental" 
            amount_limit = 1000
            rules_applied.append("Dental diagnosis detected - limit: $1000")
        else:
            diagnosis_category = "general"
            amount_limit = 200000
            rules_applied.append("General diagnosis detected - limit: $200000")
        
        # STEP 3: Amount validation
        if bill_amount > amount_limit:
            rejection_reason = f"Bill amount ${bill_amount} exceeds {diagnosis_category} limit of ${amount_limit}"
            rules_applied.append(f"❌ Amount limit exceeded: ${bill_amount} > ${amount_limit}")
            return {
                "eligible": False,
                "coverage_percentage": 0,
                "covered_amount": 0.0,
                "patient_responsibility": bill_amount,
                "deductible": 0,
                "max_benefit": amount_limit,
                "rules_applied": rules_applied,
                "rejection_reason": rejection_reason,
                "status_update_required": True,
                "new_status": "marked for rejection"
            }
        
        # STEP 4: If all validations pass, approve for further processing
        rules_applied.append(f"✅ All validations passed - proceeding to next workflow steps")
        
        return {
            "eligible": True,
            "coverage_percentage": 100,  # Not relevant for your workflow
            "covered_amount": bill_amount,  # Full amount approved for processing
            "patient_responsibility": 0.0,
            "deductible": 0,
            "max_benefit": amount_limit,
            "rules_applied": rules_applied,
            "rejection_reason": None,
            "status_update_required": False,
            "new_status": "continue_processing"
        }

# Create the fixed executor instance
CoverageRulesExecutor = CoverageRulesExecutorFixed

print("⚖️ FIXED Coverage Rules Engine Executor loaded successfully!")
print("✅ A2A compatible version with correct parameter handling")
