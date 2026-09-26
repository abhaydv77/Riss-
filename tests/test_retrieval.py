"""Tests for the retrieval layer."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from retrieval.embeddings import build_creator_text, build_brief_text
from retrieval.chroma_store import add_creators, get_collection, load_creators, load_brands, get_creator_by_id
from retrieval.retrieve import retrieve_creators


class TestEmbeddings(unittest.TestCase):
    def test_build_creator_text_includes_niche(self):
        creator = {"primary_niche": "fitness", "secondary_niches": ["sports"], "name": "Test Creator",
                    "bio": "A test bio.", "location": "Test City", "languages": ["English"],
                    "platforms": ["instagram"], "followers": 10000, "engagement_rate": 0.05,
                    "average_views": 5000, "audience_age_range": "25-34",
                    "audience_gender_distribution": {"female": 0.7}, "audience_locations": ["US"],
                    "content_types": ["workout"], "content_style": "energetic",
                    "rate_card": "₹5,000–₹15,000", "past_brand_categories": ["sports"],
                    "interests": ["fitness"], "posting_frequency": "daily"}
        text = build_creator_text(creator)
        self.assertIn("fitness", text)
        self.assertIn("Test Creator", text)
        self.assertIn("Test City", text)

    def test_build_brief_text_includes_goal(self):
        brand = {"brand_name": "TestBrand", "industry": "Fitness", "campaign_title": "Test Campaign",
                 "campaign_goal": "Test goal", "product": "Test product",
                 "target_audience": "Young women", "target_age_range": "18-30",
                 "target_gender": "female", "target_locations": ["US"],
                 "required_creator_niches": ["fitness"], "preferred_creator_niches": ["wellness"],
                 "content_types": ["workout"], "platforms": ["instagram"], "tone": "energetic",
                 "mandatory_requirements": ["must have fitness"], "preferred_traits": ["motivational"],
                 "excluded_traits": ["luxury"], "campaign_description": "Test description"}
        text = build_brief_text(brand)
        self.assertIn("TestBrand", text)
        self.assertIn("Test Campaign", text)
        self.assertIn("Test goal", text)
        self.assertIn("fitness", text)


class TestChromaStore(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        import chromadb
        from retrieval.config import COLLECTION_NAME
        self.client = chromadb.PersistentClient(path=self.tmpdir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_add_creators(self) -> None:
        creators = [{"creator_id": "c001", "primary_niche": "fitness", "name": "Test",
                      "location": "Test", "languages": ["English"], "platforms": ["instagram"],
                      "followers": 10000, "engagement_rate": 0.05, "average_views": 5000,
                      "audience_age_range": "25-34", "audience_gender_distribution": {"female": 0.7},
                      "audience_locations": ["US"], "content_types": ["workout"],
                      "content_style": "energetic", "rate_card": "test",
                      "past_brand_categories": ["sports"], "interests": ["fitness"],
                      "posting_frequency": "daily"}]
        add_creators(creators, collection=self.collection)
        self.assertEqual(self.collection.count(), 1)

    def test_no_duplicate_on_reload(self) -> None:
        creators = [{"creator_id": "c001", "primary_niche": "fitness", "name": "Test",
                      "location": "Test", "languages": ["English"], "platforms": ["instagram"],
                      "followers": 10000, "engagement_rate": 0.05, "average_views": 5000,
                      "audience_age_range": "25-34", "audience_gender_distribution": {"female": 0.7},
                      "audience_locations": ["US"], "content_types": ["workout"],
                      "content_style": "energetic", "rate_card": "test",
                      "past_brand_categories": ["sports"], "interests": ["fitness"],
                      "posting_frequency": "daily"}]
        add_creators(creators, collection=self.collection)
        self.assertEqual(self.collection.count(), 1)
        add_creators(creators, collection=self.collection)
        self.assertEqual(self.collection.count(), 1)


class TestRetrieve(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import chromadb
        import tempfile
        cls.tmpdir = tempfile.mkdtemp()
        cls.client = chromadb.PersistentClient(path=cls.tmpdir)
        from retrieval.config import COLLECTION_NAME
        cls.collection = cls.client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        creators = [
            {"creator_id": "c001", "primary_niche": "fitness", "name": "Fit Creator One",
             "location": "Mumbai", "languages": ["English", "Hindi"], "platforms": ["instagram", "youtube"],
             "followers": 185000, "engagement_rate": 0.042, "average_views": 320000,
             "audience_age_range": "18-30", "audience_gender_distribution": {"female": 0.72},
             "audience_locations": ["India"], "content_types": ["workout", "nutrition"],
             "content_style": "energetic", "rate_card": "₹15,000–₹50,000",
             "past_brand_categories": ["fitness", "sports"], "interests": ["gym", "running"],
             "posting_frequency": "4-5 posts/week"},
            {"creator_id": "c002", "primary_niche": "gaming", "name": "Gamer Creator",
             "location": "Tokyo", "languages": ["Japanese", "English"], "platforms": ["youtube"],
             "followers": 680000, "engagement_rate": 0.062, "average_views": 1200000,
             "audience_age_range": "18-24", "audience_gender_distribution": {"male": 0.75},
             "audience_locations": ["Japan"], "content_types": ["gaming", "tech"],
             "content_style": "high-energy", "rate_card": "₹20,000–₹50,000",
             "past_brand_categories": ["gaming", "tech"], "interests": ["esports", "tech"],
             "posting_frequency": "daily"},
        ]
        add_creators(creators, collection=cls.collection)

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        shutil.rmtree(cls.tmpdir)

    def test_retrieve_returns_top_k(self) -> None:
        brand = {"brand_name": "FitNova", "industry": "Fitness", "campaign_title": "Test",
                 "campaign_goal": "Test goal", "product": "Test product",
                 "target_audience": "Young women 18-30", "target_age_range": "18-30",
                 "target_gender": "female", "target_locations": ["India"],
                 "required_creator_niches": ["fitness"], "preferred_creator_niches": ["fitness"],
                 "content_types": ["workout"], "platforms": ["instagram"], "tone": "energetic",
                 "mandatory_requirements": ["must have fitness"], "preferred_traits": ["motivational"],
                 "excluded_traits": ["luxury"], "campaign_description": "Test campaign"}
        results = retrieve_creators(brand, top_k=1, collection=self.collection)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["creator_id"], "c001")

    def test_retrieve_returns_requested_k(self) -> None:
        brand = {"brand_name": "TestBrand", "industry": "Fitness", "campaign_title": "Test",
                 "campaign_goal": "Test goal", "product": "Test product",
                 "target_audience": "Test", "target_age_range": "25-34",
                 "target_gender": "all", "target_locations": ["US"],
                 "required_creator_niches": ["fitness"], "preferred_creator_niches": ["fitness"],
                 "content_types": ["workout"], "platforms": ["instagram"], "tone": "energetic",
                 "mandatory_requirements": [], "preferred_traits": [], "excluded_traits": [],
                 "campaign_description": "Test"}
        results = retrieve_creators(brand, top_k=2, collection=self.collection)
        self.assertEqual(len(results), 2)

    def test_no_duplicate_creator_ids(self) -> None:
        brand = {"brand_name": "TestBrand", "industry": "Fitness", "campaign_title": "Test",
                 "campaign_goal": "Test goal", "product": "Test product",
                 "target_audience": "Test", "target_age_range": "25-34",
                 "target_gender": "all", "target_locations": ["US"],
                 "required_creator_niches": ["fitness"], "preferred_creator_niches": ["fitness"],
                 "content_types": ["workout"], "platforms": ["instagram"], "tone": "energetic",
                 "mandatory_requirements": [], "preferred_traits": [], "excluded_traits": [],
                 "campaign_description": "Test"}
        results = retrieve_creators(brand, top_k=2, collection=self.collection)
        ids = [r["creator_id"] for r in results]
        self.assertEqual(len(ids), len(set(ids)))


class TestIntegration(unittest.TestCase):
    def test_load_creators(self) -> None:
        creators = load_creators()
        self.assertEqual(len(creators), 40)
        creator_ids = [c["creator_id"] for c in creators]
        self.assertEqual(len(creator_ids), len(set(creator_ids)))

    def test_load_brands(self) -> None:
        brands = load_brands()
        self.assertEqual(len(brands), 10)

    def test_chroma_collection_can_be_loaded(self) -> None:
        collection = get_collection()
        self.assertIsNotNone(collection)

    def test_unknown_brand_id_handled(self) -> None:
        brands = load_brands()
        existing_ids = [b["brand_id"] for b in brands]
        unknown_id = "b99"
        self.assertNotIn(unknown_id, existing_ids)


if __name__ == "__main__":
    unittest.main()
