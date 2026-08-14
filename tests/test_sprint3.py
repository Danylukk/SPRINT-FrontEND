import tempfile
import unittest
from pathlib import Path

from src.models.equipment import Equipment
from src.repositories.event_repository import EventRepository
from src.services.alert_service import STATUS_CRITICAL, STATUS_HEALTHY, STATUS_WARNING, AlertService
from src.services.operational_intelligence_service import OperationalIntelligenceService


def make_equipment() -> Equipment:
    return Equipment(
        tag="MTR-001",
        modelo="WEG W22 IR3",
        fabricante="WEG",
        potencia=15.0,
        unidade_potencia="CV",
        tensao=380.0,
        corrente_nominal=28.5,
        rotacao_nominal=1750.0,
        local_instalacao="Linha de Produção A",
        status_operacional="Operacional",
        observacoes="Motor principal da esteira de alimentação.",
    )


class AlertServiceRegressionTests(unittest.TestCase):
    def setUp(self):
        self.service = AlertService()

    def test_temperature_thresholds_are_preserved(self):
        self.assertEqual(self.service.evaluate_temperature(70).status, STATUS_HEALTHY)
        self.assertEqual(self.service.evaluate_temperature(71).status, STATUS_WARNING)
        self.assertEqual(self.service.evaluate_temperature(86).status, STATUS_CRITICAL)

    def test_vibration_thresholds_are_preserved(self):
        self.assertEqual(self.service.evaluate_vibration(4.5).status, STATUS_HEALTHY)
        self.assertEqual(self.service.evaluate_vibration(5.0).status, STATUS_WARNING)
        self.assertEqual(self.service.evaluate_vibration(7.1).status, STATUS_CRITICAL)

    def test_current_thresholds_are_preserved(self):
        nominal = 10.0
        self.assertEqual(self.service.evaluate_current(10.0, nominal).status, STATUS_HEALTHY)
        self.assertEqual(self.service.evaluate_current(11.0, nominal).status, STATUS_WARNING)
        self.assertEqual(self.service.evaluate_current(11.6, nominal).status, STATUS_CRITICAL)


class OperationalIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.equipment = make_equipment()
        self.service = OperationalIntelligenceService()
        self.baseline = {
            "tag": self.equipment.tag,
            "temperatura_c": 61.0,
            "vibracao_mm_s": 3.2,
            "corrente_a": 24.0,
            "rotacao_rpm": 1735.0,
        }

    def test_baseline_is_healthy(self):
        snapshot = self.service.analyze(self.equipment, self.baseline)
        self.assertEqual(snapshot.status, STATUS_HEALTHY)
        self.assertEqual(snapshot.source, "rules_fallback")
        self.assertEqual(snapshot.nlp_provider, "mock_nlp")
        self.assertIn("baseline operacional", snapshot.summary)

    def test_demo_update_produces_critical_alert(self):
        snapshot = self.service.analyze(self.equipment, self.baseline, simulate_anomaly=True)
        self.assertEqual(snapshot.status, STATUS_CRITICAL)
        self.assertEqual(snapshot.dominant_metric, "Vibração")
        self.assertEqual(snapshot.dominant_value, "7.80 mm/s")
        self.assertEqual(snapshot.source, "simulation")
        self.assertIn("rolamentos", snapshot.recommendation.lower())
        self.assertIn("MTR-001", snapshot.summary)

    def test_input_reading_is_not_mutated(self):
        original = dict(self.baseline)
        self.service.analyze(self.equipment, self.baseline, simulate_anomaly=True)
        self.assertEqual(self.baseline, original)

    def test_warning_snapshot_has_medium_severity_and_preventive_action(self):
        warning = dict(self.baseline)
        warning["vibracao_mm_s"] = 5.5
        snapshot = self.service.analyze(self.equipment, warning)
        self.assertEqual(snapshot.status, STATUS_WARNING)
        self.assertEqual(snapshot.severity, "Média")
        self.assertIn("acompanhar", snapshot.recommendation.lower())

    def test_demo_keeps_non_dominant_metrics_below_critical_limits(self):
        snapshot = self.service.analyze(self.equipment, self.baseline, simulate_anomaly=True)
        self.assertLessEqual(float(snapshot.reading["temperatura_c"]), 85.0)
        self.assertLessEqual(float(snapshot.reading["corrente_a"]), self.equipment.corrente_nominal * 1.15)

    def test_transition_event_contains_before_and_after_states(self):
        snapshot = self.service.analyze(self.equipment, self.baseline, simulate_anomaly=True)
        event = self.service.build_transition_event(snapshot, previous_status=STATUS_HEALTHY)
        self.assertEqual(event.status_before, STATUS_HEALTHY)
        self.assertEqual(event.status_after, STATUS_CRITICAL)
        self.assertEqual(event.tag, "MTR-001")
        self.assertEqual(event.source, "simulation")


class EventRepositoryTests(unittest.TestCase):
    def test_event_is_persisted_and_reloaded(self):
        equipment = make_equipment()
        service = OperationalIntelligenceService()
        snapshot = service.analyze(
            equipment,
            {"temperatura_c": 61, "vibracao_mm_s": 3.2, "corrente_a": 24, "rotacao_rpm": 1735},
            simulate_anomaly=True,
        )
        event = service.build_transition_event(snapshot, previous_status=STATUS_HEALTHY)

        with tempfile.TemporaryDirectory() as tmp:
            repo = EventRepository(Path(tmp) / "event_history.csv")
            self.assertEqual(repo.list_recent(), [])
            repo.append(event)
            loaded = repo.list_recent()
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].tag, event.tag)
            self.assertEqual(loaded[0].status_after, STATUS_CRITICAL)
            self.assertEqual(loaded[0].summary, event.summary)


if __name__ == "__main__":
    unittest.main()
