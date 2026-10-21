from app.core.errors import AppError


class ChatService:
    def __init__(self, repository, provider):
        self.repository = repository
        self.provider = provider

    def health(self):
        return {"status": "degraded" if self.provider.name == "unavailable" else "ok",
                "provider": self.provider.name, "modelo": self.provider.model}

    def list(self, user_id):
        return self.repository.list(user_id)

    def create(self, user_id, data):
        return self.repository.create(user_id, data.titulo)

    def get(self, user_id, conversation_id):
        result = self.repository.get(user_id, conversation_id)
        if not result:
            raise AppError(404, "Conversa não encontrada.")
        return result

    def send(self, user_id, conversation_id, data):
        history = self.get(user_id, conversation_id)["mensagens"]
        answer = self.provider.generate(history, data.conteudo)
        # Falhas no provider não gravam meia interação no histórico.
        pair = self.repository.append_pair(user_id, conversation_id, data.conteudo, answer)
        if not pair:
            raise AppError(404, "Conversa não encontrada.")
        return {"conversa_id": conversation_id, "mensagem_usuario": pair[0], "resposta": pair[1],
                "modelo": self.provider.model, "criado_em": pair[1]["criado_em"]}
