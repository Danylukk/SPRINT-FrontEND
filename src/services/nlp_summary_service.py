from src.services.alert_service import STATUS_CRITICAL, STATUS_HEALTHY, STATUS_WARNING


class NLPSummaryService:
    """Adapter textual para a Sprint 3.

    Hoje usa templates determinísticos (mock NLP). A interface consome apenas este
    contrato; uma futura integração com NLP real pode substituir esta implementação
    sem alterar a página do Streamlit.
    """

    provider = "mock_nlp"

    def build_summary(self, *, tag: str, status: str, dominant_metric: str, message: str) -> str:
        if status == STATUS_CRITICAL:
            return (
                f"O ativo {tag} apresenta desvio operacional crítico relacionado a {dominant_metric}. "
                f"{message} O evento deve ser priorizado pela equipe de manutenção."
            )
        if status == STATUS_WARNING:
            return (
                f"O ativo {tag} apresenta comportamento de atenção em {dominant_metric}. "
                f"{message} Recomenda-se acompanhar a tendência antes que o desvio evolua."
            )
        return (
            f"O ativo {tag} permanece dentro do baseline operacional nas variáveis avaliadas. "
            "Não há anomalia prioritária no momento."
        )

    def build_recommendation(self, *, status: str, dominant_metric: str) -> str:
        metric = dominant_metric.lower()
        if status == STATUS_CRITICAL:
            if "vibra" in metric:
                return "Priorizar inspeção mecânica, verificando rolamentos, fixação e possível desalinhamento."
            if "temper" in metric:
                return "Priorizar inspeção térmica, ventilação, carga e condições de refrigeração do ativo."
            if "corrente" in metric:
                return "Verificar sobrecarga, alimentação elétrica e condição mecânica antes de manter a operação."
            return "Priorizar inspeção do equipamento e validar a condição com a equipe de manutenção."
        if status == STATUS_WARNING:
            return "Acompanhar a tendência, comparar com o histórico recente e programar verificação preventiva."
        return "Manter monitoramento de rotina e comparar novas leituras com o baseline operacional."
