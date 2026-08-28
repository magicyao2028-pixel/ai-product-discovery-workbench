"""Evidence-traceable product discovery workflow."""

from .engine import DiscoveryWorkbench
from .interview_review import build_interview_claim_review
from .models import DiscoveryPacket, load_packet
from .report import render_markdown
from .sensitivity import PriorityScenario, compare_priority_scenarios, load_priority_scenarios
from .templates import TemplateProfile, TemplateValidationError, load_template_profile
from .grounded import build_grounded_summary
from .service_contract import analyze_request, build_request_receipt

__all__ = [
    "DiscoveryPacket", "DiscoveryWorkbench", "build_interview_claim_review", "load_packet",
    "PriorityScenario", "compare_priority_scenarios", "load_priority_scenarios", "render_markdown",
    "TemplateProfile", "TemplateValidationError", "load_template_profile",
    "build_grounded_summary",
    "analyze_request", "build_request_receipt",
]
__version__ = "0.7.0"
