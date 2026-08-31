from dataclasses import dataclass
from math import isfinite


STATUS_HEALTHY = "Saudável"
STATUS_WARNING = "Atenção"
STATUS_CRITICAL = "Crítico"
STATUS_UNAVAILABLE = "Indisponível"


@dataclass(frozen=True)
class AlertResult:
    status: str
    message: str


class AlertService:
    STATUS_ORDER = {
        STATUS_UNAVAILABLE: -1,
        STATUS_HEALTHY: 0,
        STATUS_WARNING: 1,
        STATUS_CRITICAL: 2,
    }

    def evaluate_temperature(self, temperatura_c: float) -> AlertResult:
        if not self._is_valid_number(temperatura_c):
            return AlertResult(STATUS_UNAVAILABLE, "Temperatura indisponível para análise.")
        if temperatura_c <= 70:
            return AlertResult(STATUS_HEALTHY, "Temperatura dentro da faixa saudável.")
        if temperatura_c <= 85:
            return AlertResult(STATUS_WARNING, "Temperatura em atenção. Acompanhar tendência.")
        return AlertResult(STATUS_CRITICAL, "Temperatura crítica. Recomenda-se inspeção.")

    def evaluate_vibration(self, vibracao_mm_s: float) -> AlertResult:
        if not self._is_valid_number(vibracao_mm_s):
            return AlertResult(STATUS_UNAVAILABLE, "Vibração indisponível para análise.")
        if vibracao_mm_s <= 4.5:
            return AlertResult(STATUS_HEALTHY, "Vibração dentro da faixa saudável.")
        if vibracao_mm_s <= 7.0:
            return AlertResult(STATUS_WARNING, "Vibração em atenção. Verificar rolamentos e fixação.")
        return AlertResult(STATUS_CRITICAL, "Vibração crítica. Priorizar análise mecânica.")

    def evaluate_current(self, corrente_a: float, corrente_nominal: float) -> AlertResult:
        if not self._is_valid_number(corrente_a):
            return AlertResult(STATUS_UNAVAILABLE, "Corrente indisponível para análise.")
        if not self._is_valid_number(corrente_nominal) or corrente_nominal <= 0:
            return AlertResult(STATUS_UNAVAILABLE, "Corrente nominal indisponível para comparação.")

        percentual = (corrente_a / corrente_nominal) * 100
        if percentual <= 100:
            return AlertResult(STATUS_HEALTHY, "Corrente dentro da faixa nominal.")
        if percentual <= 115:
            return AlertResult(STATUS_WARNING, "Corrente acima do nominal. Acompanhar carga.")
        return AlertResult(STATUS_CRITICAL, "Corrente crítica. Verificar sobrecarga.")

    def evaluate_all(self, reading: dict, corrente_nominal: float) -> dict[str, AlertResult | str]:
        temperature = self.evaluate_temperature(self._to_float(reading.get("temperatura_c")))
        vibration = self.evaluate_vibration(self._to_float(reading.get("vibracao_mm_s")))
        current = self.evaluate_current(self._to_float(reading.get("corrente_a")), corrente_nominal)
        statuses = [temperature.status, vibration.status, current.status]
        overall = (
            STATUS_UNAVAILABLE
            if STATUS_UNAVAILABLE in statuses
            else max(statuses, key=lambda status: self.STATUS_ORDER[status])
        )

        return {
            "temperatura": temperature,
            "vibracao": vibration,
            "corrente": current,
            "geral": overall,
        }

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    @staticmethod
    def _is_valid_number(value: float) -> bool:
        return isfinite(value)
