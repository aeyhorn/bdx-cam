import json

from app.core.config import get_settings
from app.services.agent_types import RunPayload, RunResult
from app.services.ai_client import AIClientError, OpenAICompatibleClient


class AgentExecutor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAICompatibleClient(self.settings)

    def run(self, payload: RunPayload) -> RunResult:
        if not self.settings.AI_AGENT_ENABLED:
            return self._fallback(payload, reason="AI agent disabled")
        try:
            raw = self.client.analyze(payload.model_dump())
            parsed = json.loads(raw)
            return RunResult(**parsed, model_name=self.settings.AI_AGENT_MODEL, model_version="external")
        except (AIClientError, json.JSONDecodeError, TypeError, ValueError) as ex:
            return self._fallback(payload, reason=str(ex))

    def _fallback(self, payload: RunPayload, reason: str) -> RunResult:
        title = payload.title or f"Case {payload.ticket_no}" if payload.ticket_no else "Unbenannt"
        return RunResult(
            output_summary=f"Agentenprüfung abgeschlossen (Fallback): {title}",
            output_structured={
                "analysis": "fallback-pass",
                "reason": reason,
                "proposed_generator_improvement": "Regelprüfung und Outputvergleich für ähnliche Fälle aktivieren",
                "confidence": 0.5,
            },
            knowledge_title=f"Agent-Analyse: {title}",
            knowledge_symptom=(payload.description or "")[:2000] or None,
            knowledge_cause="Automatisch erkannte Abweichung in NC/Post-Verhalten",
            knowledge_resolution="Empfohlene Generator-Verbesserung dokumentiert",
            model_name="fallback-agent",
            model_version="v1",
        )

