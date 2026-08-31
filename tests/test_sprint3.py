import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.models.equipment import Equipment
from src.repositories.event_repository import EventRepository
from src.repositories.errors import RepositoryDataError
from src.repositories.equipment_repository import EquipmentRepository
from src.repositories.telemetry_repository import TelemetryRepository
from src.services.alert_service import (
    STATUS_CRITICAL,
    STATUS_HEALTHY,
    STATUS_UNAVAILABLE,
    STATUS_WARNING,
    AlertService,
)
from src.services.operational_intelligence_service import OperationalIntelligenceService
from src.services.telemetry_service import TelemetryService


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

    def test_thresholds_are_preserved(self):
        self.assertEqual(self.service.evaluate_temperature(70).status, STATUS_HEALTHY)
        self.assertEqual(self.service.evaluate_temperature(71).status, STATUS_WARNING)
        self.assertEqual(self.service.evaluate_temperature(86).status, STATUS_CRITICAL)
        self.assertEqual(self.service.evaluate_vibration(4.5).status, STATUS_HEALTHY)
        self.assertEqual(self.service.evaluate_vibration(5.0).status, STATUS_WARNING)
        self.assertEqual(self.service.evaluate_vibration(7.1).status, STATUS_CRITICAL)
        self.assertEqual(self.service.evaluate_current(10.0, 10.0).status, STATUS_HEALTHY)
        self.assertEqual(self.service.evaluate_current(11.0, 10.0).status, STATUS_WARNING)
        self.assertEqual(self.service.evaluate_current(11.6, 10.0).status, STATUS_CRITICAL)

    def test_nan_is_unavailable_and_never_critical(self):
        result = self.service.evaluate_all(
            {"temperatura_c": float("nan"), "vibracao_mm_s": 3.2, "corrente_a": 24},
            28.5,
        )
        self.assertEqual(result["temperatura"].status, STATUS_UNAVAILABLE)
        self.assertEqual(result["geral"], STATUS_UNAVAILABLE)


