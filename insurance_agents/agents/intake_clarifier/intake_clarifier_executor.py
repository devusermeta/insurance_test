"""
Intake Clarifier Executor
Implements the agent execution logic for the Intake Clarifier
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from shared.mcp_config import A2A_AGENT_PORTS

class IntakeClarifierExecutor:
    """
    Executor for Intake Clarifier Agent
    Implements the business logic for validating and clarifying insurance claims
    """
    
    def __init__(self):
        self.agent_name = "intake_clarifier"
        self.agent_description = "Validates and clarifies incoming insurance claims"
        self.port = A2A_AGENT_PORTS["intake_clarifier"]
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        # Create colored formatter
        formatter = logging.Formatter(
            f"📋 [{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Setup console handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a request using the Intake Clarifier logic
        This is the main entry point for A2A requests
        """
        try:
            self.logger.info(f"🔄 Executing request: {request.get('task', 'unknown')}")
            
            # Extract task and parameters
            task = request.get('task', '')
            parameters = request.get('parameters', {})
            
            # Route to appropriate handler
            if 'clarify' in task.lower() or 'validate' in task.lower():
                return await self._handle_claim_clarification(parameters)
            elif 'fraud' in task.lower() or 'risk' in task.lower():
                return await self._handle_fraud_assessment(parameters)
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
    
    async def _handle_claim_clarification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle claim clarification and validation requests"""
        self.logger.info("📋 Performing claim clarification")
        
        # Extract claim information
        claim_id = parameters.get('claim_id', f"CLARIFY_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        claim_type = parameters.get('claim_type', 'unknown')
        description = parameters.get('description', '')
        documents = parameters.get('documents', [])
        customer_id = parameters.get('customer_id', '')
        
        # Perform clarification analysis
        clarification_result = await self._perform_clarification_analysis({
            'claim_id': claim_id,
            'claim_type': claim_type,
            'description': description,
            'documents': documents,
            'customer_id': customer_id
        })
        
        return {
            "status": "success",
            "claim_id": claim_id,
            "clarification_result": clarification_result,
            "agent": self.agent_name
        }
    
    async def _handle_fraud_assessment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fraud risk assessment requests"""
        self.logger.info("🚨 Performing fraud risk assessment")
        
        claim_data = parameters.get('claim_data', {})
        
        # Perform fraud assessment
        fraud_assessment = await self._assess_fraud_risk(claim_data)
        
        return {
            "status": "success",
            "fraud_assessment": fraud_assessment,
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
                "Validate claim completeness",
                "Assess fraud risk",
                "Generate clarification questions",
                "Check customer information",
                "Score claim quality"
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
                "Claims validation and clarification",
                "Fraud risk assessment",
                "Customer information verification",
                "Document completeness checking"
            ]
        }
    
    async def _perform_clarification_analysis(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive claim clarification analysis"""
        claim_id = claim_data['claim_id']
        self.logger.info(f"🔍 Analyzing claim for clarification: {claim_id}")
        
        clarification_result = {
            "claim_id": claim_id,
            "validation_status": "pending",
            "completeness_score": 0,
            "fraud_risk_score": 0,
            "issues": [],
            "questions": [],
            "recommendations": []
        }
        
        try:
            # Check required fields
            required_fields = ['claim_id', 'claim_type', 'customer_id', 'description']
            missing_fields = [field for field in required_fields if not claim_data.get(field)]
            
            if missing_fields:
                clarification_result["issues"].extend(missing_fields)
                clarification_result["questions"].extend([
                    f"Please provide {field.replace('_', ' ')}" for field in missing_fields
                ])
            
            # Calculate completeness score
            total_fields = ['claim_id', 'claim_type', 'customer_id', 'description', 'documents']
            provided_fields = [field for field in total_fields if claim_data.get(field)]
            clarification_result["completeness_score"] = int((len(provided_fields) / len(total_fields)) * 100)
            
            # Assess description quality
            description = claim_data.get('description', '')
            if len(description) < 20:
                clarification_result["issues"].append("insufficient_description")
                clarification_result["questions"].append("Can you provide more detailed description?")
            
            # Calculate fraud risk
            clarification_result["fraud_risk_score"] = await self._calculate_fraud_risk(claim_data)
            
            # Determine validation status
            if missing_fields or clarification_result["fraud_risk_score"] > 70:
                clarification_result["validation_status"] = "requires_clarification"
            elif clarification_result["completeness_score"] < 60:
                clarification_result["validation_status"] = "incomplete"
            else:
                clarification_result["validation_status"] = "validated"
            
            # Generate recommendations
            if clarification_result["validation_status"] == "validated":
                clarification_result["recommendations"].append("Proceed to document analysis")
            else:
                clarification_result["recommendations"].append("Address validation issues before proceeding")
            
            self.logger.info(f"✅ Clarification completed: {clarification_result['validation_status']}")
            
            return clarification_result
            
        except Exception as e:
            self.logger.error(f"❌ Clarification analysis failed: {str(e)}")
            clarification_result["validation_status"] = "error"
            clarification_result["issues"].append(f"Analysis error: {str(e)}")
            return clarification_result
    
    async def _assess_fraud_risk(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess fraud risk for a claim"""
        self.logger.info("🚨 Assessing fraud risk")
        
        fraud_score = await self._calculate_fraud_risk(claim_data)
        
        risk_level = "low"
        if fraud_score > 70:
            risk_level = "high"
        elif fraud_score > 40:
            risk_level = "medium"
        
        return {
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "factors": self._get_fraud_factors(claim_data),
            "recommendations": self._get_fraud_recommendations(fraud_score)
        }
    
    async def _calculate_fraud_risk(self, claim_data: Dict[str, Any]) -> int:
        """Calculate fraud risk score (0-100)"""
        risk_score = 0
        
        # Check description quality
        description = claim_data.get('description', '').lower()
        if len(description) < 10:
            risk_score += 20
        
        # Check for high-risk keywords
        high_risk_keywords = ['total loss', 'stolen', 'fire', 'flood']
        risk_keywords_found = sum(1 for keyword in high_risk_keywords if keyword in description)
        risk_score += risk_keywords_found * 15
        
        # Check claim timing (mock weekend logic)
        risk_score += 10  # Mock timing risk
        
        return min(risk_score, 100)
    
    def _get_fraud_factors(self, claim_data: Dict[str, Any]) -> List[str]:
        """Get factors contributing to fraud risk"""
        factors = []
        
        description = claim_data.get('description', '').lower()
        
        if len(description) < 10:
            factors.append("Very brief claim description")
        
        if 'total loss' in description:
            factors.append("Total loss claim")
        
        if not claim_data.get('documents'):
            factors.append("No supporting documents provided")
        
        return factors
    
    def _get_fraud_recommendations(self, fraud_score: int) -> List[str]:
        """Get recommendations based on fraud score"""
        recommendations = []
        
        if fraud_score > 70:
            recommendations.extend([
                "Flag for manual fraud investigation",
                "Request additional documentation",
                "Verify customer identity"
            ])
        elif fraud_score > 40:
            recommendations.extend([
                "Increase documentation requirements",
                "Perform additional validation checks"
            ])
        else:
            recommendations.append("Standard processing approved")
        
        return recommendations
