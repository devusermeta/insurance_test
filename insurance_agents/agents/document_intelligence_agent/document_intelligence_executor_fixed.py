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
            
            # Process the document intelligence task
            result = await self._process_document_intelligence_task(task_text)
            
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
        """Process document intelligence task based on the request text"""
        
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

# Create the fixed executor instance
DocumentIntelligenceExecutor = DocumentIntelligenceExecutorFixed

print("📄 FIXED Document Intelligence Executor loaded successfully!")
print("✅ A2A compatible version with correct parameter handling")
