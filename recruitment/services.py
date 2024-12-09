from django.core.exceptions import ObjectDoesNotExist
from .models import Candidate, CV, JobOffer, Result, Interview
from typing import Dict, List, Optional, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
import os
import joblib

class CandidateService:
    @staticmethod
    def create_candidate(nom_prenom: str, mail: str, numero_tlfn: str) -> int:
        """Crée un nouveau candidat."""
        candidate = Candidate.objects.create(
            nom_prenom=nom_prenom,
            mail=mail,
            numero_tlfn=numero_tlfn
        )
        return candidate.user_id

    @staticmethod
    def get_all_candidates() -> List[Dict[str, Any]]:
        """Récupère tous les candidats."""
        candidates = Candidate.objects.all()
        return [
            {
                "user_id": c.user_id,
                "nom_prenom": c.nom_prenom,
                "mail": c.mail,
                "numero_tlfn": c.numero_tlfn,
                "profil": c.profil.profil if c.profil else None,
                "code": c.code
            } for c in candidates
        ]

    @staticmethod
    def update_candidate(user_id: int, data: Dict[str, Any]) -> Optional[int]:
        """Met à jour les informations d'un candidat."""
        try:
            candidate = Candidate.objects.get(user_id=user_id)
            for field, value in data.items():
                setattr(candidate, field, value)
            candidate.save()
            return candidate.user_id
        except ObjectDoesNotExist:
            return None

class CVService:
    @staticmethod
    def preprocess_text(text):
        """
        Prétraite le texte du CV
        """
        if not text:
            return ""
            
        try:
            # Convertir en minuscules
            text = text.lower()
            
            # Supprimer les caractères spéciaux et la ponctuation
            import re
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Supprimer les espaces multiples
            text = ' '.join(text.split())
            
            return text
        except Exception as e:
            print(f"Erreur lors du prétraitement du texte: {str(e)}")
            return text

    @staticmethod
    def save_to_user(nom_prenom, mail, numero_tlfn=None):
        """
        Enregistre ou met à jour les informations d'un utilisateur
        """
        try:
            print(f"Tentative d'enregistrement/mise à jour pour {nom_prenom} ({mail})")
            # Vérifier si l'utilisateur existe déjà avec cet email
            user = Candidate.objects.filter(mail=mail).first()
            
            if user:
                print(f"Utilisateur existant trouvé avec l'ID {user.user_id}")
                # Mise à jour des informations existantes
                user.nom_prenom = nom_prenom
                if numero_tlfn:
                    user.numero_tlfn = numero_tlfn
                user.save()
                return user.user_id
            else:
                print("Création d'un nouvel utilisateur")
                # Création d'un nouvel utilisateur
                user = Candidate.objects.create(
                    nom_prenom=nom_prenom,
                    mail=mail,
                    numero_tlfn=numero_tlfn if numero_tlfn else ''
                )
                print(f"Nouvel utilisateur créé avec l'ID {user.user_id}")
                return user.user_id
        except Exception as e:
            print(f"Erreur détaillée lors de l'enregistrement de l'utilisateur: {str(e)}")
            return None

    @staticmethod
    def save_to_cv(user_id, cv_text, competences_list):
        """
        Enregistre un CV pour un utilisateur donné
        """
        try:
            print(f"Tentative d'enregistrement du CV pour l'utilisateur {user_id}")
            # Création du CV
            cv = CV.objects.create(
                user_id=user_id,
                cv_text=cv_text,
                competences=competences_list
            )
            print(f"CV créé avec l'ID {cv.cv_id}")
            return cv.cv_id
        except Exception as e:
            print(f"Erreur détaillée lors de l'enregistrement du CV: {str(e)}")
            return None

    @staticmethod
    def get_all_cvs():
        """Récupère tous les CVs avec les informations des candidats"""
        try:
            cvs = CV.objects.select_related('user').all()
            return [{
                'cv_id': cv.cv_id,
                'cv_text': cv.cv_text,
                'competences': cv.competences,
                'candidate': {
                    'id': cv.user.user_id,
                    'nom_prenom': cv.user.nom_prenom,
                    'mail': cv.user.mail,
                    'numero_tlfn': cv.user.numero_tlfn
                } if cv.user else None
            } for cv in cvs]
        except Exception as e:
            print(f"Erreur lors de la récupération des CVs: {str(e)}")
            return []

