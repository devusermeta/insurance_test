"""
FIXED Document Intelligence Executor - A2A Compatible
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

class DocumentIntelligenceExecutorFixed(AgentExecutor):
    """
    FIXED Document Intelligence Executor - A2A Compatible
    Simplified version that works correctly with A2A framework
    """
    
    def __init__(self):
        self.agent_name = "document_intelligence"
        self.agent_description = "Analyzes documents and extracts intelligence for insurance claims"
        self.port = A2A_AGENT_PORTS["document_intelligence"]
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        # Create colored formatter
        formatter = logging.Formatter(
            f"📄 [DOCUMENT_INTELLIGENCE_FIXED] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Setup console handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute a request using the Document Intelligence logic with A2A framework
        FIXED VERSION - Works with correct A2A parameters
        """
        try:
            # Try the intake clarifier approach first
            user_input = context.get_user_input()
            print(f"\n🔍 DOCUMENT EXECUTE - User input method: '{user_input[:200] if user_input else None}...'")
            print(f"🔍 DOCUMENT EXECUTE - User input length: {len(user_input) if user_input else 0}")
            
            # Extract message from context (old method)
            message = context.message
            task_text = ""
            
            # Extract text from message parts
            if hasattr(message, 'parts') and message.parts:
                for part in message.parts:
                    if hasattr(part, 'text'):
                        task_text += part.text + " "
            
            task_text = task_text.strip()
            
            # Use the working method
            final_task_text = user_input if user_input else task_text
            print(f"🔍 DOCUMENT EXECUTE - Using final text: '{final_task_text[:200]}...'")
            
            self.logger.info(f"🔄 A2A Executing task: {final_task_text[:100]}...")
            
            # Process the document intelligence task
            result = await self._process_document_intelligence_task(final_task_text)
            
            # Create and send response message
            response_message = new_agent_text_message(
                text=result.get("response", "Document analysis completed successfully"),
                task_id=getattr(context, 'task_id', None)
            )
            await event_queue.enqueue_event(response_message)
            
            self.logger.info("✅ Document Intelligence task completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Execution error: {str(e)}")
            
            # Send error message
            error_message = new_agent_text_message(
                text=f"Document Intelligence error: {str(e)}",
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
    
    async def _process_document_intelligence_task(self, task_text: str) -> Dict[str, Any]:
        """Process document intelligence task with new workflow support"""
        
        print(f"\n🔍 DOCUMENT TASK - Processing task: '{task_text[:100]}...'")
        
        # Check if this is a new workflow request with claim details
        if self._is_new_workflow_claim_request(task_text):
            print("🔍 DOCUMENT TASK - Using NEW WORKFLOW path")
            return await self._handle_new_workflow_document_processing(task_text)
        
        print("🔍 DOCUMENT TASK - Using LEGACY path")
        task_lower = task_text.lower()
        
        # Simulate document analysis
        self.logger.info("📄 Analyzing document content...")
        await asyncio.sleep(0.1)  # Simulate processing time
        
        result = {
            "agent": "document_intelligence",
            "task": task_text,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "document_type": "medical_record",
                "confidence": 0.95,
                "extracted_data": {
                    "patient_info": "Successfully extracted",
                    "diagnosis_codes": ["M79.3", "Z51.11"],
                    "procedures": ["Office visit", "Consultation"],
                    "provider_info": "Verified"
                }
            }
        }
        
        if 'analyze' in task_lower or 'document' in task_lower:
            result["analysis"]["focus"] = "Document structure analysis"
        elif 'extract' in task_lower or 'text' in task_lower:
            result["analysis"]["focus"] = "Text extraction and processing"
        elif 'damage' in task_lower or 'assess' in task_lower:
            result["analysis"]["focus"] = "Damage assessment analysis"
        else:
            result["analysis"]["focus"] = "General document intelligence"
        
        result["response"] = json.dumps({
            "status": "success", 
            "message": f"Document intelligence completed: {result['analysis']['focus']}",
            "extracted_codes": result["analysis"]["extracted_data"]["diagnosis_codes"],
            "confidence": result["analysis"]["confidence"]
        }, indent=2)
        
        self.logger.info(f"📊 Analysis complete - Confidence: {result['analysis']['confidence']}")
        
        return result

    def _is_new_workflow_claim_request(self, task_text: str) -> bool:
        """Check if this is a new workflow claim document processing request"""
        # DEBUG: Print to console for immediate visibility
        print(f"\n🔍 DOCUMENT DEBUG - Received text: '{task_text[:200]}...'")
        
        indicators = [
            "claim_id" in task_text.lower(),
            "document processing" in task_text.lower(),
            "patient_name" in task_text.lower(),
            "category" in task_text.lower()
        ]
        
        indicator_count = sum(indicators)
        print(f"🔍 DOCUMENT DEBUG - Found {indicator_count}/4 indicators: {dict(zip(['claim_id', 'document processing', 'patient_name', 'category'], indicators))}")
        
        is_new_workflow = indicator_count >= 2
        print(f"🔍 DOCUMENT DEBUG - New workflow detected: {is_new_workflow}")
        
        return is_new_workflow

    async def _handle_new_workflow_document_processing(self, task_text: str) -> Dict[str, Any]:
        """Handle document processing for new workflow with structured claim data"""
        try:
            self.logger.info("🆕 Processing NEW WORKFLOW document analysis")
            
            # Extract claim information
            claim_info = self._extract_claim_info_from_text(task_text)
            
            # Perform enhanced document processing
            processing_result = await self._process_structured_claim_documents(claim_info)
            
            response_message = f"""📄 **DOCUMENT INTELLIGENCE ANALYSIS COMPLETE**

**Claim Analysis:**
• **Claim ID**: {claim_info.get('claim_id', 'Unknown')}
• **Patient**: {claim_info.get('patient_name', 'Unknown')}
• **Category**: {claim_info.get('category', 'Unknown')}

**Document Processing Results:**
• **Documents Found**: {processing_result['documents_found']}
• **Processing Status**: {'✅ SUCCESS' if processing_result['processing_success'] else '❌ ISSUES DETECTED'}
• **Confidence Score**: {processing_result['confidence_score']}/100

**Extracted Information:**
{chr(10).join(['• ' + item for item in processing_result['extracted_items']])}

**Validation Results:**
{chr(10).join(['• ' + validation for validation in processing_result['validations']])}

**Recommendations:**
{chr(10).join(['• ' + rec for rec in processing_result['recommendations']])}
"""

            return {
                "status": "success",
                "response": response_message,
                "processing_result": processing_result,
                "workflow_type": "new_structured"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in new workflow document processing: {e}")
            return {
                "status": "error",
                "response": f"Document processing failed: {str(e)}"
            }

    def _extract_claim_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured claim information from task text"""
        import re
        
        claim_info = {}
        patterns = {
            'claim_id': r'claim[_\s]*id[:\s]+([A-Z]{2}-\d{2,3})',
            'patient_name': r'patient[_\s]*name[:\s]+([^,\n]+)',
            'category': r'category[:\s]+([^,\n]+)',
            'diagnosis': r'diagnosis[:\s]+([^,\n]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                claim_info[key] = match.group(1).strip()
        
        return claim_info

    async def _process_structured_claim_documents(self, claim_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process documents for structured claim with enhanced analysis"""
        category = claim_info.get('category', '').lower()
        claim_id = claim_info.get('claim_id', 'Unknown')
        
        # Simulate document processing based on category
        await asyncio.sleep(0.2)  # Simulate processing time
        
        if 'outpatient' in category:
            documents_found = 3
            extracted_items = [
                "Medical bill with itemized charges",
                "Provider diagnosis codes (ICD-10)",
                "Treatment summary and notes",
                "Patient identification verified"
            ]
            validations = [
                "✅ Provider credentials verified", 
                "✅ Service dates match claim period",
                "⚠️  Missing pre-authorization documentation"
            ]
            recommendations = [
                "Request pre-authorization documents",
                "Verify CPT codes with provider",
                "Proceed with standard outpatient processing"
            ]
            confidence = 85
        elif 'inpatient' in category:
            documents_found = 5
            extracted_items = [
                "Admission and discharge summaries",
                "Itemized hospital bill",
                "Physician notes and treatment plans", 
                "Diagnostic imaging reports",
                "Medication administration records"
            ]
            validations = [
                "✅ Medical necessity documented",
                "✅ Length of stay appropriate",
                "✅ All required signatures present"
            ]
            recommendations = [
                "All documentation complete",
                "Approve for standard inpatient processing",
                "No additional review required"
            ]
            confidence = 95
        else:
            documents_found = 2
            extracted_items = [
                "Basic medical documentation",
                "Provider invoice"
            ]
            validations = [
                "⚠️  Limited documentation available",
                "✅ Basic requirements met"
            ]
            recommendations = [
                "Request additional medical records",
                "Manual review recommended",
                "Proceed with caution"
            ]
            confidence = 70
        
        return {
            "documents_found": documents_found,
            "processing_success": confidence >= 80,
            "confidence_score": confidence,
            "extracted_items": extracted_items,
            "validations": validations,
            "recommendations": recommendations
        }

# Create the fixed executor instance
DocumentIntelligenceExecutor = DocumentIntelligenceExecutorFixed

print("📄 FIXED Document Intelligence Executor loaded successfully!")
print("✅ A2A compatible version with correct parameter handling")
