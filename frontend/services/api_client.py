"""Único módulo do front autorizado a realizar chamadas HTTP."""
import os
from urllib.parse import quote
from pathlib import Path

import requests
from dotenv import load_dotenv

FRONTEND_DIR = Path(__file__).resolve().parents[1]


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self, token=None, base_url=None, timeout=None):
        load_dotenv(FRONTEND_DIR / ".env", override=False)
        self.base_url = (base_url or os.getenv("API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout if timeout is not None else float(os.getenv("API_TIMEOUT_SECONDS", "15"))
        if not 0 < self.timeout <= 120:
            raise ValueError("API_TIMEOUT_SECONDS deve estar entre 0 e 120 segundos.")
        self.token = token

    def _request(self, method, path, payload=None):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = requests.request(method, f"{self.base_url}{path}", json=payload,
                                        headers=headers, timeout=self.timeout)
        except requests.Timeout as error:
            raise APIError("A API demorou para responder. Atualize o histórico antes de reenviar: "
                           "a operação pode ter sido concluída.") from error
        except requests.ConnectionError as error:
            raise APIError("Não foi possível conectar à API. Verifique se o backend está ligado "
                           "e confira API_URL. Atualize o histórico antes de reenviar.") from error
        except requests.RequestException as error:
            raise APIError("Falha na comunicação com a API. Verifique a configuração e tente novamente.") from error
        if not response.ok:
            defaults = {
                401: "Sessão inválida ou expirada. Entre novamente.",
                404: "Conversa não encontrada. Selecione outra ou crie uma nova.",
                409: "Esse nome de usuário já está em uso.",
                422: "Confira os dados: usuário com 3 a 40 caracteres, senha com 8 a 128 e texto com 1 a 4000.",
                503: "O modelo ou armazenamento está indisponível. Tente novamente mais tarde.",
            }
            if path.startswith("/motor/"):
                defaults.update({404: "Equipamento não encontrado.", 409: "Essa TAG já está cadastrada.",
                    422: "Confira os campos obrigatórios, os valores maiores que zero e a confirmação do cadastro.",
                    503: "Os dados operacionais estão indisponíveis. Verifique o backend e tente novamente."})
            # Não exibir corpo arbitrário/HTML ou dados internos de erros do servidor.
            raise APIError(defaults.get(response.status_code, "A API não conseguiu concluir a operação."),
                           response.status_code)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise APIError("A API retornou uma resposta inválida. Confira API_URL.") from error

    def health(self):
        return self._request("GET", "/health")

    def register(self, username, password):
        return self._request("POST", "/auth/register", {"usuario": username, "senha": password})

    def login(self, username, password):
        return self._request("POST", "/auth/login", {"usuario": username, "senha": password})

    def logout(self):
        return self._request("POST", "/auth/logout")

    def list_conversations(self):
        return self._request("GET", "/conversas")

    def create_conversation(self):
        return self._request("POST", "/conversas", {})

    def get_conversation(self, conversation_id):
        return self._request("GET", f"/conversas/{conversation_id}")

    def send_message(self, conversation_id, content):
        return self._request("POST", f"/conversas/{conversation_id}/mensagens", {"conteudo": content})

    def me(self):
        return self._request("GET", "/auth/me")

    def fleet(self):
        return self._request("GET", "/motor/equipamentos")

    def register_equipment(self, payload):
        return self._request("POST", "/motor/equipamentos", payload)

    def motor_panel(self, include_seed=False):
        return self._request("GET", f"/motor/painel?include_seed={str(include_seed).lower()}")

    def motor_detail(self, tag):
        return self._request("GET", f"/motor/equipamentos/{quote(tag, safe='')}")

    def motor_refresh(self, tag, demo=False):
        action = "demo" if demo else "leituras"
        return self._request("POST", f"/motor/equipamentos/{quote(tag, safe='')}/{action}")

    def raw_sensors(self, tag):
        return self._request("GET", f"/motor/equipamentos/{quote(tag, safe='')}/sensores")
