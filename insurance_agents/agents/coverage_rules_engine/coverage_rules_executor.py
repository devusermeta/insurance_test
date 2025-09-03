"""
Coverage Rules Engine Executor
Implements the agent execution logic for Coverage Rules Engine
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from shared.mcp_config import A2A_AGENT_PORTS

class CoverageRulesExecutor:
    """
    Executor for Coverage Rules Engine Agent
    Implements the business logic for coverage evaluation and rules execution
    """
    
    def __init__(self):
        self.agent_name = "coverage_rules_engine"
        self.agent_description = "Evaluates coverage rules and makes policy decisions"
        self.port = A2A_AGENT_PORTS["coverage_rules_engine"]
        self.logger = self._setup_logging()
        
        # Load rule sets
        self.rule_sets = self._initialize_rule_sets()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        # Create colored formatter
        formatter = logging.Formatter(
            f"⚖️ [{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Setup console handler
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
                "auto": {
                    "collision_coverage": True,
                    "comprehensive_coverage": True,
                    "liability_limit": 50000,
                    "deductible": 1000
                },
                "home": {
                    "dwelling_coverage": True,
                    "personal_property": True,
                    "liability_limit": 300000,
                    "deductible": 2500
                }
            },
            "pricing_rules": {
                "base_rates": {"auto": 800, "home": 1200, "life": 300},
                "risk_multipliers": {"low": 0.8, "medium": 1.0, "high": 1.5},
                "discount_factors": {"multi_policy": 0.9, "safe_driver": 0.85, "home_security": 0.95}
            },
            "underwriting_rules": {
                "auto_approval_threshold": 5000,
                "manual_review_threshold": 25000,
                "auto_denial_conditions": ["policy_lapsed", "fraud_detected", "excluded_peril"]
            }
        }
    
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a request using the Coverage Rules Engine logic
        This is the main entry point for A2A requests
        """
        try:
            self.logger.info(f"🔄 Executing request: {request.get('task', 'unknown')}")
            
            # Extract task and parameters
            task = request.get('task', '')
            parameters = request.get('parameters', {})
            
            # Route to appropriate handler
            if 'coverage' in task.lower() or 'evaluate' in task.lower():
                return await self._handle_coverage_evaluation(parameters)
            elif 'policy' in task.lower() or 'analyze' in task.lower():
                return await self._handle_policy_analysis(parameters)
            elif 'rules' in task.lower() or 'execute' in task.lower():
                return await self._handle_rules_execution(parameters)
            elif 'decision' in task.lower() or 'decide' in task.lower():
                return await self._handle_decision_engine(parameters)
            elif 'status' in task.lower():
                return await self._handle_status_request(parameters)
            else:
                return await self._handle_general_request(task, parameters)
                
        except Exception as e:
            self.logger.error(f"❌ Execution error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.agent_name
            }
    
    async def _handle_coverage_evaluation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle coverage evaluation requests"""
        self.logger.info("⚖️ Performing coverage evaluation")
        
        # Extract parameters
        claim_data = parameters.get('claim_data', {})
        policy_data = parameters.get('policy_data', {})
        
        if not claim_data:
            return {
                "status": "error",
                "error": "No claim data provided for evaluation",
                "agent": self.agent_name
            }
        
        # Perform coverage evaluation
        evaluation_result = await self._evaluate_coverage(claim_data, policy_data)
        
        return {
            "status": "success",
            "evaluation_result": evaluation_result,
            "agent": self.agent_name
        }
    
    async def _handle_policy_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle policy analysis requests"""
        self.logger.info("📋 Performing policy analysis")
        
        policy_number = parameters.get('policy_number', '')
        analysis_type = parameters.get('analysis_type', 'full_analysis')
        
        if not policy_number:
            return {
                "status": "error",
                "error": "No policy number provided",
                "agent": self.agent_name
            }
        
        # Perform policy analysis
        analysis_result = await self._analyze_policy(policy_number, analysis_type)
        
        return {
            "status": "success",
            "policy_number": policy_number,
            "analysis_type": analysis_type,
            "analysis_result": analysis_result,
            "agent": self.agent_name
        }
    
    async def _handle_rules_execution(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rules execution requests"""
        self.logger.info("🔧 Executing business rules")
        
        rule_set = parameters.get('rule_set', '')
        input_data = parameters.get('input_data', {})
        
        if not rule_set:
            return {
                "status": "error",
                "error": "No rule set specified",
                "agent": self.agent_name
            }
        
        # Execute rules
        execution_result = await self._execute_rules(rule_set, input_data)
        
        return {
            "status": "success",
            "rule_set": rule_set,
            "execution_result": execution_result,
            "agent": self.agent_name
        }
    
    async def _handle_decision_engine(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle decision engine requests"""
        self.logger.info("🎯 Making automated decision")
        
        decision_type = parameters.get('decision_type', '')
        context = parameters.get('context', {})
        
        if not decision_type:
            return {
                "status": "error",
                "error": "No decision type specified",
                "agent": self.agent_name
            }
        
        # Make decision
        decision_result = await self._make_decision(decision_type, context)
        
        return {
            "status": "success",
            "decision_type": decision_type,
            "decision_result": decision_result,
            "agent": self.agent_name
        }
    
    async def _handle_status_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status check requests"""
        return {
            "status": "success",
            "agent_status": "running",
            "agent": self.agent_name,
            "port": self.port,
            "timestamp": datetime.now().isoformat(),
            "capabilities": [
                "Coverage evaluation and eligibility",
                "Policy analysis and interpretation",
                "Business rules execution",
                "Automated decision making",
                "Risk assessment and scoring"
            ]
        }
    
    async def _handle_general_request(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general requests"""
        self.logger.info(f"🤖 Handling general request: {task}")
        
        return {
            "status": "success",
            "message": f"Processed task: {task}",
            "task": task,
            "parameters": parameters,
            "agent": self.agent_name,
            "specialties": [
                "Insurance coverage evaluation",
                "Policy terms analysis",
                "Business rules engine",
                "Automated decision making",
                "Risk and eligibility assessment"
            ]
        }
    
    async def _evaluate_coverage(self, claim_data: Dict[str, Any], policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate insurance coverage for a claim"""
        claim_type = claim_data.get('claim_type', 'auto')
        policy_number = claim_data.get('policy_number', '')
        damage_amount = claim_data.get('damage_amount', 0)
        
        self.logger.info(f"⚖️ Evaluating coverage for claim type: {claim_type}, amount: ${damage_amount}")
        
        evaluation = {
            "policy_number": policy_number,
            "claim_type": claim_type,
            "damage_amount": damage_amount,
            "coverage_decision": "pending",
            "eligible_amount": 0,
            "deductible": 0,
            "coverage_details": {},
            "exclusions_applied": [],
            "decision_factors": []
        }
        
        try:
            # Check eligibility rules
            eligibility_check = await self._check_eligibility(claim_data)
            
            if not eligibility_check["is_eligible"]:
                evaluation["coverage_decision"] = "denied"
                evaluation["denial_reasons"] = eligibility_check["reasons"]
                return evaluation
            
            # Get coverage rules for claim type
            coverage_rules = self.rule_sets["coverage_rules"].get(claim_type, {})
            
            if not coverage_rules:
                evaluation["coverage_decision"] = "denied"
                evaluation["denial_reasons"] = [f"No coverage rules found for claim type: {claim_type}"]
                return evaluation
            
            # Calculate coverage
            deductible = coverage_rules.get("deductible", 1000)
            liability_limit = coverage_rules.get("liability_limit", 50000)
            
            # Apply deductible
            if damage_amount > deductible:
                eligible_amount = min(damage_amount - deductible, liability_limit)
                evaluation["coverage_decision"] = "approved"
            else:
                eligible_amount = 0
                evaluation["coverage_decision"] = "denied"
                evaluation["denial_reasons"] = ["Damage amount below deductible"]
            
            evaluation.update({
                "eligible_amount": eligible_amount,
                "deductible": deductible,
                "coverage_details": coverage_rules,
                "decision_factors": [
                    f"Deductible: ${deductible}",
                    f"Coverage limit: ${liability_limit}",
                    f"Claim amount: ${damage_amount}"
                ]
            })
            
            self.logger.info(f"✅ Coverage evaluation complete: {evaluation['coverage_decision']}")
            return evaluation
            
        except Exception as e:
            self.logger.error(f"❌ Coverage evaluation failed: {str(e)}")
            evaluation["coverage_decision"] = "error"
            evaluation["error"] = str(e)
            return evaluation
    
    async def _analyze_policy(self, policy_number: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze policy terms and conditions"""
        self.logger.info(f"📋 Analyzing policy {policy_number} for {analysis_type}")
        
        # Mock policy data
        policy_info = {
            "policy_number": policy_number,
            "policy_type": "auto",
            "effective_date": "2024-01-01",
            "expiration_date": "2024-12-31",
            "premium": 1200,
            "status": "active"
        }
        
        analysis_result = {
            "policy_info": policy_info,
            "analysis_type": analysis_type,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        if analysis_type in ["coverage_limits", "full_analysis"]:
            analysis_result["coverage_limits"] = {
                "liability": 50000,
                "collision": 25000,
                "comprehensive": 25000,
                "medical": 10000
            }
        
        if analysis_type in ["exclusions", "full_analysis"]:
            analysis_result["exclusions"] = [
                "Racing or speed contests",
                "Using vehicle for commercial purposes",
                "Intentional damage",
                "War or nuclear hazard"
            ]
        
        if analysis_type in ["deductibles", "full_analysis"]:
            analysis_result["deductibles"] = {
                "collision": 1000,
                "comprehensive": 500
            }
        
        if analysis_type in ["premium_calculation", "full_analysis"]:
            analysis_result["premium_breakdown"] = {
                "base_rate": 800,
                "risk_adjustment": 200,
                "discounts": -100,
                "taxes_fees": 300,
                "total": 1200
            }
        
        return analysis_result
    
    async def _execute_rules(self, rule_set: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific business rules"""
        self.logger.info(f"🔧 Executing {rule_set} rules")
        
        if rule_set not in self.rule_sets:
            return {
                "status": "error",
                "error": f"Unknown rule set: {rule_set}"
            }
        
        rules = self.rule_sets[rule_set]
        execution_result = {
            "rule_set": rule_set,
            "rules_applied": [],
            "results": {},
            "status": "completed"
        }
        
        if rule_set == "eligibility_rules":
            result = await self._check_eligibility(input_data)
            execution_result["results"] = result
            execution_result["rules_applied"] = ["policy_age", "claim_amount", "excluded_types", "required_docs"]
        
        elif rule_set == "pricing_rules":
            result = await self._calculate_pricing(input_data)
            execution_result["results"] = result
            execution_result["rules_applied"] = ["base_rates", "risk_multipliers", "discounts"]
        
        elif rule_set == "underwriting_rules":
            result = await self._apply_underwriting_rules(input_data)
            execution_result["results"] = result
            execution_result["rules_applied"] = ["approval_threshold", "review_threshold", "denial_conditions"]
        
        return execution_result
    
    async def _make_decision(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make automated decisions based on rules and context"""
        self.logger.info(f"🎯 Making {decision_type} decision")
        
        decision_result = {
            "decision_type": decision_type,
            "decision": "pending",
            "confidence": 0,
            "reasoning": [],
            "timestamp": datetime.now().isoformat()
        }
        
        if decision_type == "approve":
            decision_result.update(await self._make_approval_decision(context))
        elif decision_type == "deny":
            decision_result.update(await self._make_denial_decision(context))
        elif decision_type == "review":
            decision_result.update(await self._make_review_decision(context))
        elif decision_type == "calculate":
            decision_result.update(await self._make_calculation_decision(context))
        
        return decision_result
    
    async def _check_eligibility(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check claim eligibility against rules"""
        rules = self.rule_sets["eligibility_rules"]
        
        eligibility = {
            "is_eligible": True,
            "reasons": [],
            "checks_passed": []
        }
        
        # Check claim amount
        damage_amount = claim_data.get('damage_amount', 0)
        if damage_amount > rules["max_claim_amount"]:
            eligibility["is_eligible"] = False
            eligibility["reasons"].append(f"Claim amount ${damage_amount} exceeds maximum ${rules['max_claim_amount']}")
        else:
            eligibility["checks_passed"].append("claim_amount_within_limits")
        
        # Check claim type
        claim_type = claim_data.get('claim_type', '').lower()
        if claim_type in rules["excluded_claim_types"]:
            eligibility["is_eligible"] = False
            eligibility["reasons"].append(f"Claim type '{claim_type}' is excluded")
        else:
            eligibility["checks_passed"].append("claim_type_covered")
        
        return eligibility
    
    async def _calculate_pricing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate pricing based on rules"""
        rules = self.rule_sets["pricing_rules"]
        
        policy_type = input_data.get('policy_type', 'auto')
        risk_level = input_data.get('risk_level', 'medium')
        discounts = input_data.get('discounts', [])
        
        base_rate = rules["base_rates"].get(policy_type, 1000)
        risk_multiplier = rules["risk_multipliers"].get(risk_level, 1.0)
        
        # Apply discounts
        discount_factor = 1.0
        for discount in discounts:
            if discount in rules["discount_factors"]:
                discount_factor *= rules["discount_factors"][discount]
        
        final_premium = base_rate * risk_multiplier * discount_factor
        
        return {
            "base_rate": base_rate,
            "risk_multiplier": risk_multiplier,
            "discount_factor": discount_factor,
            "final_premium": round(final_premium, 2),
            "discounts_applied": discounts
        }
    
    async def _apply_underwriting_rules(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply underwriting rules"""
        rules = self.rule_sets["underwriting_rules"]
        
        claim_amount = input_data.get('claim_amount', 0)
        conditions = input_data.get('conditions', [])
        
        decision = "approve"
        reasoning = []
        
        # Check auto denial conditions
        for condition in conditions:
            if condition in rules["auto_denial_conditions"]:
                decision = "deny"
                reasoning.append(f"Auto denial condition met: {condition}")
                break
        
        # Check thresholds
        if decision != "deny":
            if claim_amount > rules["manual_review_threshold"]:
                decision = "review"
                reasoning.append(f"Amount ${claim_amount} requires manual review")
            elif claim_amount <= rules["auto_approval_threshold"]:
                decision = "approve"
                reasoning.append(f"Amount ${claim_amount} approved automatically")
            else:
                decision = "review"
                reasoning.append(f"Amount ${claim_amount} requires standard review")
        
        return {
            "underwriting_decision": decision,
            "reasoning": reasoning,
            "claim_amount": claim_amount
        }
    
    async def _make_approval_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make approval decision"""
        # Mock approval logic
        return {
            "decision": "approved",
            "confidence": 85,
            "reasoning": ["All eligibility criteria met", "Within coverage limits"]
        }
    
    async def _make_denial_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make denial decision"""
        # Mock denial logic
        return {
            "decision": "denied",
            "confidence": 90,
            "reasoning": ["Policy exclusion applies", "Claim exceeds coverage limits"]
        }
    
    async def _make_review_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make review decision"""
        # Mock review logic
        return {
            "decision": "review_required",
            "confidence": 70,
            "reasoning": ["High claim amount", "Additional documentation needed"]
        }
    
    async def _make_calculation_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make calculation decision"""
        # Mock calculation logic
        return {
            "decision": "calculated",
            "confidence": 95,
            "reasoning": ["Standard calculation applied", "All factors considered"],
            "calculated_amount": 4500
        }
