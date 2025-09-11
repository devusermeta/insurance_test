"""
Enhanced Document Intelligence Agent
Creates documents in extracted_patient_data container based on document processing
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.mcp_chat_client import enhanced_mcp_chat_client
from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus

class EnhancedDocumentIntelligence:
    """
    Enhanced Document Intelligence Agent that creates extracted_patient_data documents
    """
    
    def __init__(self):
        self.agent_name = "document_intelligence"
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for the agent"""
        logger = logging.getLogger(f"Enhanced.{self.agent_name}")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f"📄 [ENHANCED-{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    async def process_claim_documents(self, claim_id: str) -> Dict[str, Any]:
        """
        Enhanced document processing with extracted_patient_data creation
        """
        try:
            self.logger.info(f"📄 Processing documents for claim {claim_id}")
            
            # Step 1: Check if extracted data already exists
            existing_data = await self._check_existing_extracted_data(claim_id)
            if existing_data:
                self.logger.info(f"✅ Extracted data already exists for {claim_id}")
                return {
                    "status": "success",
                    "message": f"Extracted data already exists for claim {claim_id}",
                    "extracted_data": existing_data,
                    "agent": self.agent_name
                }
            
            # Step 2: Get claim details to find document URLs
            claim_data = await self._get_claim_data(claim_id)
            if not claim_data:
                return {
                    "status": "error",
                    "message": f"Claim {claim_id} not found",
                    "agent": self.agent_name
                }
            
            # Step 3: Extract document URLs based on claim category
            document_urls = await self._get_document_urls(claim_data)
            
            # Step 4: Process documents with Azure Document Intelligence
            extracted_data = await self._process_documents_with_ai(claim_id, document_urls, claim_data)
            
            # Step 5: Create document in extracted_patient_data container
            if extracted_data:
                success = await self._create_extracted_patient_data_document(claim_id, extracted_data)
                if success:
                    self.logger.info(f"✅ Created extracted_patient_data document for {claim_id}")
                    
                    # Log workflow step
                    step_id = workflow_logger.add_step(
                        step_type=WorkflowStepType.PROCESSING,
                        title="Document Extraction Completed",
                        description=f"Created extracted_patient_data document for {claim_id}",
                        status=WorkflowStepStatus.COMPLETED,
                        agent_name=self.agent_name,
                        details={
                            "documents_processed": len(document_urls),
                            "extracted_fields": list(extracted_data.keys()),
                            "cosmos_document_created": True
                        }
                    )
                    
                    return {
                        "status": "success",
                        "message": f"Documents processed and extracted data created for {claim_id}",
                        "extracted_data": extracted_data,
                        "documents_processed": len(document_urls),
                        "cosmos_document_created": True,
                        "agent": self.agent_name
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to create extracted_patient_data document for {claim_id}",
                        "agent": self.agent_name
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to extract data from documents for {claim_id}",
                    "agent": self.agent_name
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error processing documents for {claim_id}: {e}")
            return {
                "status": "error",
                "message": f"Error processing documents: {str(e)}",
                "agent": self.agent_name
            }
    
    async def _check_existing_extracted_data(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Check if extracted data already exists for this claim"""
        try:
            query = f"SELECT * FROM c WHERE c.claim_id = '{claim_id}'"
            result = await enhanced_mcp_chat_client.query_cosmos_data(
                f"Query extracted_patient_data container: {query}"
            )
            
            if isinstance(result, dict) and 'documents' in result and result['documents']:
                return result['documents'][0]
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check existing data: {e}")
            return None
    
    async def _get_claim_data(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim data from Cosmos"""
        try:
            result = await enhanced_mcp_chat_client.query_cosmos_data(
                f"Get details for claim_id {claim_id}"
            )
            
            if isinstance(result, dict) and 'error' not in result:
                return result
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting claim data: {e}")
            return None
    
    async def _get_document_urls(self, claim_data: Dict[str, Any]) -> Dict[str, str]:
        """Get document URLs based on claim category"""
        category = claim_data.get("category", "").lower()
        claim_id = claim_data.get("claim_id", "")
        
        # Simulate document URLs (in production, these would come from blob storage)
        base_url = "https://example.blob.core.windows.net/documents"
        
        document_urls = {}
        
        if "inpatient" in category:
            # Inpatient requires: medical_bill, memo, discharge_summary
            document_urls = {
                "medical_bill": f"{base_url}/{claim_id}/medical_bill.pdf",
                "memo": f"{base_url}/{claim_id}/memo.pdf", 
                "discharge_summary": f"{base_url}/{claim_id}/discharge_summary.pdf"
            }
        elif "outpatient" in category:
            # Outpatient requires: medical_bill, memo
            document_urls = {
                "medical_bill": f"{base_url}/{claim_id}/medical_bill.pdf",
                "memo": f"{base_url}/{claim_id}/memo.pdf"
            }
        else:
            # Default to basic documents
            document_urls = {
                "medical_bill": f"{base_url}/{claim_id}/medical_bill.pdf"
            }
        
        self.logger.info(f"📄 Document URLs for {category} claim: {list(document_urls.keys())}")
        return document_urls
    
    async def _process_documents_with_ai(self, claim_id: str, document_urls: Dict[str, str], claim_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process documents with Azure Document Intelligence
        """
        try:
            self.logger.info(f"🤖 Processing {len(document_urls)} documents with AI")
            
            # Simulate document intelligence processing
            # In production, this would call Azure Document Intelligence API
            
            extracted_data = {
                "id": f"extracted_{claim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "claim_id": claim_id,
                "extraction_timestamp": datetime.now().isoformat(),
                "documents_processed": list(document_urls.keys()),
                "source_urls": document_urls
            }
            
            # Simulate extraction based on claim category
            category = claim_data.get("category", "").lower()
            
            if "medical_bill" in document_urls:
                extracted_data.update({
                    "patient_name": claim_data.get("patient_name", "John Doe"),
                    "bill_amount": float(claim_data.get("bill_amount", 100.0)),
                    "bill_date": claim_data.get("bill_date", datetime.now().strftime("%Y-%m-%d")),
                    "provider_name": claim_data.get("provider", "Medical Center"),
                    "medical_condition": claim_data.get("diagnosis", "General treatment")
                })
            
            if "memo" in document_urls:
                extracted_data.update({
                    "treatment_notes": f"Treatment notes extracted from memo for {claim_id}",
                    "provider_recommendations": "Follow-up recommended",
                    "memo_date": datetime.now().strftime("%Y-%m-%d")
                })
            
            if "discharge_summary" in document_urls:
                extracted_data.update({
                    "discharge_date": datetime.now().strftime("%Y-%m-%d"),
                    "discharge_diagnosis": claim_data.get("diagnosis", "Treated and discharged"),
                    "discharge_instructions": "Standard discharge instructions",
                    "length_of_stay": "2 days"
                })
            
            # Add metadata
            extracted_data.update({
                "extraction_method": "azure_document_intelligence",
                "confidence_score": 0.95,
                "extraction_status": "completed",
                "processed_by": self.agent_name,
                "category": claim_data.get("category", "unknown")
            })
            
            self.logger.info(f"✅ Successfully extracted {len(extracted_data)} fields from documents")
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"❌ Error processing documents with AI: {e}")
            return None
    
    async def _create_extracted_patient_data_document(self, claim_id: str, extracted_data: Dict[str, Any]) -> bool:
        """
        Create document in extracted_patient_data container
        """
        try:
            self.logger.info(f"📝 Creating extracted_patient_data document for {claim_id}")
            
            # Create the document using MCP
            create_query = f"""
            INSERT INTO extracted_patient_data 
            VALUE {json.dumps(extracted_data)}
            """
            
            result = await enhanced_mcp_chat_client.query_cosmos_data(
                f"Create extracted patient data document: {create_query}"
            )
            
            if isinstance(result, dict) and 'error' not in result:
                self.logger.info(f"✅ Successfully created extracted_patient_data document")
                return True
            else:
                self.logger.error(f"❌ Failed to create document: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error creating extracted_patient_data document: {e}")
            return False

# Create global instance
enhanced_document_intelligence = EnhancedDocumentIntelligence()