class Sprint3JourneyTests(unittest.TestCase):
    def setUp(self):
        self.equipment = make_equipment()
        self.intelligence = OperationalIntelligenceService()
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.telemetry = TelemetryService(
            TelemetryRepository(root / "telemetry_seed.csv", root / "runtime" / "telemetry.csv")
        )
        self.events = EventRepository(root / "event_seed.csv", root / "runtime" / "events.csv")

    def tearDown(self):
        self.tmp.cleanup()

    def test_baseline_reading_is_healthy_with_current_timestamp(self):
        reading = self.telemetry.append_demo_reading(self.equipment, scenario="baseline")
        snapshot = self.intelligence.analyze(self.equipment, reading)
        reading_time = datetime.fromisoformat(snapshot.timestamp)
        self.assertEqual(snapshot.status, STATUS_HEALTHY)
        self.assertEqual(snapshot.source, "demo_sprint3")
        self.assertEqual(snapshot.analytics_provider, "rules_analytics")
        self.assertEqual(snapshot.nlp_provider, "mock_nlp")
        self.assertFalse(snapshot.is_stale)
        self.assertTrue(snapshot.reading_id)
        self.assertTrue(snapshot.inference_id)
        self.assertLess(abs((datetime.now() - reading_time).total_seconds()), 5)

    def test_update_creates_critical_reading_and_exactly_one_transition_event(self):
        baseline = self.intelligence.analyze(
            self.equipment,
            self.telemetry.append_demo_reading(self.equipment, scenario="baseline"),
        )
        critical = self.intelligence.analyze(
            self.equipment,
            self.telemetry.append_demo_reading(self.equipment, scenario="critical"),
        )
        event = self.intelligence.build_transition_event(critical, previous_status=baseline.status)
        self.assertEqual(critical.status, STATUS_CRITICAL)
        self.assertEqual(critical.dominant_metric, "Vibração")
        self.assertEqual(critical.dominant_value, "7.80 mm/s")
        self.assertIn("rolamentos", critical.recommendation.lower())
        self.assertTrue(self.events.append_if_new(event))
        self.assertFalse(self.events.append_if_new(event))
        stored = self.events.list_recent(include_seed=False)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].status_before, STATUS_HEALTHY)
        self.assertEqual(stored[0].status_after, STATUS_CRITICAL)
        self.assertEqual(stored[0].reading_id, critical.reading_id)
        self.assertEqual(stored[0].inference_id, critical.inference_id)

    def test_rerun_with_same_critical_snapshot_does_not_create_event(self):
        critical = self.intelligence.analyze(
            self.equipment,
            self.telemetry.append_demo_reading(self.equipment, scenario="critical"),
        )
        self.assertEqual(critical.status, STATUS_CRITICAL)
        self.assertIsNone(
            self.intelligence.build_transition_event(critical, previous_status=critical.status)
        )
        self.assertEqual(self.events.list_recent(include_seed=False), [])

    def test_recovery_from_critical_to_healthy_creates_one_event(self):
        critical = self.intelligence.analyze(
            self.equipment,
            self.telemetry.append_demo_reading(self.equipment, scenario="critical"),
        )
        recovered = self.intelligence.analyze(
            self.equipment,
            self.telemetry.append_demo_reading(self.equipment, scenario="baseline"),
        )
        event = self.intelligence.build_transition_event(recovered, previous_status=critical.status)
        self.assertEqual(recovered.status, STATUS_HEALTHY)
        self.assertIsNotNone(event)
        self.assertTrue(self.events.append_if_new(event))
        self.assertEqual(self.events.list_recent(include_seed=False)[0].status_after, STATUS_HEALTHY)

    def test_invalid_reading_becomes_unavailable(self):
        snapshot = self.intelligence.analyze(
            self.equipment,
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "tag": self.equipment.tag,
                "temperatura_c": "invalid",
                "vibracao_mm_s": 3.2,
                "corrente_a": 24.0,
                "rotacao_rpm": 1735,
                "reading_id": "invalid-reading",
                "source": "demo_sprint3",
            },
        )
        self.assertEqual(snapshot.status, STATUS_UNAVAILABLE)
        self.assertEqual(snapshot.dominant_value, "Indisponível")
        self.assertIn("não possui dados válidos", snapshot.summary)

    def test_administrative_status_does_not_control_analytic_snapshot(self):
        inactive = make_equipment()
        inactive.status_operacional = "Inativo"
        snapshot = self.intelligence.analyze(
            inactive,
            self.telemetry.generate_demo_reading(inactive, scenario="baseline"),
        )
        self.assertEqual(snapshot.status, STATUS_HEALTHY)

    def test_runtime_writes_do_not_modify_seed_history(self):
        seed_path = Path(self.tmp.name) / "telemetry_seed.csv"
        self.telemetry.append_demo_reading(self.equipment, scenario="baseline")
        self.assertFalse(seed_path.exists())
        runtime_history = self.telemetry.repository.read_history()
        self.assertEqual(len(runtime_history), 1)
        self.assertEqual(runtime_history.iloc[0]["source"], "demo_sprint3")


class RepositorySafetyTests(unittest.TestCase):
    def test_invalid_equipment_json_is_reported_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            equipment_path = Path(tmp) / "equipments.json"
            invalid_content = "{invalid json"
            equipment_path.write_text(invalid_content, encoding="utf-8")
            with self.assertRaises(RepositoryDataError):
                EquipmentRepository(equipment_path).get_all()
            self.assertEqual(equipment_path.read_text(encoding="utf-8"), invalid_content)

    def test_invalid_telemetry_csv_is_reported_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed = Path(tmp) / "telemetry.csv"
            invalid_content = '"unterminated\n'
            seed.write_text(invalid_content, encoding="utf-8")
            repository = TelemetryRepository(seed, Path(tmp) / "runtime" / "telemetry.csv")
            with self.assertRaises(RepositoryDataError):
                repository.read_history()
            self.assertEqual(seed.read_text(encoding="utf-8"), invalid_content)

    def test_invalid_event_csv_is_reported_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed = Path(tmp) / "events.csv"
            invalid_content = '"unterminated\n'
            seed.write_text(invalid_content, encoding="utf-8")
            repository = EventRepository(seed, Path(tmp) / "runtime" / "events.csv")
            with self.assertRaises(RepositoryDataError):
                repository.list_recent()
            self.assertEqual(seed.read_text(encoding="utf-8"), invalid_content)


if __name__ == "__main__":
    unittest.main()
