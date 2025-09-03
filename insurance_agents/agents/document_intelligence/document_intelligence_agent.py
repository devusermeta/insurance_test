"""
Document Intelligence Agent
Specialized agent for analyzing and extracting information from claim documents
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from shared.base_agent import BaseInsuranceAgent
from shared.mcp_config import A2A_AGENT_PORTS

class DocumentAnalysisRequest(BaseModel):
    """Pydantic model for document analysis requests"""
    claim_id: str
    documents: List[str]
    analysis_type: str = "comprehensive"

class DocumentIntelligenceAgent(BaseInsuranceAgent):
    """
    Document Intelligence Agent - Analyzes and extracts information from claim documents
    
    Responsibilities:
    - Extract structured data from unstructured documents
    - Identify document types and classify content
    - Perform OCR and text extraction
    - Validate document authenticity and completeness
    - Extract key entities (dates, amounts, locations, people)
    - Generate document summaries and insights
    """
    
    def __init__(self):
        super().__init__(
            agent_name="document_intelligence",
            agent_description="Analyzes and extracts information from claim documents",
            port=A2A_AGENT_PORTS["document_intelligence"]
        )
        self.app = FastAPI(title="Document Intelligence Agent", version="1.0.0")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes for the agent"""
        
        @self.app.post("/api/analyze_documents")
        async def analyze_documents(request: DocumentAnalysisRequest):
            """Main endpoint to analyze claim documents"""
            try:
                self.logger.info(f"📄 Starting document analysis for claim: {request.claim_id}")
                
                # Perform document analysis
                analysis_result = await self._analyze_documents(request)
                
                # Log the analysis event
                await self.log_event(
                    "documents_analyzed",
                    f"Completed analysis for {len(request.documents)} documents in claim {request.claim_id}",
                    {
                        "claim_id": request.claim_id,
                        "document_count": len(request.documents),
                        "analysis_type": request.analysis_type,
                        "confidence_score": analysis_result.get("confidence_score")
                    }
                )
                
                return {
                    "status": "success",
                    "claim_id": request.claim_id,
                    "analysis_result": analysis_result,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error analyzing documents: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get agent status"""
            return self.get_status()
        
        @self.app.post("/api/message")
        async def receive_message(message: Dict[str, Any]):
            """Receive A2A messages from other agents"""
            message_type = message.get("type")
            
            if message_type == "analyze_documents":
                claim_id = message.get("claim_id")
                documents = message.get("documents", [])
                analysis_type = message.get("analysis_type", "comprehensive")
                
                request = DocumentAnalysisRequest(
                    claim_id=claim_id,
                    documents=documents,
                    analysis_type=analysis_type
                )
                
                return await self._analyze_documents(request)
            else:
                return await self.process_request(message)
        
        @self.app.post("/api/extract_entities")
        async def extract_entities(request: Dict[str, Any]):
            """Extract entities from document text"""
            try:
                text = request.get("text", "")
                self.logger.info(f"🔍 Extracting entities from text ({len(text)} characters)")
                
                entities = await self._extract_entities(text)
                
                return {
                    "status": "success",
                    "entities": entities,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error extracting entities: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _analyze_documents(self, request: DocumentAnalysisRequest) -> Dict[str, Any]:
        """Perform comprehensive document analysis"""
        claim_id = request.claim_id
        documents = request.documents
        
        self.logger.info(f"📋 Analyzing {len(documents)} documents for claim {claim_id}")
        
        analysis_result = {
            "claim_id": claim_id,
            "total_documents": len(documents),
            "analysis_type": request.analysis_type,
            "document_analyses": [],
            "extracted_data": {},
            "confidence_score": 0,
            "fraud_indicators": [],
            "completeness_assessment": {},
            "summary": ""
        }
        
        try:
            total_confidence = 0
            
            # Analyze each document
            for i, document in enumerate(documents):
                self.logger.info(f"📄 Analyzing document {i+1}/{len(documents)}: {document}")
                
                doc_analysis = await self._analyze_single_document(document, claim_id)
                analysis_result["document_analyses"].append(doc_analysis)
                
                total_confidence += doc_analysis.get("confidence_score", 0)
            
            # Calculate overall confidence
            if documents:
                analysis_result["confidence_score"] = int(total_confidence / len(documents))
            
            # Extract key information across all documents
            analysis_result["extracted_data"] = await self._extract_key_information(
                analysis_result["document_analyses"]
            )
            
            # Assess fraud indicators
            analysis_result["fraud_indicators"] = await self._assess_fraud_indicators(
                analysis_result["document_analyses"]
            )
            
            # Assess document completeness
            analysis_result["completeness_assessment"] = await self._assess_completeness(
                documents, claim_id
            )
            
            # Generate summary
            analysis_result["summary"] = await self._generate_summary(analysis_result)
            
            # Store analysis results
            await self._store_analysis_results(analysis_result)
            
            self.logger.info(f"✅ Document analysis completed for {claim_id}")
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ Document analysis failed: {str(e)}")
            analysis_result["status"] = "error"
            analysis_result["error"] = str(e)
            return analysis_result
    
    async def _analyze_single_document(self, document: str, claim_id: str) -> Dict[str, Any]:
        """Analyze a single document"""
        doc_analysis = {
            "document_name": document,
            "document_type": "unknown",
            "confidence_score": 85,
            "extracted_text": "",
            "entities": {},
            "metadata": {},
            "issues": []
        }
        
        # Determine document type based on filename
        doc_lower = document.lower()
        if any(keyword in doc_lower for keyword in ["police", "report", "incident"]):
            doc_analysis["document_type"] = "police_report"
            doc_analysis["confidence_score"] = 90
        elif any(keyword in doc_lower for keyword in ["photo", "image", "jpg", "png"]):
            doc_analysis["document_type"] = "photo_evidence"
            doc_analysis["confidence_score"] = 80
        elif any(keyword in doc_lower for keyword in ["receipt", "invoice", "bill"]):
            doc_analysis["document_type"] = "financial_document"
            doc_analysis["confidence_score"] = 95
        elif any(keyword in doc_lower for keyword in ["medical", "doctor", "hospital"]):
            doc_analysis["document_type"] = "medical_document"
            doc_analysis["confidence_score"] = 88
        
        # Mock text extraction
        doc_analysis["extracted_text"] = f"Extracted text from {document} for claim {claim_id}"
        
        # Extract entities
        doc_analysis["entities"] = await self._extract_entities(doc_analysis["extracted_text"])
        
        # Document metadata
        doc_analysis["metadata"] = {
            "file_size": "2.5MB",  # Mock
            "creation_date": datetime.now().isoformat(),
            "format": document.split('.')[-1] if '.' in document else "unknown"
        }
        
        return doc_analysis
    
    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        # Mock entity extraction - in real implementation, use NLP libraries
        entities = {
            "dates": [],
            "amounts": [],
            "locations": [],
            "people": [],
            "organizations": [],
            "vehicle_info": []
        }
        
        # Simple pattern matching for demo
        import re
        
        # Extract dates (simple patterns)
        date_patterns = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b'
        entities["dates"] = re.findall(date_patterns, text)
        
        # Extract amounts
        amount_patterns = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        entities["amounts"] = re.findall(amount_patterns, text)
        
        # Mock other entities
        if "police" in text.lower():
            entities["organizations"].append("Police Department")
        
        if "hospital" in text.lower():
            entities["organizations"].append("Hospital")
        
        return entities
    
    async def _extract_key_information(self, document_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract key information across all documents"""
        key_info = {
            "incident_date": None,
            "total_damage_amount": 0,
            "involved_parties": [],
            "location": None,
            "police_report_number": None,
            "medical_providers": [],
            "key_facts": []
        }
        
        # Aggregate information from all documents
        all_dates = []
        all_amounts = []
        all_organizations = []
        
        for doc in document_analyses:
            entities = doc.get("entities", {})
            
            all_dates.extend(entities.get("dates", []))
            all_amounts.extend(entities.get("amounts", []))
            all_organizations.extend(entities.get("organizations", []))
        
        # Set most likely incident date (first date found)
        if all_dates:
            key_info["incident_date"] = all_dates[0]
        
        # Calculate total damage (sum of all amounts)
        for amount_str in all_amounts:
            try:
                amount = float(amount_str.replace('$', '').replace(',', ''))
                key_info["total_damage_amount"] += amount
            except:
                pass
        
        key_info["involved_parties"] = list(set(all_organizations))
        
        return key_info
    
    async def _assess_fraud_indicators(self, document_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess potential fraud indicators in documents"""
        fraud_indicators = []
        
        # Check for suspicious patterns
        for doc in document_analyses:
            doc_type = doc.get("document_type")
            confidence = doc.get("confidence_score", 0)
            
            # Low confidence scores might indicate tampered documents
            if confidence < 70:
                fraud_indicators.append({
                    "type": "low_confidence_document",
                    "document": doc.get("document_name"),
                    "severity": "medium",
                    "score": confidence,
                    "description": f"Document confidence score is low ({confidence}%)"
                })
            
            # Missing expected document types
            if doc_type == "unknown":
                fraud_indicators.append({
                    "type": "unidentified_document",
                    "document": doc.get("document_name"),
                    "severity": "low",
                    "description": "Document type could not be determined"
                })
        
        # Check for missing critical documents
        doc_types = [doc.get("document_type") for doc in document_analyses]
        
        if "police_report" not in doc_types and len(document_analyses) > 0:
            fraud_indicators.append({
                "type": "missing_police_report",
                "severity": "high",
                "description": "No police report found for incident claim"
            })
        
        return fraud_indicators
    
    async def _assess_completeness(self, documents: List[str], claim_id: str) -> Dict[str, Any]:
        """Assess document completeness for the claim"""
        completeness = {
            "score": 0,
            "required_documents": [],
            "missing_documents": [],
            "recommendations": []
        }
        
        # Define required documents based on claim type (mock logic)
        required_docs = [
            "police_report",
            "photo_evidence", 
            "financial_document"
        ]
        
        provided_types = []
        for doc in documents:
            doc_lower = doc.lower()
            if "police" in doc_lower:
                provided_types.append("police_report")
            elif "photo" in doc_lower or "image" in doc_lower:
                provided_types.append("photo_evidence")
            elif "receipt" in doc_lower or "invoice" in doc_lower:
                provided_types.append("financial_document")
        
        completeness["required_documents"] = required_docs
        completeness["missing_documents"] = [
            doc for doc in required_docs if doc not in provided_types
        ]
        
        # Calculate completeness score
        if required_docs:
            completeness["score"] = int((len(provided_types) / len(required_docs)) * 100)
        
        # Generate recommendations
        for missing in completeness["missing_documents"]:
            if missing == "police_report":
                completeness["recommendations"].append("Please provide police incident report")
            elif missing == "photo_evidence":
                completeness["recommendations"].append("Please provide photos of damage")
            elif missing == "financial_document":
                completeness["recommendations"].append("Please provide repair estimates or receipts")
        
        return completeness
    
    async def _generate_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a summary of the document analysis"""
        total_docs = analysis_result["total_documents"]
        confidence = analysis_result["confidence_score"]
        fraud_count = len(analysis_result["fraud_indicators"])
        completeness = analysis_result["completeness_assessment"].get("score", 0)
        
        summary = f"Analyzed {total_docs} documents with {confidence}% average confidence. "
        
        if fraud_count > 0:
            summary += f"Found {fraud_count} potential fraud indicators. "
        else:
            summary += "No fraud indicators detected. "
        
        summary += f"Document completeness: {completeness}%. "
        
        if completeness < 70:
            summary += "Additional documents recommended."
        else:
            summary += "Document set appears complete."
        
        return summary
    
    async def _store_analysis_results(self, analysis_result: Dict[str, Any]):
        """Store document analysis results in Cosmos DB"""
        artifact_data = {
            "id": f"doc_analysis_{analysis_result['claim_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "claim_id": analysis_result["claim_id"],
            "artifact_type": "document_analysis",
            "content": analysis_result,
            "created_by": self.agent_name,
            "created_at": datetime.now().isoformat()
        }
        
        await self.query_cosmos_via_mcp("artifacts", {"insert": artifact_data})

# FastAPI app instance
agent = DocumentIntelligenceAgent()
app = agent.app

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    await agent.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await agent.shutdown()

if __name__ == "__main__":
    # Run the agent server
    uvicorn.run(
        "document_intelligence_agent:app",
        host="0.0.0.0",
        port=A2A_AGENT_PORTS["document_intelligence"],
        reload=True,
        log_level="info"
    )
