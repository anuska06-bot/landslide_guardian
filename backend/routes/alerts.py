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
    alerts = list(
        db_manager.alerts.find().sort(
            [("risk_score", -1), ("timestamp", -1)]
        ).limit(100)
    )
    return [clean_document(alert) for alert in alerts]


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
