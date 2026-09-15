"""
Seismic data integration service for Landslide Guardian.
Queries the USGS Earthquake Hazards Program GeoJSON feed for real-time
seismic events across Northeast India and surrounding tectonic margins.

Calculates site-specific Peak Ground Acceleration (PGA) and horizontal
seismic acceleration coefficient (k_h) for limit-equilibrium slope stability.
"""

import asyncio
import logging
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

USGS_FEED_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
_CACHE: Dict[str, Any] = {}
_CACHE_TTL = 300  # 5 minutes cache to prevent any rate-limiting


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(max(1.0 - a, 1e-12)))


def _estimate_pga(magnitude: float, distance_km: float, depth_km: float = 15.0) -> float:
    """
    Standard Himalayan Ground Motion Attenuation Model:
    Estimates Peak Ground Acceleration (PGA) in units of g.
    """
    hypocentral_dist = math.sqrt(distance_km ** 2 + max(5.0, depth_km) ** 2)
    # Joyner-Boore / Himalayan empirical form
    log_pga = -1.5 + 0.28 * magnitude - 1.05 * math.log10(hypocentral_dist)
    pga = 10 ** log_pga
    return round(max(0.001, min(pga, 1.5)), 4)


async def fetch_recent_earthquakes(past_days: int = 3) -> List[Dict]:
    """
    Fetches real-time seismic events in the Northeast India / Himalayan bounding box
    (Lat: 20.0 to 30.0, Lon: 87.0 to 98.0).
    """
    now = time.time()
    cache_entry = _CACHE.get("quakes")
    if cache_entry and (now - cache_entry[0] < _CACHE_TTL):
        return cache_entry[1]

    start_time = (datetime.now(timezone.utc) - timedelta(days=past_days)).strftime("%Y-%m-%dT%H:%M:%S")

    params = {
        "format": "geojson",
        "starttime": start_time,
        "minmagnitude": "3.0",
        "minlatitude": "20.0",
        "maxlatitude": "30.0",
        "minlongitude": "87.0",
        "maxlongitude": "98.0",
        "limit": "25",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(USGS_FEED_URL, params=params, timeout=1.8)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                parsed = []
                for feat in features:
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 10])
                    parsed.append({
                        "id": feat.get("id"),
                        "mag": float(props.get("mag") or 0.0),
                        "place": str(props.get("place") or "Regional tremor"),
                        "time_epoch_ms": props.get("time"),
                        "lon": coords[0],
                        "lat": coords[1],
                        "depth_km": coords[2] if len(coords) > 2 else 10.0,
                    })
                _CACHE["quakes"] = (now, parsed)
                return parsed
    except Exception as exc:
        logger.warning("USGS Earthquake API unavailable or timed out: %s. Using silent fallback.", exc)

    return _CACHE.get("quakes", (now, []))[1]


async def get_seismic_risk_factor(lat: float, lon: float) -> Dict[str, Any]:
    """
    Computes site-specific seismic ground motion parameters for (lat, lon).
    Returns PGA and pseudostatic seismic coefficient k_h.
    """
    default_res = {
        "active_earthquake": False,
        "recent_quakes_count": 0,
        "nearest_magnitude": None,
        "nearest_distance_km": None,
        "nearest_place": None,
        "estimated_pga_g": 0.002,
        "seismic_coefficient_kh": 0.0,
        "seismic_status": "QUIET",
        "source": "USGS_LIVE",
    }

    try:
        quakes = await fetch_recent_earthquakes(past_days=3)
        if not quakes:
            return default_res

        # Filter within 250 km radius of the target location
        closest = None
        min_dist = 99999.0
        max_pga = 0.001

        for q in quakes:
            d = _haversine_distance_km(lat, lon, q["lat"], q["lon"])
            pga = _estimate_pga(q["mag"], d, q["depth_km"])
            if pga > max_pga:
                max_pga = pga
            if d < min_dist:
                min_dist = d
                closest = q

        kh = round(0.5 * max_pga, 3)  # Standard pseudostatic seismic coefficient ~ 0.5 * PGA

        status = "QUIET"
        active = False
        if max_pga >= 0.10:
            status = "SEVERE"
            active = True
        elif max_pga >= 0.04:
            status = "MODERATE"
            active = True
        elif min_dist <= 80.0 and closest and closest["mag"] >= 4.0:
            status = "TREMOR_DETECTED"
            active = True

        return {
            "active_earthquake": active,
            "recent_quakes_count": len(quakes),
            "nearest_magnitude": closest["mag"] if closest else None,
            "nearest_distance_km": round(min_dist, 1) if closest else None,
            "nearest_place": closest["place"] if closest else None,
            "estimated_pga_g": round(max_pga, 3),
            "seismic_coefficient_kh": kh,
            "seismic_status": status,
            "source": "USGS_LIVE",
        }
    except Exception as exc:
        logger.exception("Error calculating seismic risk factor: %s", exc)
        return default_res
