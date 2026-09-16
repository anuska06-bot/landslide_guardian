"""
SIH 2026 Compliance & Integrity Test Suite
==========================================
Problem Statement ID: SIH26001
Title: AI-Based Early Warning and Landslide Risk Monitoring System in NER
Team: Ctrl+she2.0

Verifies all official requirements:
- Extra Trees ML model inference & calibration
- Infinite Slope Mohr-Coulomb Factor of Safety physics
- Hydrogeological pore water pressure computation
- Dataset provenance and transparency disclosure
- Multilingual emergency alerts (English, Hindi, Assamese, Bengali)
- Citizen report lifecycle (5 tiers) & response priority calculation
- Highway corridor status tracking across all 8 NER highway corridors
- Historical landslide disaster catalog
- Schema validation for future IoT sensors
"""

import asyncio
import unittest
from backend.ml.predict import predict_landslide_probability, model
from backend.services.terrain_service import calculate_factor_of_safety
from backend.services.pore_pressure import estimated_pore_pressure
from backend.services.multilingual import (
    generate_multilingual_alert,
    get_all_multilingual_previews,
    SUPPORTED_LANGUAGES,
)
from backend.routes.reports import calculate_response_priority, NER_HIGHWAY_CORRIDORS
from backend.routes.dataset import get_train_summary
from backend.routes.pipeline import get_map_layers
from backend.models.schemas import SensorReading, RiskResult
from backend.services.risk_service import calculate_risk_assessment


