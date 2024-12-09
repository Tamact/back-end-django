import numpy as np
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    _models = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._models:
            self._models = {
                'sentence_transformer': SentenceTransformer('all-MiniLM-L12-v2'),
                # Ajoutez d'autres modèles si nécessaire
            }

    def get_models(self):
        return list(self._models.values())

class VectorStore:
    @staticmethod
    def store_vectors(vectors: List[np.ndarray], 
                      names: List[str], 
                      collection: str = "default_collection"):
        """
        Stocke des vecteurs dans Qdrant
        
        :param vectors: Liste de vecteurs numpy
        :param names: Liste de noms correspondant aux vecteurs
        :param collection: Nom de la collection Qdrant
        """
        try:
            client = QdrantClient(
                url="https://5ab76626-81f8-42db-b56f-f23928129cce.europe-west3-0.gcp.cloud.qdrant.io:6333",
                api_key="GToQ0tM7oryP7zOxTO_P5eeftQW0UErJCYOh1wrhInH4HRlOSscewQ"
            )
            
            # Créer la collection si elle n'existe pas
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=vectors[0].shape[0], distance=Distance.COSINE)
            )
            
            # Convertir les vecteurs en liste de listes
            points = [
                {"id": i, "vector": vector.tolist(), "payload": {"name": name}}
                for i, (vector, name) in enumerate(zip(vectors, names))
            ]
            
            client.upsert(
                collection_name=collection,
                points=points
            )
            
            logger.info(f"Stored {len(vectors)} vectors in collection {collection}")
        
        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            raise

class TextAnalyzer:
    def __init__(self):
        self.model_manager = ModelManager()
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier PDF
        
        :param file_path: Chemin du fichier PDF
        :return: Texte extrait
        """
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ' '.join([page.extract_text() for page in reader.pages])
            return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF : {e}")
            return ""
    
    def analyze_style(self, text: str) -> Dict[str, Any]:
        """
        Analyse le style du texte
        
        :param text: Texte à analyser
        :return: Dictionnaire avec les résultats de l'analyse
        """
        # Implémentation basique, à enrichir
        return {
            "complexity": len(text.split()) / len(text.split('.') or 1),
            "avg_word_length": sum(len(word) for word in text.split()) / len(text.split() or 1)
        }
    
    def detect_ai_generated(self, text: str) -> Dict[str, float]:
        """
        Détecte si le texte est généré par IA
        
        :param text: Texte à analyser
        :return: Probabilité de génération par IA
        """
        try:
            from transformers import pipeline
            detector = pipeline('text-classification', model='roberta-base-openai-detector')
            result = detector(text)[0]
            return {
                "ai_probability": result['score'],
                "is_ai_generated": result['label'] == 'AI'
            }
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'IA : {e}")
            return {"ai_probability": 0.0, "is_ai_generated": False}
            
    
    def categorize_skills_with_kano(text_offre):
        """
        Utilise Gemini AI pour catégoriser les compétences d'une fiche de poste ou d'un CV selon le modèle de Kano.

        :param offre_text: Le contenu du CV ou de la fiche de poste.
        :return: Dictionnaire contenant les compétences catégorisées.
        """
    # Initialiser une session de chat avec l'API Gemini
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        },
    )
    
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    f"Voici un extrait de l'offre : {text_offre}. "
                    "Catégorise les compétences en fonction du modèle de Kano (Indispensable, Proportionnelle, Attractive, Indifférente). "
                    "Donne juste les compétences classées sans explication ni commentaire. Enléve aussi les notes",
                ],
            }
        ]
    )

    # Envoyer une requête pour générer la catégorisation
    response = chat_session.send_message("Catégorise les compétences selon le modèle de Kano sans note ni commentaire.")
    
    if response.text:
        return response.text
    else:
        return "Aucune réponse générée."


class TextComparator:
    @staticmethod
    def compute_cosine_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs
        
        :param vector1: Premier vecteur
        :param vector2: Deuxième vecteur
        :return: Score de similarité
        """
        return np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
