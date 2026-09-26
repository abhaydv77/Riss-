"""Evaluate one brand/creator pair with a single multi-question Laya call."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from laya.client import MODEL_ID, LayaClientError, predict
from laya.questions import QUESTIONS
from laya.state_builder import build_state

DECISION_OPTIONS = {
    "niche_fit": {"strong", "partial", "none"},
    "audience_fit": {"strong", "partial", "none"},
    "geography_fit": {"strong", "partial", "none"},
    "platform_fit": {"strong", "partial", "none"},
    "budget_fit": {"strong", "partial", "none"},
    "creator_size_fit": {"strong", "partial", "none"},
    "campaign_fit": {"strong", "partial", "none"},
    "final_decision": {"KEEP", "UNCERTAIN", "DROP"},
}


class LayaResponseError(ValueError):
    """Raised when the SDK response is malformed or outside the schema."""

    def __init__(self, message: str, raw_response=None):
        super().__init__(message)
        self.raw_response = raw_response


def normalize_response(raw: dict) -> dict[str, dict[str, Any]]:
    """Validate all returned choices while retaining confidence and probabilities."""
    answers = raw.get("answers") if isinstance(raw, dict) else None
    if not isinstance(answers, dict):
        raise LayaResponseError("SDK response has no answers object")
    normalized = {}
    for question_id, options in DECISION_OPTIONS.items():
        answer = answers.get(question_id)
        if not isinstance(answer, dict):
            raise LayaResponseError(f"SDK response is missing {question_id!r}")
        choice = answer.get("choice")
        if choice not in options:
            raise LayaResponseError(f"{question_id} returned invalid choice {choice!r}")
        # Current SDKs expose answer_confidence as calibrated confidence in the
        # selected class; `confidence` is normalized entropy for choice answers.
        confidence = answer.get("answer_confidence", answer.get("confidence"))
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise LayaResponseError(f"{question_id} returned invalid confidence {confidence!r}")
        probabilities = answer.get("probabilities")
        if not isinstance(probabilities, dict):
            raise LayaResponseError(f"{question_id} returned no probability distribution")
        normalized[question_id] = {
            "choice": choice,
            "confidence": float(confidence),
            "sdk_confidence": answer.get("confidence"),
            "probabilities": probabilities,
            "raw_answer": answer,
        }
    return normalized


def evaluate_creator(brand: dict, creator: dict, agent=None) -> dict:
    """Build state, call Laya once for eight decisions, and return research data."""
    state = build_state(brand, creator)
    questions = deepcopy(QUESTIONS)
    raw = None
    try:
        raw = predict(state, questions, agent=agent)
        return prediction_from_raw(brand, creator, raw, state=state, questions=questions)
    except LayaClientError:
        raise
    except LayaResponseError as exc:
        exc.raw_response = raw
        raise
    except Exception as exc:
        raise LayaResponseError(str(exc)) from exc
    raise AssertionError("unreachable")


def prediction_from_raw(brand: dict, creator: dict, raw: dict, state: dict | None = None, questions: dict | None = None) -> dict:
    """Normalize one per-state result returned by predict or predict_batch."""
    normalized = normalize_response(raw)
    return {
        "brand_id": brand["brand_id"],
        "creator_id": creator["creator_id"],
        "state": state if state is not None else build_state(brand, creator),
        "questions": questions if questions is not None else deepcopy(QUESTIONS),
        "laya": {**normalized, "raw_response": raw},
        "model": MODEL_ID,
    }


__all__ = ["evaluate_creator", "prediction_from_raw", "normalize_response", "LayaResponseError"]
