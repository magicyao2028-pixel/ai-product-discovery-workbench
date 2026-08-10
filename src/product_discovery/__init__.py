"""Evidence-traceable product discovery workflow."""

from .engine import DiscoveryWorkbench
from .models import DiscoveryPacket, load_packet
from .report import render_markdown

__all__ = ["DiscoveryPacket", "DiscoveryWorkbench", "load_packet", "render_markdown"]
__version__ = "0.2.0"