class JobOfferService:
    @staticmethod
    def preprocess_offre_text(text):
        """
        Prétraite le texte de l'offre d'emploi
        """
        if not text:
            return ""
            
        try:
            # Convertir en minuscules
            text = text.lower()
            
            # Supprimer les caractères spéciaux et la ponctuation
            import re
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Supprimer les espaces multiples
            text = ' '.join(text.split())
            
            return text
        except Exception as e:
            print(f"Erreur lors du prétraitement du texte de l'offre: {str(e)}")
            return text

    @staticmethod
    def save_to_offre(text_offre, offre_societe, titre):
        """
        Enregistre une nouvelle offre d'emploi
        """
        try:
            print(f"Tentative d'enregistrement de l'offre : {titre} pour {offre_societe}")
            
            # Créer l'offre
            offre = JobOffer.objects.create(
                text_offre=text_offre,
                offre_societe=offre_societe,
                titre=titre
            )
            
            print(f"Offre enregistrée avec l'ID {offre.offre_id}")
            
            # Vectorisation de l'offre (optionnel)
            try:
                from .ml_utils import ModelManager, VectorStore
                model_manager = ModelManager()
                models = model_manager.get_models()
                if models and len(models) > 0:
                    offer_vector = models[0].encode(text_offre)
                    VectorStore.store_vectors([offer_vector], [titre], collection="offer_collection")
            except Exception as e:
                print(f"Erreur lors de la vectorisation de l'offre: {str(e)}")
            
            return offre.offre_id
        
        except Exception as e:
            print(f"Erreur détaillée lors de l'enregistrement de l'offre: {str(e)}")
            return None

    @staticmethod
    def get_all_job_offers():
        """
        Récupère toutes les offres d'emploi
        """
        try:
            offres = JobOffer.objects.all()
            return [{
                'offre_id': offre.offre_id,
                'text_offre': offre.text_offre,
                'offre_societe': offre.offre_societe,
                'titre': offre.titre
            } for offre in offres]
        except Exception as e:
            print(f"Erreur lors de la récupération des offres: {str(e)}")
            return []

    @staticmethod
    def create_job_offer(text_offre: str, offre_societe: str, titre: str) -> int:
        """Crée une nouvelle offre d'emploi."""
        job_offer = JobOffer.objects.create(
            text_offre=text_offre,
            offre_societe=offre_societe,
            titre=titre
        )
        return job_offer.offre_id

    @staticmethod
    def get_all_job_offers() -> List[Dict[str, Any]]:
        """Récupère toutes les offres d'emploi."""
        offers = JobOffer.objects.all()
        return [
            {
                "offre_id": o.offre_id,
                "text_offre": o.text_offre,
                "offre_societe": o.offre_societe,
                "titre": o.titre
            } for o in offers
        ]

class ResultService:
    @staticmethod
    def create_result(cv_id: int, offre_id: int, similarity: float) -> Optional[int]:
        """Crée un nouveau résultat."""
        try:
            cv = CV.objects.get(cv_id=cv_id)
            job_offer = JobOffer.objects.get(offre_id=offre_id)
            result = Result.objects.create(
                cv=cv,
                job_offer=job_offer,
                similarity=similarity
            )
            return result.result_id
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_all_results() -> List[Dict[str, Any]]:
        """Récupère tous les résultats."""
        results = Result.objects.select_related('cv', 'job_offer').all()
        return [
            {
                "result_id": r.result_id,
                "cv_id": r.cv.cv_id,
                "offre_id": r.job_offer.offre_id,
                "similarity": r.similarity,
                "candidate_name": r.cv.user.nom_prenom,
                "job_title": r.job_offer.titre
            } for r in results
        ]

