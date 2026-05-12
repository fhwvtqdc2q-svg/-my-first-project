"""Shared local settings loader for the local prototype."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = BASE_DIR / "config" / "settings.json"


DEFAULT_SETTINGS: Dict[str, Any] = {
    "business": {
        "default_warehouse_name": "Main Warehouse",
        "default_currency": "USD",
        "local_currency": "SYP",
    },
    "accounting": {
        "overdue_days": 4,
        "cash_average_days": 7,
        "cash_low_threshold_ratio": 0.75,
    },
    "price_list": {
        "show_quantities_to_customers": True,
        "hide_inactive_products": True,
        "hide_out_of_stock_products": True,
        "require_price_for_published_items": True,
        "syp_rounding": 1,
    },
    "security": {
        "local_only": True,
        "allow_external_connections": False,
        "allow_auto_send_messages": False,
        "allow_auto_publish_social_media": False,
        "allow_sms_authentication": False,
    },
    "audit": {
        "enabled": True,
        "audit_log_file": "audit-log.csv",
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_settings(path: str | Path | None = None) -> Dict[str, Any]:
    settings_path = Path(path) if path else DEFAULT_SETTINGS_PATH
    if not settings_path.exists():
        return DEFAULT_SETTINGS
    with settings_path.open("r", encoding="utf-8") as file:
        loaded = json.load(file)
    return deep_merge(DEFAULT_SETTINGS, loaded)


def require_local_safe_settings(settings: Dict[str, Any]) -> None:
    """Fail fast if a local prototype safety setting is disabled."""
    security = settings.get("security", {})
    if not security.get("local_only", True):
        raise ValueError("Unsafe setting: security.local_only must remain true for this local prototype.")
    if security.get("allow_external_connections", False):
        raise ValueError("Unsafe setting: external connections are not allowed in this local prototype.")
    if security.get("allow_auto_send_messages", False):
        raise ValueError("Unsafe setting: automatic message sending is not allowed.")
    if security.get("allow_auto_publish_social_media", False):
        raise ValueError("Unsafe setting: automatic social media publishing is not allowed.")
    if security.get("allow_sms_authentication", False):
        raise ValueError("Unsafe setting: SMS authentication is not allowed as a primary method.")
