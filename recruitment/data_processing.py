import os
import uuid
import numpy as np
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import spacy
import json
from django.conf import settings
from typing import List, Dict, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Initialiser Qdrant client
client = QdrantClient(
    url=settings.QDRANT_HOST,
    api_key=settings.QDRANT_API_KEY
)

class VectorStore:
    @staticmethod
    def store_vectors(vectors: np.ndarray, names: List[str], collection: str = "cv_collection") -> bool:
        """Stockage des vecteurs dans Qdrant."""
        points = [
            {
                "id": str(uuid.uuid4()),
                "vector": vector.tolist(),
                "payload": {"name": name}
            }
            for name, vector in zip(names, vectors)
        ]
        try:
            client.upsert(collection_name=collection, points=points)
            logger.info(f"Vecteurs stockés avec succès dans la collection {collection}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du stockage des vecteurs : {str(e)}")
            return False

    @staticmethod
    def compute_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float:
        """Calcul de la similarité cosinus entre deux vecteurs."""
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vector1, vector2) / (norm1 * norm2))

class ModelManager:
    _instance = None
    _models = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._models is None:
            self._models = self.load_models()

    @staticmethod
    def load_models() -> Tuple[SentenceTransformer, SentenceTransformer, SentenceTransformer]:
        """Charge les modèles de transformation de texte."""
        try:
            model1 = SentenceTransformer('all-MPNet-base-v2')
            model2 = SentenceTransformer('paraphrase-MiniLM-L12-v2')
            model3 = SentenceTransformer('all-MiniLM-L12-v2')
            return model1, model2, model3
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles : {str(e)}")
            raise

    def get_models(self) -> Tuple[SentenceTransformer, SentenceTransformer, SentenceTransformer]:
        """Retourne les modèles chargés."""
        return self._models

class TextAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.ai_detector = pipeline("text-classification", model="roberta-base-openai-detector")

    def analyze_style(self, text: str) -> Dict[str, Any]:
        """Analyse le style et le ton du texte."""
        doc = self.nlp(text)
        sentences = list(doc.sents)
        
        try:
            avg_sentence_length = sum(len(sent) for sent in sentences) / len(sentences)
        except ZeroDivisionError:
            avg_sentence_length = 0

        return {
            "avg_sentence_length": avg_sentence_length,
            "unusual_words": [token.text for token in doc if token.is_alpha and len(token.text) > 12],
            "num_sentences": len(sentences)
        }

    def detect_ai_generated(self, text: str) -> Dict[str, float]:
        """Détecte si le texte a été généré par une IA."""
        try:
            result = self.ai_detector(text)[0]
            return {
                "label": result["label"],
                "score": result["score"]
            }
        except Exception as e:
            logger.error(f"Erreur lors de la détection IA : {str(e)}")
            return {"label": "ERROR", "score": 0.0}

class TextComparator:
    @staticmethod
    def load_references(file_path: str = "references.json") -> Dict[str, str]:
        """Charge les textes de référence."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des références : {str(e)}")
            return {}

    @staticmethod
    def jaccard_similarity(text1: str, text2: str) -> float:
        """Calcule la similarité de Jaccard entre deux textes."""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def compare_with_references(self, submitted_cv: str, reference_texts: Dict[str, str]) -> Dict[str, float]:
        """Compare un CV avec les textes de référence."""
        results = {}
        for ref_name, ref_text in reference_texts.items():
            similarity = self.jaccard_similarity(submitted_cv, ref_text)
            results[ref_name] = similarity
        return results
