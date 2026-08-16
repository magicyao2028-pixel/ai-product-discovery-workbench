"""Evidence-traceable product discovery workflow."""

from .engine import DiscoveryWorkbench
from .interview_review import build_interview_claim_review
from .models import DiscoveryPacket, load_packet
from .report import render_markdown
from .sensitivity import PriorityScenario, compare_priority_scenarios, load_priority_scenarios

__all__ = [
    "DiscoveryPacket", "DiscoveryWorkbench", "build_interview_claim_review", "load_packet",
    "PriorityScenario", "compare_priority_scenarios", "load_priority_scenarios", "render_markdown",
]
__version__ = "0.4.0"