class InterviewService:
    @staticmethod
    def create_interview_question(profile: str, question: str) -> Optional[int]:
        """Crée une nouvelle question d'entretien."""
        interview = Interview.objects.create(
            profile=profile,
            question=question
        )
        return interview.id

    @staticmethod
    def get_questions_by_profile(profile: str) -> List[str]:
        """Récupère les questions pour un profil donné."""
        return list(Interview.objects.filter(profile=profile).values_list('question', flat=True))

    @staticmethod
    def update_profile_questions(profile: str, questions: List[str]) -> bool:
        """Met à jour les questions pour un profil."""
        try:
            Interview.objects.filter(profile=profile).delete()
            Interview.objects.bulk_create([
                Interview(profile=profile, question=q) for q in questions
            ])
            return True
        except Exception:
            return False

class SimilarityService:
    @staticmethod
    def load_models():
        """
        Charger les modèles de vectorisation
        """
        try:
            model_path = os.path.join(settings.BASE_DIR, 'recruitment', 'ml_models')
            model1 = joblib.load(os.path.join(model_path, 'model1.joblib'))
            model2 = joblib.load(os.path.join(model_path, 'model2.joblib'))
            model3 = joblib.load(os.path.join(model_path, 'model3.joblib'))
            return model1, model2, model3
        except Exception as e:
            print(f"Erreur lors du chargement des modèles : {e}")
            return None, None, None

    @staticmethod
    def compute_cosine_similarity(vector1, vector2):
        """
        Calculer la similarité cosinus entre deux vecteurs
        """
        try:
            return cosine_similarity([vector1], [vector2])[0][0]
        except Exception as e:
            print(f"Erreur lors du calcul de la similarité : {e}")
            return 0.0

    @staticmethod
    def categorize_skills_with_kano(text_offre):
        """
        Catégoriser les compétences selon le modèle de Kano
        """
        # Importation conditionnelle pour éviter les dépendances
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            import os

            # Configuration de l'API Google
            os.environ['GOOGLE_API_KEY'] = settings.GOOGLE_API_KEY

            # Initialisation du modèle
            llm = ChatGoogleGenerativeAI(model="gemini-pro")

            # Prompt pour la catégorisation des compétences
            prompt = f"""
            En utilisant le modèle de Kano, analysez et catégorisez les compétences requises dans le texte suivant :

            Texte de l'offre : {text_offre}

            Catégorisez les compétences selon :
            - Indispensable : Compétences critiques sans lesquelles le candidat ne peut pas réussir
            - Proportionnelle : Compétences dont la maîtrise augmente proportionnellement la satisfaction
            - Attractive : Compétences qui surprennent et apportent une valeur ajoutée
            - Indifférente : Compétences qui n'impactent pas significativement la satisfaction
            - Double tranchant : Compétences qui peuvent être positives ou négatives selon le contexte

            Réponse structurée avec des titres en gras et les compétences listées.
            """

            # Génération de la réponse
            response = llm.invoke(prompt)
            return response.content

        except ImportError:
            print("Les dépendances pour la catégorisation des compétences ne sont pas installées.")
            return None

    @staticmethod
    def calculate_kano_score(cv_competences, offre_competences):
        """
        Calculer le score Kano basé sur les compétences
        """
        poids_kano = {
            "Indispensable": 1.0,
            "Proportionnelle": 0.7,
            "Attractive": 0.5,
            "Indifférente": 0.2,
            "Double tranchant": 0.3
        }

        score = sum(
            poids_kano.get(kano_category, 0) 
            for competence, kano_category in offre_competences 
            if competence in cv_competences
        )
        return min(score, 1.0)

    @staticmethod
    def calculate_similarity(cv_text, offre_text):
        """
        Calculer la similarité complète entre un CV et une offre
        """
        try:
            # Charger les modèles
            model1, model2, model3 = SimilarityService.load_models()
            
            if not all([model1, model2, model3]):
                raise ValueError("Impossible de charger tous les modèles")

            # Encoder les textes
            cv_vector = np.concatenate([
                model1.encode([cv_text]),
                model2.encode([cv_text]),
                model3.encode([cv_text])
            ], axis=1)

            offre_vector = np.concatenate([
                model1.encode([offre_text]),
                model2.encode([offre_text]),
                model3.encode([offre_text])
            ], axis=1)

            # Calculer la similarité cosinus
            similarity = SimilarityService.compute_cosine_similarity(cv_vector[0], offre_vector[0])

            return similarity

        except Exception as e:
            print(f"Erreur lors du calcul de la similarité : {e}")
            return 0.0
