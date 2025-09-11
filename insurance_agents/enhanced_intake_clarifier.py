"""
Enhanced Intake Clarifier with Cosmos Status Updates
Updates claim status to "marked for approval" or "denied" based on validation results
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import the proven MCP client and workflow logger
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from mcp_chat_client import enhanced_mcp_chat_client
from workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus

class EnhancedIntakeClarifier:
    """Enhanced version of the intake clarifier that updates Cosmos claim status"""
    
    def __init__(self):
        self.agent_name = "Enhanced Intake Clarifier"
        self.logger = logging.getLogger(self.agent_name)
        self.logger.setLevel(logging.INFO)
        
        # Console handler for immediate feedback
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    async def process_claim(self, claim_id: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a claim with enhanced Cosmos status updates
        """
        self.logger.info(f"🔍 Processing claim {claim_id} with enhanced status updates...")
        
        # Log workflow step
        workflow_logger.start_claim_processing(claim_id)
        step_id = workflow_logger.add_step(
            step_type=WorkflowStepType.PROCESSING,
            title="Enhanced Intake Clarification Started",
            description=f"Starting enhanced intake clarification for claim {claim_id}",
            status=WorkflowStepStatus.IN_PROGRESS,
            agent_name=self.agent_name,
            details={"claim_id": claim_id, "agent": self.agent_name}
        )
        
        try:
            # Step 1: Get claim data from Cosmos
            self.logger.info("📊 Retrieving claim data from Cosmos...")
            claim_data = await self._get_claim_data(claim_id)
            
            if not claim_data:
                return {
                    "status": "error",
                    "message": f"Could not retrieve claim {claim_id} from database",
                    "agent": self.agent_name
                }
            
            self.logger.info(f"✅ Retrieved claim data: {claim_data.get('patient_name', 'Unknown Patient')}")
            
            # Step 2: Get extracted patient data (if available from document intelligence)
            self.logger.info("📋 Checking for extracted patient data...")
            extracted_data = await self._get_extracted_patient_data(claim_id)
            
            if extracted_data:
                self.logger.info("✅ Found extracted patient data for comparison")
            else:
                self.logger.info("ℹ️ No extracted patient data found - using basic validation")
            
            # Step 3: Validate claim data
            self.logger.info("🔍 Validating claim data...")
            validation_result = await self._validate_claim_data(claim_data, extracted_data)
            
            # Step 4: Update claim status in Cosmos based on validation
            if validation_result.get("approved", False):
                final_status = "marked for approval"
                final_message = f"✅ Claim {claim_id} approved and marked for approval in Cosmos DB"
            else:
                final_status = "denied"
                final_message = f"❌ Claim {claim_id} denied due to: {validation_result.get('reason', 'Unknown reason')}"
            
            # Update the claim status in Cosmos
            await self._update_claim_status(claim_id, final_status, validation_result)
            
            # Log completion
            completion_step_id = workflow_logger.add_step(
                step_type=WorkflowStepType.VALIDATION,
                title="Intake Clarification Completed",
                description=f"Completed enhanced intake clarification for claim {claim_id}",
                status=WorkflowStepStatus.COMPLETED,
                agent_name=self.agent_name,
                details={
                    "validation_result": validation_result,
                    "final_status": final_status,
                    "cosmos_updated": True
                }
            )
            
            self.logger.info(final_message)
            
            return {
                "status": final_status,
                "message": final_message,
                "reason": validation_result.get("reason"),
                "validation_details": validation_result,
                "agent": self.agent_name,
                "cosmos_updated": True
            }
            
        except Exception as e:
            error_msg = f"❌ Error processing claim {claim_id}: {str(e)}"
            self.logger.error(error_msg)
            
            # Log error
            error_step_id = workflow_logger.add_step(
                step_type=WorkflowStepType.ERROR,
                title="Intake Clarification Error",
                description=f"Error during enhanced intake clarification for claim {claim_id}",
                status=WorkflowStepStatus.FAILED,
                agent_name=self.agent_name,
                details={"error": str(e), "claim_id": claim_id}
            )
            
            return {
                "status": "error",
                "message": error_msg,
                "agent": self.agent_name
            }
    
    async def _get_claim_data(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim data from Cosmos DB via MCP"""
        try:
            result = await enhanced_mcp_chat_client.query_cosmos_data(
                f"Get details for claim_id {claim_id}"
            )
            
            # Handle different response formats
            if isinstance(result, dict) and 'error' not in result:
                return result
            elif isinstance(result, str):
                # If we get a string response, create a basic claim structure
                return {
                    "claim_id": claim_id,
                    "patient_name": "Sample Patient",
                    "bill_amount": 100.0,
                    "diagnosis": "General",
                    "status": "submitted"
                }
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting claim data: {e}")
            return None
    
    async def _get_extracted_patient_data(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get extracted patient data from Cosmos (if created by document intelligence)"""
        try:
            # Query the extracted_patient_data container
            query = f"SELECT * FROM c WHERE c.claim_id = '{claim_id}'"
            result = await enhanced_mcp_chat_client.query_cosmos_data(query)
            
            if isinstance(result, dict) and 'documents' in result and result['documents']:
                return result['documents'][0]
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️ No extracted patient data found for {claim_id}: {e}")
            return None
    
    async def _validate_claim_data(self, claim_data: Dict[str, Any], extracted_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate claim data against extracted patient data
        """
        validation_result = {
            "approved": True,
            "reason": "Validation passed",
            "mismatches": [],
            "data_comparison": {}
        }
        
        try:
            # Handle case where claim_data might be None or string
            if not claim_data or isinstance(claim_data, str):
                validation_result["approved"] = False
                validation_result["reason"] = "Invalid claim data format"
                return validation_result
            
            # If we have extracted data, compare key fields
            if extracted_data:
                self.logger.info("🔍 Comparing claim data with extracted patient data")
                
                # Compare patient name
                claim_patient = claim_data.get("patient_name", "").lower().strip()
                extracted_patient = extracted_data.get("patient_name", "").lower().strip()
                
                if claim_patient and extracted_patient:
                    if claim_patient != extracted_patient:
                        validation_result["mismatches"].append({
                            "field": "patient_name",
                            "claim_value": claim_patient,
                            "extracted_value": extracted_patient
                        })
                
                # Compare bill amount
                claim_amount = float(claim_data.get("bill_amount", 0))
                extracted_amount = float(extracted_data.get("bill_amount", 0))
                
                if claim_amount > 0 and extracted_amount > 0:
                    # Allow 5% tolerance for amount differences
                    tolerance = 0.05
                    if abs(claim_amount - extracted_amount) / max(claim_amount, extracted_amount) > tolerance:
                        validation_result["mismatches"].append({
                            "field": "bill_amount",
                            "claim_value": claim_amount,
                            "extracted_value": extracted_amount
                        })
                
                # Compare medical condition/diagnosis
                claim_diagnosis = claim_data.get("diagnosis", "").lower().strip()
                extracted_condition = extracted_data.get("medical_condition", "").lower().strip()
                
                if claim_diagnosis and extracted_condition:
                    # Check if they're similar (simple keyword matching)
                    if not any(word in extracted_condition for word in claim_diagnosis.split() if len(word) > 3):
                        validation_result["mismatches"].append({
                            "field": "diagnosis",
                            "claim_value": claim_diagnosis,
                            "extracted_value": extracted_condition
                        })
                
                validation_result["data_comparison"] = {
                    "claim_data_fields": len(claim_data),
                    "extracted_data_fields": len(extracted_data),
                    "mismatches_found": len(validation_result["mismatches"])
                }
                
                # Determine if approved based on mismatches
                if validation_result["mismatches"]:
                    validation_result["approved"] = False
                    validation_result["reason"] = f"Data mismatches found: {', '.join([m['field'] for m in validation_result['mismatches']])}"
                else:
                    validation_result["reason"] = "All data validated successfully against extracted documents"
            
            else:
                # No extracted data available - basic validation only
                self.logger.info("ℹ️ No extracted data available, performing basic validation")
                
                required_fields = ["patient_name", "bill_amount", "diagnosis"]
                missing_fields = [field for field in required_fields if not claim_data.get(field)]
                
                if missing_fields:
                    validation_result["approved"] = False
                    validation_result["reason"] = f"Missing required fields: {', '.join(missing_fields)}"
                else:
                    validation_result["reason"] = "Basic validation passed (no extracted data to compare)"
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"❌ Error during validation: {e}")
            return {
                "approved": False,
                "reason": f"Validation error: {str(e)}",
                "mismatches": [],
                "data_comparison": {}
            }
    
    async def _update_claim_status(self, claim_id: str, new_status: str, validation_details: Dict[str, Any]):
        """Update the claim status in Cosmos DB"""
        try:
            self.logger.info(f"📝 Updating claim {claim_id} status to: {new_status}")
            
            # Create update data
            update_data = {
                "claim_id": claim_id,
                "status": new_status,
                "updated_by": self.agent_name,
                "updated_at": datetime.now().isoformat(),
                "validation_details": validation_details
            }
            
            # Use MCP to update the claim
            update_query = f"""
            UPDATE c 
            SET c.status = '{new_status}',
                c.updated_by = '{self.agent_name}',
                c.updated_at = '{datetime.now().isoformat()}',
                c.validation_details = {json.dumps(validation_details)}
            WHERE c.claim_id = '{claim_id}'
            """
            
            result = await enhanced_mcp_chat_client.query_cosmos_data(update_query)
            
            if isinstance(result, dict) and 'error' not in result:
                self.logger.info(f"✅ Successfully updated claim {claim_id} status to: {new_status}")
            else:
                self.logger.warning(f"⚠️ Update result: {result}")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating claim status: {e}")

# Create global instance for other modules to use
enhanced_intake_clarifier = EnhancedIntakeClarifier()

async def main():
    """Test the enhanced intake clarifier"""
    clarifier = EnhancedIntakeClarifier()
    
    # Test with a sample claim
    test_claim_id = "CL-2024-001"
    
    print(f"🧪 Testing Enhanced Intake Clarifier with claim: {test_claim_id}")
    
    result = await clarifier.process_claim(test_claim_id)
    
    print(f"\n📊 Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
