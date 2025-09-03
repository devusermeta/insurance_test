"""
Document Intelligence Executor
Implements the agent execution logic for Document Intelligence
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
import base64

from shared.mcp_config import A2A_AGENT_PORTS

class DocumentIntelligenceExecutor:
    """
    Executor for Document Intelligence Agent
    Implements the business logic for document analysis and intelligence extraction
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
            f"📄 [{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
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
        Execute a request using the Document Intelligence logic
        This is the main entry point for A2A requests
        """
        try:
            self.logger.info(f"🔄 Executing request: {request.get('task', 'unknown')}")
            
            # Extract task and parameters
            task = request.get('task', '')
            parameters = request.get('parameters', {})
            
            # Route to appropriate handler
            if 'analyze' in task.lower() or 'document' in task.lower():
                return await self._handle_document_analysis(parameters)
            elif 'extract' in task.lower() or 'text' in task.lower():
                return await self._handle_text_extraction(parameters)
            elif 'damage' in task.lower() or 'assess' in task.lower():
                return await self._handle_damage_assessment(parameters)
            elif 'form' in task.lower() or 'recognize' in task.lower():
                return await self._handle_form_recognition(parameters)
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
    
    async def _handle_document_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive document analysis requests"""
        self.logger.info("📄 Performing document analysis")
        
        # Extract parameters
        documents = parameters.get('documents', [])
        analysis_type = parameters.get('analysis_type', 'full_analysis')
        claim_id = parameters.get('claim_id', f"DOC_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not documents:
            return {
                "status": "error",
                "error": "No documents provided for analysis",
                "agent": self.agent_name
            }
        
        # Perform analysis on each document
        analysis_results = []
        for doc in documents:
            doc_result = await self._analyze_single_document(doc, analysis_type)
            analysis_results.append(doc_result)
        
        # Aggregate results
        overall_analysis = await self._aggregate_document_analysis(analysis_results)
        
        return {
            "status": "success",
            "claim_id": claim_id,
            "analysis_type": analysis_type,
            "document_count": len(documents),
            "individual_results": analysis_results,
            "overall_analysis": overall_analysis,
            "agent": self.agent_name
        }
    
    async def _handle_text_extraction(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text extraction from documents"""
        self.logger.info("📝 Performing text extraction")
        
        document_path = parameters.get('document_path', '')
        extraction_mode = parameters.get('extraction_mode', 'hybrid')
        
        if not document_path:
            return {
                "status": "error",
                "error": "No document path provided",
                "agent": self.agent_name
            }
        
        # Perform text extraction
        extraction_result = await self._extract_text_from_document(document_path, extraction_mode)
        
        return {
            "status": "success",
            "document_path": document_path,
            "extraction_mode": extraction_mode,
            "extraction_result": extraction_result,
            "agent": self.agent_name
        }
    
    async def _handle_damage_assessment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle damage assessment from images"""
        self.logger.info("🔍 Performing damage assessment")
        
        images = parameters.get('images', [])
        assessment_criteria = parameters.get('assessment_criteria', {})
        
        if not images:
            return {
                "status": "error",
                "error": "No images provided for damage assessment",
                "agent": self.agent_name
            }
        
        # Perform damage assessment
        damage_assessment = await self._assess_damage_from_images(images, assessment_criteria)
        
        return {
            "status": "success",
            "image_count": len(images),
            "damage_assessment": damage_assessment,
            "agent": self.agent_name
        }
    
    async def _handle_form_recognition(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle form recognition and data extraction"""
        self.logger.info("📋 Performing form recognition")
        
        form_type = parameters.get('form_type', 'claim_form')
        document = parameters.get('document', '')
        
        if not document:
            return {
                "status": "error",
                "error": "No document provided for form recognition",
                "agent": self.agent_name
            }
        
        # Perform form recognition
        form_data = await self._recognize_form_data(document, form_type)
        
        return {
            "status": "success",
            "form_type": form_type,
            "form_data": form_data,
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
                "Document text extraction (OCR/NLP)",
                "Form recognition and data extraction",
                "Damage assessment from images",
                "Multi-format document support",
                "Structured data extraction"
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
                "OCR and text extraction",
                "Form recognition",
                "Damage assessment",
                "Data structure extraction",
                "Multi-language support"
            ]
        }
    
    async def _analyze_single_document(self, document: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Analyze a single document"""
        file_path = document.get('file_path', '')
        document_type = document.get('document_type', 'unknown')
        metadata = document.get('metadata', {})
        
        self.logger.info(f"📄 Analyzing document: {file_path} (type: {document_type})")
        
        # Mock document analysis
        analysis_result = {
            "file_path": file_path,
            "document_type": document_type,
            "analysis_type": analysis_type,
            "confidence_score": 85,
            "processing_time": 2.3,
            "extracted_data": {},
            "issues": []
        }
        
        # Simulate different analysis types
        if analysis_type in ['text_extraction', 'full_analysis']:
            analysis_result["extracted_data"]["text_content"] = await self._mock_text_extraction(file_path)
        
        if analysis_type in ['form_recognition', 'full_analysis']:
            analysis_result["extracted_data"]["form_fields"] = await self._mock_form_recognition(document_type)
        
        if analysis_type in ['damage_assessment', 'full_analysis'] and 'image' in document_type.lower():
            analysis_result["extracted_data"]["damage_info"] = await self._mock_damage_assessment()
        
        # Check for issues
        if not file_path:
            analysis_result["issues"].append("No file path provided")
            analysis_result["confidence_score"] = 0
        
        return analysis_result
    
    async def _extract_text_from_document(self, document_path: str, extraction_mode: str) -> Dict[str, Any]:
        """Extract text from a document using specified mode"""
        self.logger.info(f"📝 Extracting text from {document_path} using {extraction_mode}")
        
        # Mock text extraction
        extraction_result = {
            "document_path": document_path,
            "extraction_mode": extraction_mode,
            "confidence_score": 92,
            "word_count": 1247,
            "language": "en",
            "extracted_text": await self._mock_extracted_text(),
            "structured_data": await self._mock_structured_extraction(),
            "processing_time": 1.8
        }
        
        return extraction_result
    
    async def _assess_damage_from_images(self, images: List[str], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Assess damage from provided images"""
        self.logger.info(f"🔍 Assessing damage from {len(images)} images")
        
        # Mock damage assessment
        damage_results = []
        total_damage_score = 0
        
        for i, image_path in enumerate(images):
            damage_score = 65 + (i * 5)  # Mock varying damage scores
            damage_info = {
                "image_path": image_path,
                "damage_score": damage_score,
                "damage_type": ["impact", "water"][i % 2],
                "affected_areas": ["front_bumper", "hood", "windshield"][i % 3],
                "repair_estimate": damage_score * 100,
                "severity": "moderate" if damage_score < 75 else "severe"
            }
            damage_results.append(damage_info)
            total_damage_score += damage_score
        
        average_damage = total_damage_score / len(images) if images else 0
        
        return {
            "total_images": len(images),
            "average_damage_score": round(average_damage, 2),
            "overall_severity": "severe" if average_damage > 75 else "moderate" if average_damage > 50 else "minor",
            "estimated_total_cost": sum(d["repair_estimate"] for d in damage_results),
            "individual_assessments": damage_results,
            "assessment_criteria": criteria
        }
    
    async def _recognize_form_data(self, document: str, form_type: str) -> Dict[str, Any]:
        """Recognize and extract data from insurance forms"""
        self.logger.info(f"📋 Recognizing {form_type} data")
        
        # Mock form recognition based on type
        form_data = {
            "form_type": form_type,
            "recognition_confidence": 88,
            "fields_detected": 0,
            "extracted_fields": {}
        }
        
        if form_type == "claim_form":
            form_data["extracted_fields"] = {
                "claim_number": "CLM-2024-001234",
                "policy_number": "POL-789456123",
                "incident_date": "2024-01-15",
                "claimant_name": "John Smith",
                "incident_description": "Vehicle collision on Main Street",
                "damage_amount": "$5,500"
            }
            form_data["fields_detected"] = 6
        elif form_type == "policy_document":
            form_data["extracted_fields"] = {
                "policy_number": "POL-789456123",
                "policyholder": "John Smith",
                "coverage_amount": "$50,000",
                "deductible": "$1,000",
                "effective_date": "2024-01-01",
                "expiration_date": "2024-12-31"
            }
            form_data["fields_detected"] = 6
        
        return form_data
    
    async def _aggregate_document_analysis(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple document analyses"""
        if not analysis_results:
            return {"status": "no_documents"}
        
        # Calculate overall metrics
        total_confidence = sum(result.get('confidence_score', 0) for result in analysis_results)
        average_confidence = total_confidence / len(analysis_results)
        
        total_issues = sum(len(result.get('issues', [])) for result in analysis_results)
        
        # Aggregate extracted data
        all_text = []
        all_forms = []
        all_damage = []
        
        for result in analysis_results:
            extracted_data = result.get('extracted_data', {})
            if 'text_content' in extracted_data:
                all_text.append(extracted_data['text_content'])
            if 'form_fields' in extracted_data:
                all_forms.append(extracted_data['form_fields'])
            if 'damage_info' in extracted_data:
                all_damage.append(extracted_data['damage_info'])
        
        return {
            "documents_processed": len(analysis_results),
            "average_confidence": round(average_confidence, 2),
            "total_issues": total_issues,
            "summary": {
                "text_documents": len(all_text),
                "form_documents": len(all_forms),
                "damage_assessments": len(all_damage)
            },
            "overall_status": "complete" if total_issues == 0 else "issues_detected"
        }
    
    async def _mock_text_extraction(self, file_path: str) -> str:
        """Mock text extraction result"""
        return f"This is extracted text content from {file_path}. The document contains insurance claim information including policy details, incident description, and supporting documentation."
    
    async def _mock_extracted_text(self) -> str:
        """Mock comprehensive extracted text"""
        return """Insurance Claim Form - Auto Accident
        Policy Number: POL-789456123
        Claim Number: CLM-2024-001234
        Date of Incident: January 15, 2024
        Location: Main Street & Oak Avenue
        Description: Vehicle collision resulting in front-end damage
        Estimated Damage: $5,500
        Claimant: John Smith
        Contact: (555) 123-4567"""
    
    async def _mock_structured_extraction(self) -> Dict[str, Any]:
        """Mock structured data extraction"""
        return {
            "entities": [
                {"type": "policy_number", "value": "POL-789456123", "confidence": 0.95},
                {"type": "claim_number", "value": "CLM-2024-001234", "confidence": 0.98},
                {"type": "date", "value": "2024-01-15", "confidence": 0.92},
                {"type": "amount", "value": "$5,500", "confidence": 0.89}
            ],
            "key_phrases": ["auto accident", "front-end damage", "Main Street collision"],
            "sentiment": "neutral"
        }
    
    async def _mock_form_recognition(self, document_type: str) -> Dict[str, Any]:
        """Mock form recognition result"""
        return {
            "form_type": document_type,
            "fields_found": 8,
            "key_value_pairs": {
                "policy_number": "POL-789456123",
                "claim_date": "2024-01-15",
                "claimant": "John Smith"
            }
        }
    
    async def _mock_damage_assessment(self) -> Dict[str, Any]:
        """Mock damage assessment result"""
        return {
            "damage_score": 72,
            "affected_areas": ["front_bumper", "hood"],
            "severity": "moderate",
            "repair_estimate": "$5,500"
        }
