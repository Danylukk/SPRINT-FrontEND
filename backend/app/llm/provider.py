import unicodedata

from app.core.errors import AppError


class ModelProvider:
    """Único ponto de acesso ao bot. Nenhum serviço externo é chamado."""

    def __init__(self, provider: str):
        self.name = provider
        self.model = {"simulated": "motor-assistant-rules-v1", "echo": "echo-v1",
                      "unavailable": "unavailable"}[provider]

    def generate(self, history, content, context=None):
        if self.name == "unavailable":
            raise AppError(503, "O modelo está indisponível. Tente novamente mais tarde.")
        if self.name == "echo":
            return f"[Bot eco simulado] Você escreveu: {content}"
        if context:
            item, snapshot = context["equipamento"], context["snapshot"]
            freshness = "Dados desatualizados" if snapshot["is_stale"] else "Leitura atual"
            return (f"**Consulta por regras · {item['tag']}**\n\n"
                    f"Modelo: {item['modelo']} · Área: {item['local_instalacao']}.\n\n"
                    f"Estado analítico: **{snapshot['status']}**. {freshness}.\n\n"
                    f"{snapshot['summary']}\n\n{snapshot['recommendation']}\n\n"
                    f"Fonte: {snapshot['source']} · Leitura: {snapshot['timestamp']} · "
                    f"ID: {snapshot['reading_id']}.\n\n"
                    "Dados da API do sistema, sem sensores reais. Resposta determinística, sem LLM.")
        normalized = unicodedata.normalize("NFKD", content.lower()).encode("ascii", "ignore").decode()
        if "api" in normalized or "fastapi" in normalized:
            answer = ("Uma API é um contrato de comunicação entre programas. Neste CP6, o Streamlit "
                      "envia requests HTTP para o FastAPI; a API valida o token e os dados, consulta "
                      "o SQLite e devolve JSON. Consulte /docs para explorar os endpoints.")
        elif "vibr" in normalized or "motor" in normalized:
            answer = ("No Motor Digital Twin, a vibração é uma leitura usada pelas regras de estado "
                      "das sprints anteriores. Confira a TAG, a origem e a data da leitura no painel "
                      "operacional. Este chat não consulta sensores nem executa diagnósticos reais.")
        elif "persist" in normalized or "histor" in normalized:
            answer = ("As conversas e mensagens ficam no SQLite da API. Ao retomar uma conversa, "
                      "o front lê o histórico por HTTP. Reiniciar a API preserva os dados no mesmo "
                      "DATABASE_PATH; trocar a conta mostra somente as conversas daquele usuário.")
        elif "autent" in normalized or "token" in normalized or "senha" in normalized:
            answer = ("O login verifica um hash PBKDF2 da senha e emite um token opaco com validade. "
                      "A API identifica o usuário por esse token e verifica o dono de cada conversa. "
                      "O logout revoga a sessão no servidor.")
        else:
            answer = (f"Recebi: {content}\n\nPosso demonstrar respostas sobre API, autenticação, "
                      "persistência e vibração de motores. A qualidade conversacional não faz parte "
                      "da avaliação: este bot utiliza regras, sem um LLM real.")
        turns = sum(item["papel"] == "user" for item in history)
        return f"**Assistente simulado · Motor Digital Twin**\n\n{answer}\n\nInteração {turns + 1} nesta conversa."