class TestSIHCompliance(unittest.TestCase):

    def test_01_ml_model_integrity(self):
        """Verify ExtraTreesClassifier inference produces valid probabilities."""
        self.assertIsNotNone(model, "ML Model should be loaded and ready.")
        # Typical steep terrain conditions in NER
        test_inputs = {
            "slope_angle_deg": 38.5,
            "soil_moisture": 72.0,
            "rainfall": 65.0,
            "water_pressure": 45.0,
            "acceleration": 9.81,
            "tilt_angle": 1.2,
            "temperature": 20.0,
            "humidity": 85.0,
            "antecedent_rainfall_7d": 120.0,
        }
        prob = predict_landslide_probability(test_inputs)
        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        # On a 38.5° saturated slope with 65mm rain, risk should not be 0
        self.assertGreater(prob, 0.20, "ML probability should reflect elevated hazard on steep saturated slopes.")

    def test_02_factor_of_safety_physics(self):
        """Verify Infinite Slope Mohr-Coulomb equation behaves realistically."""
        # Gentle slope vs steep slope
        fos_gentle = calculate_factor_of_safety(
            {"slope_deg": 15.0, "cohesion_kpa": 15.0, "phi": 28.0, "soil_depth_m": 2.0},
            soil_moisture_pct=25.0,
            pore_pressure_kpa=2.0
        )
        fos_steep = calculate_factor_of_safety(
            {"slope_deg": 42.0, "cohesion_kpa": 8.0, "phi": 22.0, "soil_depth_m": 2.5},
            soil_moisture_pct=85.0,
            pore_pressure_kpa=35.0
        )

        self.assertGreater(fos_gentle, 1.3, "Gentle dry slope should be stable (FoS > 1.3).")
        self.assertLess(fos_steep, 1.2, "Steep saturated slope should be critical or unstable.")
        self.assertGreater(fos_gentle, fos_steep)

    def test_03_hydrogeological_pore_pressure(self):
        """Verify pore pressure computation with antecedent and daily rainfall."""
        res_dry = estimated_pore_pressure(0.0, 5.0, 2.0, 0.40)
        res_deluge = estimated_pore_pressure(120.0, 180.0, 2.5, 0.45)

        self.assertGreater(res_deluge["value_kpa"], res_dry["value_kpa"])
        self.assertEqual(res_deluge["pore_pressure_type"], "estimated")
        self.assertIn("label", res_deluge)

    def test_04_dataset_provenance_and_transparency(self):
        """Verify dataset provenance disclosure for scientific honesty."""
        meta = get_train_summary()
        self.assertEqual(meta["dataset_type"], "synthetic")
        self.assertFalse(meta["real_world_validated"])
        self.assertIn("synthetic_evaluation_metrics", meta)
        eval_metrics = meta["synthetic_evaluation_metrics"]
        self.assertGreater(eval_metrics["accuracy"], 0.90)
        self.assertGreater(eval_metrics["roc_auc"], 0.95)
        self.assertIn("notice", meta)

    def test_05_multilingual_alert_framework(self):
        """Verify alert templates in all 4 supported SIH languages."""
        for code, name in SUPPORTED_LANGUAGES.items():
            alert = generate_multilingual_alert(
                location="Tupul Sector",
                risk_level="CRITICAL",
                risk_score=88.5,
                lang=code
            )
            self.assertEqual(alert["language_code"], code)
            self.assertIn("Tupul", alert["subject"])
            self.assertIn("112", alert["body"], "Emergency helpline 112 must be present in body.")
            self.assertGreater(len(alert["sms_text"]), 10)

        previews = get_all_multilingual_previews()
        self.assertEqual(len(previews), 4)
        self.assertIn("as", previews)
        self.assertIn("bn", previews)
        self.assertIn("hi", previews)
        self.assertIn("en", previews)

    def test_06_citizen_report_lifecycle_and_priority(self):
        """Verify response priority and 5-tier lifecycle calculations."""
        # Critical blocked road incident -> P1 Emergency
        p1 = calculate_response_priority("CRITICAL", "BLOCKED", "Highway Washout")
        self.assertEqual(p1, "P1_EMERGENCY")

        # High single-lane incident -> P2 Urgent
        p2 = calculate_response_priority("HIGH", "SINGLE_LANE", "Active Mudflow")
        self.assertEqual(p2, "P2_URGENT")

        # Low open road -> P4 Advisory
        p4 = calculate_response_priority("LOW", "FULLY_OPEN", "Tension Cracks")
        self.assertEqual(p4, "P4_ADVISORY")

    def test_07_highway_corridors_connectivity(self):
        """Verify all 8 Northeast Highway corridors are monitored."""
        codes = [c.get("code") for c in NER_HIGHWAY_CORRIDORS]
        expected_corridors = ["NH-10", "NH-40", "NH-29", "NH-37", "NH-54", "NH-13", "NH-27", "NH-8"]
        for expected in expected_corridors:
            self.assertIn(expected, codes)

    def test_08_sensor_reading_schema(self):
        """Verify schema compatibility for future ESP32 payloads."""
        reading = SensorReading(
            device_id="ESP32-SIKKIM-01",
            section_id="S1",
            soil_moisture=65.0,
            accel_x=0.05,
            accel_y=-0.1,
            accel_z=9.81,
            rainfall_detected=True,
            rainfall_value=12.5,
            pore_pressure_kpa=48.2,
            latitude=27.3389,
            longitude=88.6065,
        )
        self.assertEqual(reading.device_id, "ESP32-SIKKIM-01")
        self.assertEqual(reading.soil_moisture, 65.0)

    def test_09_historical_disaster_catalog(self):
        """Verify historical disaster points include major Northeast events."""
        async def _check():
            data = await get_map_layers()
            events = data["historical_events"]
            event_names = " ".join(e["name"] for e in events)
            self.assertIn("Tupul", event_names)
            self.assertIn("Lhonak", event_names)
            self.assertIn("Mirik", event_names)
            self.assertIn("Mangan", event_names)
        asyncio.run(_check())

    def test_10_scientific_disclaimer_in_risk_result(self):
        """Verify RiskResult contains scientific disclaimer, model version, and dataset type."""
        async def _check():
            res = await calculate_risk_assessment("Gangtok, Sikkim", 27.3389, 88.6065)
            self.assertIsInstance(res, RiskResult)
            self.assertEqual(res.dataset_type, "synthetic")
            self.assertFalse(res.real_world_validated)
            self.assertIn("v3.0", res.model_version)
            self.assertTrue(len(res.scientific_disclaimer) > 0)
            self.assertIn("calculation_breakdown", res.model_dump())
        asyncio.run(_check())


if __name__ == "__main__":
    unittest.main()
