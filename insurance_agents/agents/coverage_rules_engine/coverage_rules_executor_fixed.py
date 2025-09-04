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
            # Extract message from context
            message = context.message
            task_text = ""
            
            # Extract text from message parts
            if hasattr(message, 'parts') and message.parts:
                for part in message.parts:
                    if hasattr(part, 'text'):
                        task_text += part.text + " "
            
            task_text = task_text.strip()
            self.logger.info(f"🔄 A2A Executing task: {task_text[:100]}...")
            
            # Process the coverage rules evaluation
            result = await self._process_coverage_rules_task(task_text)
            
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
        """Process coverage rules evaluation based on the request text"""
        
        task_lower = task_text.lower()
        
        # Simulate coverage evaluation
        self.logger.info("⚖️ Evaluating coverage rules...")
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

# Create the fixed executor instance
CoverageRulesExecutor = CoverageRulesExecutorFixed

print("⚖️ FIXED Coverage Rules Engine Executor loaded successfully!")
print("✅ A2A compatible version with correct parameter handling")
