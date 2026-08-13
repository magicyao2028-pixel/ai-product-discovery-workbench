"""Evidence-traceable product discovery workflow."""

from .engine import DiscoveryWorkbench
from .interview_review import build_interview_claim_review
from .models import DiscoveryPacket, load_packet
from .report import render_markdown

__all__ = [
    "DiscoveryPacket", "DiscoveryWorkbench", "build_interview_claim_review", "load_packet",
    "render_markdown",
]
__version__ = "0.3.0"
