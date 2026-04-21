import json
from urllib import request

from app.core.config import Settings


class AIClientError(Exception):
    pass


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyze(self, payload: dict) -> str:
        if not self.settings.AI_AGENT_API_KEY:
            raise AIClientError("AI_AGENT_API_KEY missing")
        body = {
            "model": self.settings.AI_AGENT_MODEL,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a manufacturing post-processor analysis agent. "
                        "Return ONLY strict JSON with keys: output_summary, output_structured, "
                        "knowledge_title, knowledge_symptom, knowledge_cause, knowledge_resolution."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        }
        raw = json.dumps(body).encode("utf-8")
        req = request.Request(
            self.settings.AI_AGENT_BASE_URL,
            data=raw,
            headers={
                "Authorization": f"Bearer {self.settings.AI_AGENT_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.settings.AI_AGENT_TIMEOUT_SECONDS) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
        except Exception as ex:
            raise AIClientError(f"AI request failed: {ex}") from ex
        try:
            return parsed["choices"][0]["message"]["content"]
        except Exception as ex:
            raise AIClientError("Unexpected AI response format") from ex

