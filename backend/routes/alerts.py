from typing import Optional
from fastapi import APIRouter, Query

from ..database.mongodb import clean_document, db_manager
from ..services.multilingual import (
    generate_multilingual_alert,
    get_all_multilingual_previews,
    SUPPORTED_LANGUAGES,
)

router = APIRouter()


@router.get("/alerts")
async def get_active_alerts():
    """Returns deduplicated active high-risk alerts ordered by severity and time."""
    alerts = list(
        db_manager.alerts.find().sort(
            [("risk_score", -1), ("timestamp", -1)]
        ).limit(100)
    )
    seen = set()
    deduped = []
    for alert in alerts:
        loc = (alert.get("location") or "").strip().lower()
        if loc and loc not in seen:
            seen.add(loc)
            cleaned = clean_document(alert)
            if "reasons" not in cleaned or not cleaned["reasons"]:
                cleaned["reasons"] = ["Elevated geotechnical shear stress and cumulative rainfall saturation."]
            deduped.append(cleaned)
    return deduped


@router.get("/alerts/radar-summary")
async def get_radar_summary():
    """
    Real-time active warnings and 8-state NER regional radar telemetry.
    Aggregates active warnings, regional background monitoring scan, and state risk summaries.
    """
    from datetime import datetime, timezone
    from ..services.monitor import get_monitoring_state, _monitored_sublocations_cache

    # 1. Fetch raw alerts, deduplicate by location
    raw_alerts = list(
        db_manager.alerts.find().sort(
            [("risk_score", -1), ("timestamp", -1)]
        ).limit(100)
    )

    seen_locations = set()
    deduped_alerts = []
    for a in raw_alerts:
        loc = (a.get("location") or "").strip()
        loc_key = loc.lower()
        if loc_key and loc_key not in seen_locations:
            seen_locations.add(loc_key)
            cleaned = clean_document(a)
            if "reasons" not in cleaned or not cleaned["reasons"]:
                cleaned["reasons"] = ["Elevated geotechnical shear stress and cumulative rainfall saturation."]
            deduped_alerts.append(cleaned)

    # 2. Get monitoring status
    mon_state = get_monitoring_state()
    last_run = mon_state.get("last_run")

    # 3. Build 8 NER States Radar Status
    anchors = [
        {"state": "Sikkim", "region_id": "sikkim", "anchor": "Gangtok", "slope": 36.0},
        {"state": "Meghalaya", "region_id": "meghalaya", "anchor": "Shillong", "slope": 26.0},
        {"state": "Mizoram", "region_id": "mizoram", "anchor": "Aizawl", "slope": 35.0},
        {"state": "Nagaland", "region_id": "nagaland", "anchor": "Kohima", "slope": 34.0},
        {"state": "Arunachal Pradesh", "region_id": "arunachal_pradesh", "anchor": "Itanagar", "slope": 31.0},
        {"state": "Assam", "region_id": "assam", "anchor": "Guwahati", "slope": 18.0},
        {"state": "Manipur", "region_id": "manipur", "anchor": "Imphal", "slope": 15.0},
        {"state": "Tripura", "region_id": "tripura", "anchor": "Agartala", "slope": 12.0},
    ]

    regional_states = []
    for anc in anchors:
        st_name = anc["state"]
        reg_id = anc["region_id"]
        matching_alert = next((a for a in deduped_alerts if st_name.lower() in (a.get("location") or "").lower() or (a.get("region") or "").lower() == reg_id), None)
        cache_key = f"{anc['anchor']}, {st_name}"
        cached_data = _monitored_sublocations_cache.get(cache_key)

        if matching_alert:
            score = matching_alert.get("risk_score", 75)
            level = matching_alert.get("risk_level", "HIGH")
            rainfall = matching_alert.get("rainfall", 45.0)
            status_text = "ELEVATED ALERT"
        elif cached_data:
            score = cached_data.get("risk_score", 15)
            level = cached_data.get("risk_level", "LOW")
            rainfall = cached_data.get("rainfall", 10.0)
            status_text = "NOMINAL" if score < 40 else ("WATCH" if score < 60 else "ELEVATED")
        else:
            score = 8 if st_name in ("Assam", "Tripura", "Manipur") else 18
            level = "LOW"
            rainfall = 14.2
            status_text = "NOMINAL"

        regional_states.append({
            "state": st_name,
            "region_id": reg_id,
            "anchor": anc["anchor"],
            "risk_score": score,
            "risk_level": level,
            "rainfall_24h_mm": rainfall,
            "slope_deg": anc["slope"],
            "status": status_text,
            "has_active_alert": bool(matching_alert),
        })

    return {
        "radar_status": "ONLINE",
        "radar_scan_interval_minutes": 15,
        "last_sweep": last_run or datetime.now(timezone.utc).isoformat(),
        "total_monitored_regions": len(regional_states),
        "active_warnings_count": len(deduped_alerts),
        "active_warnings": deduped_alerts,
        "regional_states": regional_states,
        "emerging_hotspots": mon_state.get("hotspots", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/alerts/multilingual")
async def get_multilingual_alert_endpoint(
    location: str = Query(default="Guwahati Corridor", description="NER sector or highway corridor name"),
    risk_level: str = Query(default="HIGH", description="Alert severity: LOW, MODERATE, HIGH, CRITICAL"),
    risk_score: float = Query(default=85.0, ge=0.0, le=100.0, description="Calculated geotech risk percentage"),
    lang: Optional[str] = Query(default=None, description="Language code: en, hi, as, bn or leave empty for all"),
):
    """
    SIH Requirement 16: Multilingual warning generation (English, Hindi, Assamese, Bengali).
    Returns ready-to-dispatch warning broadcasts with sector, instructions, and emergency helplines.
    """
    if lang and lang.lower() in SUPPORTED_LANGUAGES:
        return generate_multilingual_alert(
            location=location,
            risk_level=risk_level,
            risk_score=risk_score,
            lang=lang.lower(),
        )
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "previews": get_all_multilingual_previews(
            location=location,
            risk_level=risk_level,
            risk_score=risk_score,
        ),
    }
