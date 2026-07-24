import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class XAICard(BaseModel):
    """
    Standardized Explainable AI (XAI) Card attached to every agent recommendation.
    Guarantees full transparency, financial auditability, and carbon impact traceability.
    """
    agent_name: str = Field(..., description="Name of the executing agent")
    recommendation: str = Field(..., description="Actionable operational directive")
    reasoning_why: str = Field(..., description="Root cause explanation based on telemetry/tariffs")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence (0.0 to 1.0)")
    financial_impact_inr: str = Field(..., description="Calculated cost savings or financial penalty avoidance")
    carbon_impact_kg: str = Field(..., description="Calculated CO2 reduction in kg")
    risk_level: str = Field("LOW", description="Risk classification: LOW, MEDIUM, HIGH, CRITICAL")
    human_approval_required: bool = Field(True, description="Whether human executive approval is required")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Raw telemetry and benchmark metrics")

class BaseAgent:
    """
    Abstract Base Class for all PRAGATI AI specialized agents.
    Provides standard logging, tool execution wrappers, and XAI card generation.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.execution_logs: List[Dict[str, Any]] = []

    def log_step(self, step_name: str, details: Dict[str, Any]):
        entry = {
            "timestamp": time.time(),
            "agent": self.name,
            "step": step_name,
            "details": details
        }
        self.execution_logs.append(entry)
        logger.info(f"[{self.name}] {step_name}: {details}")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement the run() method.")
