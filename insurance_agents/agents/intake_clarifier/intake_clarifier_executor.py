"""
Intake Clarifier Executor
Implements the agent execution logic for the Intake Clarifier with A2A and MCP integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from shared.mcp_config import A2A_AGENT_PORTS
from shared.mcp_client import MCPClient

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
        
        # Initialize MCP client for Cosmos DB access
        self.mcp_client = MCPClient()
        
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
            if 'clarify_claim_intake' in task.lower():
                return await self._handle_a2a_claim_clarification(parameters)
            elif 'clarify' in task.lower() or 'validate' in task.lower():
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
    
    async def _handle_a2a_claim_clarification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle A2A claim clarification requests from Claims Orchestrator
        
        Args:
            parameters: Contains claim_data from orchestrator
            
        Returns:
            Clarified claim data
        """
        try:
            self.logger.info("📨 Handling A2A claim clarification request")
            
            claim_data = parameters.get('claim_data', {})
            claim_id = claim_data.get('claim_id', 'UNKNOWN')
            
            # Use MCP to check existing claims data
            self.logger.info(f"🔍 Checking existing claims for {claim_id} using MCP...")
            existing_claims = await self.mcp_client.get_claims(claim_id)
            
            # Perform clarification analysis
            clarified_data = await self._clarify_claim_data(claim_data)
            
            # Perform completeness check
            completeness_score = self._calculate_completeness_score(clarified_data)
            
            # Perform fraud risk assessment
            fraud_risk_score = self._calculate_fraud_risk(clarified_data)
            
            self.logger.info(f"✅ Claim clarification completed for {claim_id}")
            
            return {
                "status": "completed",
                "clarified_data": clarified_data,
                "completeness_score": completeness_score,
                "fraud_risk_score": fraud_risk_score,
                "validation_status": "validated" if completeness_score > 70 else "incomplete",
                "agent": self.agent_name,
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ A2A clarification error: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "agent": self.agent_name
            }
    
    async def _clarify_claim_data(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clarify and enhance claim data
        
        Args:
            claim_data: Raw claim data
            
        Returns:
            Clarified claim data
        """
        clarified = claim_data.copy()
        
        # Add standardized fields
        clarified['claim_type_standardized'] = self._standardize_claim_type(claim_data.get('type', ''))
        clarified['amount_numeric'] = self._extract_numeric_amount(claim_data.get('amount', 0))
        clarified['date_standardized'] = self._standardize_date(claim_data.get('date', ''))
        
        # Add derived fields
        clarified['urgency_level'] = self._determine_urgency(clarified)
        clarified['complexity_score'] = self._calculate_complexity(clarified)
        
        return clarified
    
    def _standardize_claim_type(self, claim_type: str) -> str:
        """Standardize claim type"""
        claim_type_lower = claim_type.lower()
        if 'auto' in claim_type_lower or 'vehicle' in claim_type_lower:
            return 'automotive'
        elif 'home' in claim_type_lower or 'property' in claim_type_lower:
            return 'property'
        elif 'health' in claim_type_lower or 'medical' in claim_type_lower:
            return 'medical'
        else:
            return 'general'
    
    def _extract_numeric_amount(self, amount) -> float:
        """Extract numeric amount from various formats"""
        if isinstance(amount, (int, float)):
            return float(amount)
        elif isinstance(amount, str):
            # Remove currency symbols and extract number
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', amount.replace(',', ''))
            return float(numbers[0]) if numbers else 0.0
        else:
            return 0.0
    
    def _standardize_date(self, date_str) -> str:
        """Standardize date format"""
        if not date_str:
            return datetime.now().isoformat()
        # In a real implementation, this would handle various date formats
        return str(date_str)
    
    def _determine_urgency(self, claim_data: Dict[str, Any]) -> str:
        """Determine claim urgency level"""
        amount = claim_data.get('amount_numeric', 0)
        claim_type = claim_data.get('claim_type_standardized', '')
        
        if amount > 100000 or claim_type == 'medical':
            return 'high'
        elif amount > 10000:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_complexity(self, claim_data: Dict[str, Any]) -> int:
        """Calculate claim complexity score (1-10)"""
        complexity = 1
        
        # Add complexity based on various factors
        if claim_data.get('documents'):
            complexity += len(claim_data['documents'])
        
        if claim_data.get('amount_numeric', 0) > 50000:
            complexity += 3
        
        if claim_data.get('claim_type_standardized') == 'medical':
            complexity += 2
        
        return min(complexity, 10)
    
    def _calculate_completeness_score(self, claim_data: Dict[str, Any]) -> int:
        """Calculate how complete the claim data is (0-100)"""
        required_fields = ['claim_id', 'type', 'amount', 'description']
        optional_fields = ['customer_id', 'date', 'documents', 'policy_number']
        
        score = 0
        
        # Check required fields
        for field in required_fields:
            if claim_data.get(field):
                score += 20
        
        # Check optional fields
        for field in optional_fields:
            if claim_data.get(field):
                score += 5
        
        return min(score, 100)
    
    def _calculate_fraud_risk(self, claim_data: Dict[str, Any]) -> int:
        """Calculate fraud risk score (0-100)"""
        risk = 0
        
        # High amount increases risk
        amount = claim_data.get('amount_numeric', 0)
        if amount > 100000:
            risk += 30
        elif amount > 50000:
            risk += 15
        
        # Multiple claims in short time (mock check)
        risk += 10  # Simplified risk calculation
        
        return min(risk, 100)
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.mcp_client.close()
            self.logger.info("🧹 Resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {str(e)}")
        
        return recommendations
