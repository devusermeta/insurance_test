"""
Azure Document Intelligence Client
Handles document processing for the insurance claims workflow
Extracts structured data from medical bills, discharge summaries, and memos
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TerminalLogger:
    """Enhanced terminal logging for Document Intelligence operations"""
    
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m'
    }
    
    @classmethod
    def log(cls, level: str, component: str, message: str):
        """Log with colors and emojis"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        emoji_map = {
            'INFO': '📋',
            'SUCCESS': '✅', 
            'ERROR': '❌',
            'WARNING': '⚠️',
            'DEBUG': '🔍',
            'PROCESSING': '🔄'
        }
        
        color = {
            'INFO': cls.COLORS['blue'],
            'SUCCESS': cls.COLORS['green'],
            'ERROR': cls.COLORS['red'], 
            'WARNING': cls.COLORS['yellow'],
            'DEBUG': cls.COLORS['magenta'],
            'PROCESSING': cls.COLORS['cyan']
        }.get(level, cls.COLORS['reset'])
        
        emoji = emoji_map.get(level, '📋')
        print(f"{color}{emoji} [{timestamp}] {component}: {message}{cls.COLORS['reset']}")

class AzureDocumentIntelligenceClient:
    """
    Azure Document Intelligence Client for Insurance Claims
    Processes medical documents and extracts structured data
    """
    
    def __init__(self):
        self.logger = TerminalLogger()
        
        # Azure Document Intelligence configuration
        self.endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        self.key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        self.client = None
        self._initialized = False
        
        # Document type configurations for field extraction
        self.document_field_mappings = {
            'discharge_summary': {
                'expected_fields': ['patient_name', 'hospital_name', 'admit_date', 'discharge_date', 'medical_condition'],
                'keywords': ['discharge', 'summary', 'hospital', 'admitted', 'discharged']
            },
            'medical_bill': {
                'expected_fields': ['patient_name', 'bill_date', 'bill_amount'],
                'keywords': ['bill', 'invoice', 'amount', 'total', 'due', 'payment']
            },
            'memo': {
                'expected_fields': ['patient_name', 'medical_condition'],
                'keywords': ['memo', 'note', 'condition', 'diagnosis', 'treatment']
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize Azure Document Intelligence client"""
        try:
            self.logger.log("INFO", "DOC_INTELLIGENCE", "🚀 Initializing Azure Document Intelligence client...")
            
            # Validate environment variables
            if not self.endpoint:
                self.logger.log("ERROR", "DOC_INTELLIGENCE", 
                               "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable not set")
                return False
                
            if not self.key:
                self.logger.log("ERROR", "DOC_INTELLIGENCE", 
                               "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variable not set")
                return False
            
            self.logger.log("INFO", "DOC_INTELLIGENCE", f"Endpoint: {self.endpoint}")
            
            # Initialize Document Intelligence client
            credential = AzureKeyCredential(self.key)
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=credential
            )
            
            self._initialized = True
            self.logger.log("SUCCESS", "DOC_INTELLIGENCE", "✅ Azure Document Intelligence client initialized")
            return True
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", f"Failed to initialize: {str(e)}")
            return False
    
    async def process_document_from_url(self, document_url: str, document_type: str = None) -> Dict[str, Any]:
        """
        Process a document from URL using Azure Document Intelligence
        
        Args:
            document_url: URL to the document (blob storage URL)
            document_type: Type hint for better extraction (discharge_summary, medical_bill, memo)
            
        Returns:
            Extracted structured data
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            self.logger.log("PROCESSING", "DOC_INTELLIGENCE", 
                           f"📄 Processing document: {document_url.split('/')[-1]}")
            
            # Use prebuilt-invoice model for medical bills, prebuilt-read for others
            model_id = "prebuilt-invoice" if document_type == "medical_bill" else "prebuilt-read"
            
            self.logger.log("DEBUG", "DOC_INTELLIGENCE", f"Using model: {model_id}")
            
            # Start document analysis
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                body={"urlSource": document_url}
            )
            
            # Wait for completion
            self.logger.log("PROCESSING", "DOC_INTELLIGENCE", "⏳ Analyzing document...")
            result = poller.result()
            
            # Extract structured data based on document type
            if document_type:
                extracted_data = await self._extract_structured_data(result, document_type)
            else:
                # Auto-detect document type and extract
                detected_type = await self._detect_document_type(result)
                extracted_data = await self._extract_structured_data(result, detected_type)
            
            self.logger.log("SUCCESS", "DOC_INTELLIGENCE", 
                           f"✅ Document processed successfully: {len(extracted_data)} fields extracted")
            
            return {
                'success': True,
                'document_type': document_type or detected_type,
                'extracted_data': extracted_data,
                'processing_time': datetime.now().isoformat(),
                'model_used': model_id
            }
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", 
                           f"Failed to process document {document_url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'document_url': document_url,
                'processing_time': datetime.now().isoformat()
            }
    
    async def _detect_document_type(self, result) -> str:
        """Auto-detect document type based on content"""
        try:
            # Get all text content
            full_text = ""
            if result.content:
                full_text = result.content.lower()
            
            # Check for keywords to determine document type
            for doc_type, config in self.document_field_mappings.items():
                keyword_matches = sum(1 for keyword in config['keywords'] if keyword in full_text)
                if keyword_matches >= 2:  # At least 2 keywords match
                    self.logger.log("DEBUG", "DOC_INTELLIGENCE", 
                                   f"Detected document type: {doc_type} ({keyword_matches} keywords matched)")
                    return doc_type
            
            # Default to memo if no clear match
            self.logger.log("DEBUG", "DOC_INTELLIGENCE", "Document type unclear, defaulting to memo")
            return "memo"
            
        except Exception as e:
            self.logger.log("WARNING", "DOC_INTELLIGENCE", f"Document type detection failed: {e}")
            return "memo"
    
    async def _extract_structured_data(self, result, document_type: str) -> Dict[str, Any]:
        """Extract structured data based on document type"""
        try:
            extracted = {}
            
            if document_type == "discharge_summary":
                extracted = await self._extract_discharge_summary_data(result)
            elif document_type == "medical_bill":
                extracted = await self._extract_medical_bill_data(result)
            elif document_type == "memo":
                extracted = await self._extract_memo_data(result)
            else:
                # Generic extraction
                extracted = await self._extract_generic_data(result)
            
            self.logger.log("DEBUG", "DOC_INTELLIGENCE", 
                           f"Extracted fields for {document_type}: {list(extracted.keys())}")
            
            return extracted
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", 
                           f"Data extraction failed for {document_type}: {str(e)}")
            return {}
    
    async def _extract_discharge_summary_data(self, result) -> Dict[str, Any]:
        """Extract data from discharge summary documents"""
        extracted = {
            'patient_name': None,
            'hospital_name': None,
            'admit_date': None,
            'discharge_date': None,
            'medical_condition': None
        }
        
        try:
            # Extract from key-value pairs if available
            if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value:
                        key_text = kv_pair.key.content.lower() if kv_pair.key.content else ""
                        value_text = kv_pair.value.content if kv_pair.value.content else ""
                        
                        # Patient name
                        if any(term in key_text for term in ['patient', 'name']):
                            extracted['patient_name'] = value_text
                        
                        # Hospital name
                        elif any(term in key_text for term in ['hospital', 'facility', 'medical center']):
                            extracted['hospital_name'] = value_text
                        
                        # Admit date
                        elif any(term in key_text for term in ['admit', 'admission']):
                            extracted['admit_date'] = value_text
                        
                        # Discharge date
                        elif any(term in key_text for term in ['discharge', 'released']):
                            extracted['discharge_date'] = value_text
                        
                        # Medical condition
                        elif any(term in key_text for term in ['diagnosis', 'condition', 'primary']):
                            extracted['medical_condition'] = value_text
            
            # Fallback to text analysis if key-value pairs don't work
            if not extracted['patient_name'] and result.content:
                extracted.update(await self._extract_from_text_patterns(result.content, 'discharge_summary'))
            
            return extracted
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", f"Discharge summary extraction error: {e}")
            return extracted
    
    async def _extract_medical_bill_data(self, result) -> Dict[str, Any]:
        """Extract data from medical bill documents"""
        extracted = {
            'patient_name': None,
            'bill_date': None,
            'bill_amount': None
        }
        
        try:
            # For invoice model, use specific fields
            if hasattr(result, 'documents') and result.documents:
                document = result.documents[0]
                
                # Get customer name (patient name)
                if hasattr(document, 'fields'):
                    fields = document.fields
                    
                    # Patient name from customer fields
                    if 'CustomerName' in fields and fields['CustomerName'].content:
                        extracted['patient_name'] = fields['CustomerName'].content
                    elif 'BillingAddress' in fields and fields['BillingAddress'].content:
                        # Extract name from billing address
                        billing_text = fields['BillingAddress'].content
                        lines = billing_text.split('\n')
                        if lines:
                            extracted['patient_name'] = lines[0].strip()
                    
                    # Bill date
                    if 'InvoiceDate' in fields and fields['InvoiceDate'].content:
                        extracted['bill_date'] = str(fields['InvoiceDate'].content)
                    
                    # Bill amount
                    if 'InvoiceTotal' in fields and fields['InvoiceTotal'].content:
                        try:
                            extracted['bill_amount'] = float(fields['InvoiceTotal'].content)
                        except:
                            extracted['bill_amount'] = fields['InvoiceTotal'].content
                    elif 'AmountDue' in fields and fields['AmountDue'].content:
                        try:
                            extracted['bill_amount'] = float(fields['AmountDue'].content)
                        except:
                            extracted['bill_amount'] = fields['AmountDue'].content
            
            # Fallback to key-value pairs
            if not extracted['patient_name'] and hasattr(result, 'key_value_pairs'):
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value:
                        key_text = kv_pair.key.content.lower() if kv_pair.key.content else ""
                        value_text = kv_pair.value.content if kv_pair.value.content else ""
                        
                        # Patient name
                        if any(term in key_text for term in ['patient', 'name', 'bill to']):
                            extracted['patient_name'] = value_text
                        
                        # Date
                        elif any(term in key_text for term in ['date', 'bill date', 'service date']):
                            extracted['bill_date'] = value_text
                        
                        # Amount
                        elif any(term in key_text for term in ['total', 'amount', 'due', 'balance']):
                            # Extract numeric value
                            import re
                            amount_match = re.search(r'[\d,]+\.?\d*', value_text.replace('$', '').replace(',', ''))
                            if amount_match:
                                try:
                                    extracted['bill_amount'] = float(amount_match.group())
                                except:
                                    pass
            
            return extracted
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", f"Medical bill extraction error: {e}")
            return extracted
    
    async def _extract_memo_data(self, result) -> Dict[str, Any]:
        """Extract data from memo documents"""
        extracted = {
            'patient_name': None,
            'medical_condition': None
        }
        
        try:
            # Extract from key-value pairs
            if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value:
                        key_text = kv_pair.key.content.lower() if kv_pair.key.content else ""
                        value_text = kv_pair.value.content if kv_pair.value.content else ""
                        
                        # Patient name
                        if any(term in key_text for term in ['patient', 'name']):
                            extracted['patient_name'] = value_text
                        
                        # Medical condition
                        elif any(term in key_text for term in ['diagnosis', 'condition', 'medical condition']):
                            extracted['medical_condition'] = value_text
            
            # Fallback to text analysis
            if not extracted['patient_name'] and result.content:
                extracted.update(await self._extract_from_text_patterns(result.content, 'memo'))
            
            return extracted
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", f"Memo extraction error: {e}")
            return extracted
    
    async def _extract_from_text_patterns(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Extract data using text pattern matching as fallback"""
        import re
        extracted = {}
        
        try:
            # Common patterns for patient names
            name_patterns = [
                r'Patient[:\s]+([A-Za-z\s]+)',
                r'Name[:\s]+([A-Za-z\s]+)',
                r'Patient Name[:\s]+([A-Za-z\s]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['patient_name'] = match.group(1).strip()
                    break
            
            # Condition/diagnosis patterns
            if doc_type in ['discharge_summary', 'memo']:
                condition_patterns = [
                    r'Diagnosis[:\s]+([^.\n]+)',
                    r'Condition[:\s]+([^.\n]+)',
                    r'Medical Condition[:\s]+([^.\n]+)'
                ]
                
                for pattern in condition_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        extracted['medical_condition'] = match.group(1).strip()
                        break
            
            # Date patterns for bills
            if doc_type == 'medical_bill':
                date_patterns = [
                    r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                    r'Bill Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        extracted['bill_date'] = match.group(1).strip()
                        break
            
            return extracted
            
        except Exception as e:
            self.logger.log("WARNING", "DOC_INTELLIGENCE", f"Text pattern extraction failed: {e}")
            return {}
    
    async def _extract_generic_data(self, result) -> Dict[str, Any]:
        """Generic data extraction for unknown document types"""
        extracted = {}
        
        try:
            # Extract all key-value pairs
            if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value and kv_pair.key.content and kv_pair.value.content:
                        key = kv_pair.key.content.strip().lower().replace(' ', '_')
                        value = kv_pair.value.content.strip()
                        extracted[key] = value
            
            # Also extract first few lines of text
            if hasattr(result, 'content') and result.content:
                lines = result.content.split('\n')[:10]  # First 10 lines
                extracted['content_preview'] = '\n'.join(line.strip() for line in lines if line.strip())
            
            return extracted
            
        except Exception as e:
            self.logger.log("WARNING", "DOC_INTELLIGENCE", f"Generic extraction failed: {e}")
            return {}
    
    async def process_multiple_documents(self, document_urls: Dict[str, str]) -> Dict[str, Any]:
        """
        Process multiple documents for a claim
        
        Args:
            document_urls: Dictionary mapping document types to URLs
                          e.g., {'billAttachment': 'url1', 'memoAttachment': 'url2', 'dischargeAttachment': 'url3'}
        
        Returns:
            Dictionary with extracted data for each document type
        """
        try:
            self.logger.log("INFO", "DOC_INTELLIGENCE", 
                           f"🔄 Processing {len(document_urls)} documents...")
            
            results = {}
            
            # Map attachment names to document types
            attachment_mapping = {
                'billAttachment': 'medical_bill',
                'memoAttachment': 'memo', 
                'dischargeAttachment': 'discharge_summary'
            }
            
            for attachment_name, document_url in document_urls.items():
                if document_url and document_url.strip():
                    doc_type = attachment_mapping.get(attachment_name, 'memo')
                    
                    self.logger.log("PROCESSING", "DOC_INTELLIGENCE", 
                                   f"📄 Processing {attachment_name} as {doc_type}")
                    
                    result = await self.process_document_from_url(document_url, doc_type)
                    results[doc_type] = result
                else:
                    self.logger.log("WARNING", "DOC_INTELLIGENCE", 
                                   f"⚠️ No URL provided for {attachment_name}")
            
            self.logger.log("SUCCESS", "DOC_INTELLIGENCE", 
                           f"✅ Completed processing {len(results)} documents")
            
            return {
                'success': True,
                'documents_processed': len(results),
                'results': results,
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log("ERROR", "DOC_INTELLIGENCE", 
                           f"Multiple document processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': datetime.now().isoformat()
            }

# Global client instance
_doc_intelligence_client = None

async def get_document_intelligence_client() -> AzureDocumentIntelligenceClient:
    """Get or create global Document Intelligence client instance"""
    global _doc_intelligence_client
    
    if _doc_intelligence_client is None:
        _doc_intelligence_client = AzureDocumentIntelligenceClient()
        await _doc_intelligence_client.initialize()
    
    return _doc_intelligence_client

# Convenience functions
async def process_claim_documents(document_urls: Dict[str, str]) -> Dict[str, Any]:
    """Convenience function to process all documents for a claim"""
    client = await get_document_intelligence_client()
    return await client.process_multiple_documents(document_urls)

async def process_single_document(document_url: str, document_type: str = None) -> Dict[str, Any]:
    """Convenience function to process a single document"""
    client = await get_document_intelligence_client()
    return await client.process_document_from_url(document_url, document_type)
