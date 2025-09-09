"""
Workflow Logger for Insurance Claims Processing
Captures structured workflow events for dashboard visualization with file persistence and real-time updates
"""

import json
import os
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

class WorkflowStepType(Enum):
    DISCOVERY = "discovery"
    AGENT_SELECTION = "agent_selection"
    TASK_DISPATCH = "task_dispatch"
    AGENT_RESPONSE = "agent_response"
    DECISION = "decision"
    COMPLETION = "completion"

class WorkflowStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Represents a single step in the workflow"""
    step_id: str
    claim_id: str
    step_type: WorkflowStepType
    title: str
    description: str
    status: WorkflowStepStatus
    timestamp: str
    agent_name: Optional[str] = None
    agent_reasoning: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['step_type'] = self.step_type.value
        data['status'] = self.status.value
        return data

class WorkflowLogger:
    """Captures and manages workflow events for dashboard visualization with file persistence"""
    
    def __init__(self):
        self.workflow_steps: Dict[str, List[WorkflowStep]] = {}
        self.current_claim: Optional[str] = None
        self.step_counter = 0
        self.dashboard_url = "http://localhost:3000"  # Dashboard webhook URL (Fixed port!)
        
        # Set up persistent storage with absolute path
        # Find the insurance root directory (where workflow_logs should be)
        current_file = Path(__file__).resolve()
        # Go up from shared/workflow_logger.py -> shared -> insurance_agents -> insurance
        insurance_root = current_file.parent.parent.parent
        self.storage_dir = insurance_root / "workflow_logs" 
        self.storage_dir.mkdir(exist_ok=True)
        self.storage_file = self.storage_dir / "workflow_steps.json"
        
        # Load existing data
        self._load_from_file()
    
    def _send_to_dashboard(self, step_data: Dict[str, Any]) -> None:
        """Send workflow step to dashboard in real-time"""
        try:
            import httpx
            with httpx.Client(timeout=1.0) as client:
                client.post(f"{self.dashboard_url}/api/workflow-step", json=step_data)
        except Exception as e:
            # Silently fail if dashboard is not available
            pass
    
    def _load_from_file(self) -> None:
        """Load workflow steps from persistent storage"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    
                    # Convert back to WorkflowStep objects
                    for claim_id, steps_data in data.items():
                        steps = []
                        for step_data in steps_data:
                            # Convert enum strings back to enums
                            step_data['step_type'] = WorkflowStepType(step_data['step_type'])
                            step_data['status'] = WorkflowStepStatus(step_data['status'])
                            steps.append(WorkflowStep(**step_data))
                        self.workflow_steps[claim_id] = steps
        except Exception as e:
            print(f"⚠️ Could not load workflow steps from file: {e}")
    
    def _save_to_file(self) -> None:
        """Save workflow steps to persistent storage"""
        try:
            # Convert to serializable format
            data = {}
            for claim_id, steps in self.workflow_steps.items():
                data[claim_id] = [step.to_dict() for step in steps]
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save workflow steps to file: {e}")
    
    def start_claim_processing(self, claim_id: str) -> None:
        """Start tracking a new claim processing workflow"""
        print(f"🔍 WORKFLOW_LOGGER: Starting claim processing for {claim_id}")
        self.current_claim = claim_id
        self.workflow_steps[claim_id] = []
        self.step_counter = 0
        self._save_to_file()  # Persist immediately
        print(f"🔍 WORKFLOW_LOGGER: Claim {claim_id} initialized successfully")
        
    def add_step(self, 
                 step_type: WorkflowStepType,
                 title: str,
                 description: str,
                 status: WorkflowStepStatus = WorkflowStepStatus.IN_PROGRESS,
                 agent_name: Optional[str] = None,
                 agent_reasoning: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None) -> str:
        """Add a new workflow step"""
        
        if not self.current_claim:
            raise ValueError("No active claim processing")
            
        self.step_counter += 1
        step_id = f"step_{self.step_counter:02d}"
        
        step = WorkflowStep(
            step_id=step_id,
            claim_id=self.current_claim,
            step_type=step_type,
            title=title,
            description=description,
            status=status,
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            agent_reasoning=agent_reasoning,
            details=details or {}
        )
        
        self.workflow_steps[self.current_claim].append(step)
        self._save_to_file()  # Persist immediately
        
        # Send to dashboard in real-time
        self._send_to_dashboard(step.to_dict())
        
        return step_id
    
    def update_step(self, 
                   step_id: str, 
                   status: WorkflowStepStatus,
                   details: Optional[Dict[str, Any]] = None,
                   duration_ms: Optional[int] = None) -> None:
        """Update an existing workflow step"""
        
        if not self.current_claim:
            return
            
        for step in self.workflow_steps[self.current_claim]:
            if step.step_id == step_id:
                step.status = status
                if details:
                    step.details.update(details)
                if duration_ms:
                    step.duration_ms = duration_ms
                self._save_to_file()  # Persist immediately
                break
    
    def log_discovery(self, agents_found: int, agent_details: List[Dict[str, Any]]) -> str:
        """Log agent discovery phase"""
        print(f"🔍 WORKFLOW_LOGGER: Logging discovery - found {agents_found} agents")
        return self.add_step(
            step_type=WorkflowStepType.DISCOVERY,
            title="🔍 Agent Discovery",
            description=f"Discovering available agents for claim processing",
            details={
                "agents_found": agents_found,
                "agent_details": agent_details
            }
        )
    
    def log_agent_selection(self, 
                          task_type: str,
                          selected_agent: str,
                          agent_name: str,
                          reasoning: str,
                          alternatives: List[str] = None) -> str:
        """Log agent selection with reasoning"""
        return self.add_step(
            step_type=WorkflowStepType.AGENT_SELECTION,
            title=f"🎯 Agent Selection - {task_type.title()}",
            description=f"Selected {agent_name} for {task_type}",
            agent_name=selected_agent,
            agent_reasoning=reasoning,
            details={
                "task_type": task_type,
                "selected_agent": selected_agent,
                "alternatives_considered": alternatives or []
            }
        )
    
    def log_task_dispatch(self, 
                         agent_name: str,
                         task_description: str,
                         agent_url: str) -> str:
        """Log task being sent to agent"""
        return self.add_step(
            step_type=WorkflowStepType.TASK_DISPATCH,
            title=f"📤 Task Dispatch",
            description=f"Sending task to {agent_name}",
            agent_name=agent_name,
            details={
                "task_description": task_description,
                "agent_url": agent_url
            }
        )
    
    def log_agent_response(self,
                          agent_name: str,
                          success: bool,
                          response_summary: str,
                          response_details: Dict[str, Any] = None) -> str:
        """Log agent response"""
        status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED
        return self.add_step(
            step_type=WorkflowStepType.AGENT_RESPONSE,
            title=f"📥 Agent Response - {agent_name}",
            description=response_summary,
            agent_name=agent_name,
            status=status,
            details=response_details or {}
        )
    
    def log_final_decision(self,
                          decision: str,
                          reasoning: str,
                          confidence: float,
                          factors: Dict[str, Any]) -> str:
        """Log final decision making"""
        return self.add_step(
            step_type=WorkflowStepType.DECISION,
            title="🎯 Final Decision",
            description=f"Decision: {decision.upper()}",
            status=WorkflowStepStatus.COMPLETED,
            details={
                "decision": decision,
                "reasoning": reasoning,
                "confidence": confidence,
                "decision_factors": factors
            }
        )
    
    def log_completion(self, 
                      claim_id: str,
                      final_status: str,
                      processing_time_ms: int) -> str:
        """Log workflow completion"""
        return self.add_step(
            step_type=WorkflowStepType.COMPLETION,
            title="🎉 Processing Complete",
            description=f"Claim {claim_id} processed successfully",
            status=WorkflowStepStatus.COMPLETED,
            details={
                "final_status": final_status,
                "total_processing_time_ms": processing_time_ms
            }
        )
    
    def get_workflow_steps(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get all workflow steps for a claim"""
        # Refresh from file to get latest data from other processes
        self._load_from_file()
        
        if claim_id not in self.workflow_steps:
            return []
        return [step.to_dict() for step in self.workflow_steps[claim_id]]
    
    def get_all_recent_steps(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent workflow steps across all claims"""
        # Refresh from file to get latest data from other processes
        self._load_from_file()
        
        all_steps = []
        for claim_steps in self.workflow_steps.values():
            all_steps.extend([step.to_dict() for step in claim_steps])
        
        # Sort by timestamp, most recent first
        all_steps.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_steps[:limit]

# Global workflow logger instance
workflow_logger = WorkflowLogger()
