import json
from dataclasses import dataclass
from sqlite3 import Connection

import httpx
from backend.app.core.config import get_settings


@dataclass(frozen=True)
class ModerationDecision:
    decision: str
    scores: dict[str, float | str]

    @property
    def allowed(self) -> bool:
        return self.decision in {"allow", "review"}


SUSPICIOUS_TERMS = {"crypto", "airdrop", "seed phrase", "wire money", "gift card"}


async def moderate_text(text: str) -> ModerationDecision:
    settings = get_settings()
    lowered = text.lower()
    local_scores: dict[str, float | str] = {
        "spam": 0.4 if len(text) > 1200 else 0.0,
        "scam": 0.7 if any(term in lowered for term in SUSPICIOUS_TERMS) else 0.0,
        "toxicity": 0.0,
        "harassment": 0.0,
    }
    if settings.moderation_provider == "disabled" or not settings.moderation_api_url:
        decision = "review" if max(float(v) for v in local_scores.values()) >= 0.7 else "allow"
        return ModerationDecision(decision=decision, scores=local_scores)

    headers = {"Authorization": f"Bearer {settings.moderation_api_key}"}
    payload = {
        "text": text,
        "checks": ["toxicity", "scam", "spam", "harassment"],
    }
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.post(settings.moderation_api_url, json=payload, headers=headers)
        response.raise_for_status()
    data = response.json()
    decision = data.get("decision", "review")
    scores = data.get("scores", {})
    return ModerationDecision(decision=decision, scores=scores | local_scores)


def log_moderation(
    db: Connection,
    user_id: int,
    content_type: str,
    content_id: int | None,
    decision: ModerationDecision,
) -> None:
    db.execute(
        """
        INSERT INTO moderation_logs (user_id, content_type, content_id, provider, decision, scores_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            content_type,
            content_id,
            get_settings().moderation_provider,
            decision.decision,
            json.dumps(decision.scores),
        ),
    )
    if float(decision.scores.get("scam", 0.0)) >= 0.7:
        db.execute(
            """
            INSERT INTO trust_scores (user_id, score, scam_signals)
            VALUES (?, 40, 1)
            ON CONFLICT(user_id) DO UPDATE SET
              score = MAX(0, score - 10),
              scam_signals = scam_signals + 1,
              updated_at = CURRENT_TIMESTAMP
            """,
            (user_id,),
        )
    db.commit()
