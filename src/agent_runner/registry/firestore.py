"""Firestore agent registry CRUD operations."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

DEFAULT_DATABASE = "agents"
REGISTRY_COLLECTION = "registry"
AGENTS_COLLECTION = "agents"

# An agent is considered stale if it hasn't heartbeated within this window.
STALE_THRESHOLD = timedelta(minutes=10)

# Placeholder descriptions that indicate unconfigured agents.
_PLACEHOLDER_DESCRIPTIONS = frozenset({
    "What this agent does",
    "",
})


def _firestore_client(project: str, database: str = DEFAULT_DATABASE):
    from google.cloud.firestore import Client

    return Client(project=project, database=database)


def _compute_status(last_heartbeat, threshold: timedelta = STALE_THRESHOLD) -> str:
    """Derive effective status from heartbeat recency."""
    if last_heartbeat is None:
        return "unknown"
    now = datetime.now(timezone.utc)
    # Handle both datetime objects and Firestore DatetimeWithNanoseconds
    if hasattr(last_heartbeat, "timestamp"):
        hb = last_heartbeat if last_heartbeat.tzinfo else last_heartbeat.replace(tzinfo=timezone.utc)
    else:
        return "unknown"
    if (now - hb) > threshold:
        return "stale"
    return "online"


def advertise(
    agent_name: str,
    service_url: str,
    capabilities: list[str],
    description: str,
    project: str,
    *,
    model: str | None = None,
):
    """Upsert agent entry in the Firestore registry (non-fatal on failure).

    Writes a unified record that includes both runtime state (heartbeat,
    service_url) and config metadata (model, description) so the registry
    collection alone is sufficient for discovery and status queries.
    """
    now = datetime.now(timezone.utc)
    registry_data: dict = {
        "name": agent_name,
        "service_url": service_url,
        "capabilities": capabilities,
        "description": description,
        "status": "online",
        "last_heartbeat": now,
        "project": project,
    }
    if model:
        registry_data["model"] = model

    try:
        db = _firestore_client(project)
        db.collection(REGISTRY_COLLECTION).document(agent_name).set(registry_data, merge=True)
        print(f"Registry updated for agent '{agent_name}'", file=sys.stderr)
    except Exception as exc:
        print(f"Failed to update registry: {exc}", file=sys.stderr)


def discover(
    capability: str | None = None,
    project: str = "claude-connectors",
    *,
    include_stale: bool = False,
) -> list[dict]:
    """Query the Firestore registry for available agents.

    Status is always computed dynamically from heartbeat recency rather
    than relying on the stored ``status`` field.  By default only agents
    whose heartbeat is within STALE_THRESHOLD are returned.  Set
    include_stale=True to return all registered agents with a computed
    ``effective_status`` field.
    """
    db = _firestore_client(project)

    results = []
    for doc in db.collection(REGISTRY_COLLECTION).stream():
        data = doc.to_dict()
        if capability and capability not in data.get("capabilities", []):
            continue
        effective = _compute_status(data.get("last_heartbeat"))
        data["effective_status"] = effective
        if not include_stale and effective != "online":
            continue
        results.append(data)

    return results


def list_peers(project: str = "claude-connectors") -> list[dict]:
    """Return all registered agents with unified config + status info."""
    return list_agents_unified(project=project)


def list_agents_unified(project: str = "claude-connectors") -> list[dict]:
    """Return a unified view joining registry and agents collections.

    Each result includes runtime state from ``registry/{name}`` merged with
    config metadata from ``agents/{name}`` (if it exists).  The
    ``effective_status`` field is computed from heartbeat recency.
    ``has_config`` indicates whether a Firestore config document exists.
    ``has_system_prompt`` indicates whether a system prompt is configured.
    """
    db = _firestore_client(project)

    # Load all agent config documents keyed by name
    configs: dict[str, dict] = {}
    for doc in db.collection(AGENTS_COLLECTION).stream():
        data = doc.to_dict()
        name = data.get("name", doc.id)
        configs[name] = data

    # Load all registry entries
    results = []
    seen_names: set[str] = set()
    for doc in db.collection(REGISTRY_COLLECTION).stream():
        data = doc.to_dict()
        name = data.get("name", doc.id)
        seen_names.add(name)

        effective = _compute_status(data.get("last_heartbeat"))
        data["effective_status"] = effective

        # Merge config fields
        cfg = configs.get(name, {})
        data["has_config"] = name in configs
        data["has_system_prompt"] = bool(cfg.get("system_prompt"))
        data["model"] = cfg.get("model") or data.get("model", "")
        data["description_placeholder"] = data.get("description", "") in _PLACEHOLDER_DESCRIPTIONS

        results.append(data)

    # Include agents with config but no registry entry (deployed but never started)
    for name, cfg in configs.items():
        if name not in seen_names:
            results.append({
                "name": name,
                "service_url": cfg.get("service_url", ""),
                "capabilities": cfg.get("capabilities", []),
                "description": cfg.get("description", ""),
                "effective_status": "not_registered",
                "has_config": True,
                "has_system_prompt": bool(cfg.get("system_prompt")),
                "model": cfg.get("model", ""),
                "description_placeholder": cfg.get("description", "") in _PLACEHOLDER_DESCRIPTIONS,
            })

    results.sort(key=lambda r: r.get("name", ""))
    return results


def mark_stale(project: str = "claude-connectors", threshold: timedelta = STALE_THRESHOLD) -> int:
    """Mark agents as stale if their heartbeat exceeds the threshold.

    Returns the number of agents marked stale.
    """
    db = _firestore_client(project)
    cutoff = datetime.now(timezone.utc) - threshold
    count = 0

    for doc in db.collection(REGISTRY_COLLECTION).where("status", "==", "online").stream():
        data = doc.to_dict()
        hb = data.get("last_heartbeat")
        if hb is None:
            continue
        if hasattr(hb, "tzinfo") and hb.tzinfo is None:
            hb = hb.replace(tzinfo=timezone.utc)
        if hb < cutoff:
            doc.reference.update({"status": "stale"})
            count += 1
            print(f"Marked '{data.get('name', doc.id)}' as stale", file=sys.stderr)

    return count
