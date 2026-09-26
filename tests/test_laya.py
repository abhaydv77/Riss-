"""Unit tests for Laya state/question construction and response normalization."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from laya.decision import LayaResponseError, evaluate_creator, normalize_response
from laya.client import predict_batch
from laya.questions import QUESTIONS
from laya.state_builder import build_state


def mock_response():
    choices = {
        "niche_fit": "strong", "audience_fit": "partial", "geography_fit": "strong",
        "platform_fit": "strong", "budget_fit": "partial", "creator_size_fit": "strong",
        "campaign_fit": "strong", "final_decision": "KEEP",
    }
    return {"answers": {
        key: {"choice": value, "confidence": .50, "answer_confidence": .83,
              "probabilities": {value: .83, "other": .17}, "raw": True}
        for key, value in choices.items()
    }, "usage": {"input_tokens": 20, "output_tokens": 0}}


class FakeAgent:
    def __init__(self):
        self.calls = []

    def predict(self, state, questions):
        self.calls.append((state, questions))
        return mock_response()

    def predict_batch(self, states, questions, batch_size):
        self.calls.append((states, questions, batch_size))
        return [mock_response() for _ in states]


class TestLayaIntegration(unittest.TestCase):
    def setUp(self):
        self.brand = {
            "brand_id": "b01", "brand_name": "FitNova", "industry": "fitness",
            "product": "bands", "campaign_goal": "awareness", "campaign_description": "small homes",
            "target_audience": "women", "target_age_range": "18-30", "target_gender": "female",
            "target_locations": ["India"], "required_creator_niches": ["fitness"],
            "preferred_creator_niches": ["wellness"], "minimum_followers": 100,
            "maximum_followers": 1000, "creator_size_preference": "mid-tier", "budget": 1000,
            "currency": "INR", "content_types": ["workout"], "platforms": ["instagram"],
            "tone": "energetic", "mandatory_requirements": ["fitness"],
            "preferred_traits": [], "excluded_traits": [], "unused_key": "omit me",
        }
        self.creator = {
            "creator_id": "c01", "name": "Priya", "primary_niche": "fitness",
            "secondary_niches": ["wellness"], "bio": "workouts", "location": "Mumbai, India",
            "languages": ["English"], "platforms": ["instagram"], "followers": 500,
            "engagement_rate": .05, "average_views": 400, "audience_age_range": "18-30",
            "audience_gender_distribution": {"female": .8}, "audience_locations": ["India"],
            "content_types": ["workout"], "content_style": "energetic", "rate_card": "₹1-2",
            "past_brand_categories": ["fitness"], "interests": ["gym"],
            "posting_frequency": "weekly", "unused_key": "omit me",
        }

    def test_state_is_compact_and_deterministic(self):
        state = build_state(self.brand, self.creator)
        self.assertEqual(state, build_state(self.brand, self.creator))
        self.assertNotIn("unused_key", state["brand"])
        self.assertNotIn("unused_key", state["creator"])
        self.assertIn("100-1000", state["brand"])
        self.assertIn("niche fitness", state["creator"])

    def test_all_eight_questions_are_typed_choices(self):
        self.assertEqual(len(QUESTIONS), 8)
        self.assertTrue(all(q["type"] == "choice" for q in QUESTIONS.values()))
        self.assertEqual(set(QUESTIONS["final_decision"]["criteria"]), {"KEEP", "UNCERTAIN", "DROP"})

    def test_one_prediction_call_preserves_confidence_and_probabilities(self):
        agent = FakeAgent()
        result = evaluate_creator(self.brand, self.creator, agent=agent)
        self.assertEqual(len(agent.calls), 1)
        self.assertEqual(len(agent.calls[0][1]), 8)
        self.assertEqual(result["laya"]["final_decision"]["choice"], "KEEP")
        self.assertEqual(result["laya"]["final_decision"]["confidence"], .83)
        self.assertIn("probabilities", result["laya"]["niche_fit"])
        self.assertEqual(result["laya"]["raw_response"]["usage"]["input_tokens"], 20)

    def test_rejects_malformed_response(self):
        malformed = mock_response()
        del malformed["answers"]["audience_fit"]["probabilities"]
        with self.assertRaises(LayaResponseError):
            normalize_response(malformed)

    def test_sdk_batch_method_is_used_when_requested(self):
        agent = FakeAgent()
        states = [{"brand": "one"}, {"brand": "two"}]
        results = predict_batch(states, QUESTIONS, batch_size=2, agent=agent)
        self.assertEqual(len(results), 2)
        self.assertEqual(len(agent.calls), 1)
        self.assertEqual(agent.calls[0][2], 2)


if __name__ == "__main__":
    unittest.main()
