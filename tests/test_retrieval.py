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
from retrieval.chroma_store import add_creators, get_collection, load_creators
from retrieval.retrieve import retrieve


class TestEmbeddings(unittest.TestCase):
    def test_build_creator_text(self):
        creator = {"niche": ["fitness"], "audience_age": "25-34", "audience_geo": ["US"],
                    "past_brand_categories": ["sports"], "deliverable_types": ["reel"]}
        text = build_creator_text(creator)
        self.assertIn("fitness", text)
        self.assertIn("25-34", text)
        self.assertIn("US", text)

    def test_build_brief_text(self):
        brand = {"target_niche": ["beauty"], "target_age": "18-24", "target_geo": ["US"],
                 "tone": "authentic and warm", "brief_text": "test brief"}
        text = build_brief_text(brand)
        self.assertIn("beauty", text)
        self.assertIn("authentic and warm", text)


class TestChromaStore(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        import chromadb
        self.client = chromadb.PersistentClient(path=self.tmpdir)
        self.collection = self.client.get_or_create_collection(name="test", metadata={"hnsw:space": "cosine"})

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_add_creators(self) -> None:
        creators = [{"creator_id": "c001", "niche": ["fitness"], "audience_age": "25-34",
                      "audience_geo": ["US"], "past_brand_categories": ["sports"],
                      "deliverable_types": ["reel"]}]
        collection = self.client.get_or_create_collection(name="test_creators", metadata={"hnsw:space": "cosine"})
        add_creators(creators, collection=collection)
        self.assertEqual(collection.count(), 1)


class TestRetrieve(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.creators = [
            {"creator_id": "c001", "niche": ["fitness"], "audience_age": "25-34",
             "audience_geo": ["US"], "past_brand_categories": ["sports"],
             "deliverable_types": ["reel"], "followers": 50000},
            {"creator_id": "c002", "niche": ["tech"], "audience_age": "18-24",
             "audience_geo": ["UK"], "past_brand_categories": ["gaming"],
             "deliverable_types": ["youtube short"], "followers": 30000},
        ]
        import chromadb
        cls.client = chromadb.PersistentClient(path=tempfile.mkdtemp())
        cls.collection = cls.client.get_or_create_collection(name="test_retrieve", metadata={"hnsw:space": "cosine"})
        add_creators(cls.creators, collection=cls.collection)

    def test_retrieve_returns_results(self) -> None:
        brand = {"target_niche": ["fitness"], "target_age": "25-34", "target_geo": ["US"],
                 "tone": "casual", "brief_text": "fitness campaign"}
        results = retrieve(brand, k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["creator_id"], "c001")


if __name__ == "__main__":
    unittest.main()
