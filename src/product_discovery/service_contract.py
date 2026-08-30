from __future__ import annotations

import hashlib
import json
from typing import Any

from .engine import DiscoveryWorkbench
from .models import DiscoveryPacket


SERVICE_SCHEMA_VERSION = "1.0"
SUPPORTED_GROUNDED_MODES = {"fallback", "local_extractive"}


def build_request_receipt(packet_payload: dict[str, Any], grounded_mode: str) -> dict[str, Any]:
    """Return deterministic trace metadata without persisting the request."""
    canonical = {
        "packet": packet_payload,
        "grounded_mode": grounded_mode,
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "request_fingerprint": f"sha256:{hashlib.sha256(encoded).hexdigest()}",
        "grounded_mode": grounded_mode,
        "idempotency_scope": "validated_packet_and_grounded_mode",
        "retry_safe": True,
        "persistence_executed": False,
        "deduplication_executed": False,
    }


def analyze_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and execute one offline discovery request."""
    if not isinstance(payload, dict):
        raise ValueError("service request must be an object")
    schema_version = payload.get("schema_version", SERVICE_SCHEMA_VERSION)
    if schema_version != SERVICE_SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {schema_version}")
    packet_payload = payload.get("packet")
    if not isinstance(packet_payload, dict):
        raise ValueError("service request packet must be an object")
    grounded_mode = payload.get("grounded_mode", "fallback")
    if grounded_mode not in SUPPORTED_GROUNDED_MODES:
        raise ValueError("grounded_mode must be fallback or local_extractive")
    packet = DiscoveryPacket.from_mapping(packet_payload)
    result = DiscoveryWorkbench().build(packet, grounded_mode=grounded_mode)
    return {
        "schema_version": SERVICE_SCHEMA_VERSION,
        "status": "ok",
        "request_receipt": build_request_receipt(packet_payload, grounded_mode),
        "review": result,
        "governance": {
            "persistence_executed": False,
            "external_action_executed": False,
            "human_approval_required": True,
        },
    }
