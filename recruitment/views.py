from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.conf import settings
import pandas as pd

from .services import (
    CandidateService,
    CVService,
    JobOfferService,
    ResultService,
    InterviewService
)
from .ml_utils import (
    VectorStore,
    ModelManager,
    TextAnalyzer,
    TextComparator
)
from .utils.visualization import DataVisualizer

class CandidateListAPIView(APIView):
    def get(self, request):
        """Récupère tous les candidats"""
        candidates = CandidateService.get_all_candidates()
        return Response(candidates)
    
    def post(self, request):
        """Crée un nouveau candidat"""
        data = request.data
        user_id = CandidateService.create_candidate(
            nom_prenom=data.get('nom_prenom'),
            mail=data.get('mail'),
            numero_tlfn=data.get('numero_tlfn')
        )
        return Response({'user_id': user_id}, status=status.HTTP_201_CREATED)

class CVUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        """
        Endpoint pour télécharger un CV et enregistrer les informations du candidat
        """
        try:
            print("Content-Type:", request.content_type)
            print("Données POST:", request.POST)
            print("Données FILES:", request.FILES)
            print("Données brutes:", request.data)
            
            # Vérifier tous les champs possibles
            nom_prenom = request.POST.get('nom_prenom') or request.data.get('nom_prenom')
            mail = request.POST.get('mail') or request.data.get('mail')
            numero_tlfn = request.POST.get('numero_tlfn') or request.data.get('numero_tlfn')
            competences = request.POST.get('competences') or request.data.get('competences')
            cv_file = request.FILES.get('cv_file')

            print("nom_prenom reçu:", nom_prenom)
            print("mail reçu:", mail)
            print("numero_tlfn reçu:", numero_tlfn)
            print("competences reçues:", competences)
            print("cv_file reçu:", cv_file)

            if not nom_prenom:
                return Response(
                    {'error': 'Le nom et prénom sont requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not mail:
                return Response(
                    {'error': 'L\'adresse email est requise'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not cv_file:
                return Response(
                    {'error': 'Le fichier CV est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lecture et prétraitement du CV
            try:
                print(f"Type de fichier reçu: {cv_file.content_type}")
                
                if cv_file.content_type == 'application/pdf':
                    # Utiliser un chemin temporaire pour le PDF
                    import tempfile
                    import os
                    
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, 'temp.pdf')
                    
                    with open(temp_path, 'wb') as f:
                        for chunk in cv_file.chunks():
                            f.write(chunk)
                    
                    try:
                        from pdfminer.high_level import extract_text
                        cv_text = extract_text(temp_path)
                    except Exception as e:
                        print(f"Erreur lors de l'extraction du texte PDF: {str(e)}")
                        return Response(
                            {'error': f'Erreur lors de la lecture du PDF: {str(e)}'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    finally:
                        # Nettoyage
                        import shutil
                        shutil.rmtree(temp_dir)
                
                elif cv_file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    # Pour les fichiers DOCX
                    import docx2txt
                    cv_text = docx2txt.process(cv_file)
                
                elif cv_file.content_type == 'text/plain':
                    # Pour les fichiers texte
                    cv_text = cv_file.read().decode('utf-8')
                
                else:
                    return Response(
                        {'error': f'Type de fichier non supporté: {cv_file.content_type}. Utilisez PDF, DOCX ou TXT.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not cv_text or not cv_text.strip():
                    return Response(
                        {'error': 'Le fichier CV est vide ou ne contient pas de texte lisible'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                print(f"Texte extrait (premiers 100 caractères): {cv_text[:100]}")
                
                preprocessed_cv_text = CVService.preprocess_text(cv_text)
            except Exception as e:
                print(f"Erreur détaillée lors de l'extraction du texte: {str(e)}")
                return Response(
                    {'error': f'Erreur lors de la lecture du fichier CV: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Conversion des compétences en liste
            competences_list = [comp.strip() for comp in competences.split(',')] if competences else []

            # Enregistrement du candidat et du CV
            try:
                # Enregistrement des informations de l'utilisateur
                user_id = CVService.save_to_user(nom_prenom, mail, numero_tlfn)
                
                if not user_id:
                    return Response(
                        {'error': 'Erreur lors de l\'enregistrement du candidat'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # Enregistrement du CV
                cv_id = CVService.save_to_cv(user_id, preprocessed_cv_text, competences_list)
                
                if not cv_id:
                    return Response(
                        {'error': 'Erreur lors de l\'enregistrement du CV'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                return Response({
                    'message': 'CV enregistré avec succès',
                    'cv_id': cv_id,
                    'user_id': user_id
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                print(f"Erreur lors de l'enregistrement: {str(e)}")
                return Response(
                    {'error': f'Erreur lors de l\'enregistrement: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            print(f"Erreur générale: {str(e)}")
            return Response(
                {'error': f'Une erreur s\'est produite: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CVListAPIView(APIView):
    def get(self, request):
        """Récupère la liste de tous les CVs"""
        cvs = CVService.get_all_cvs()
        return Response(cvs)

class JobOfferAPIView(APIView):
    def get(self, request):
        """Récupère toutes les offres d'emploi"""
        offers = JobOfferService.get_all_job_offers()
        return Response(offers)

    def post(self, request):
        """Crée une nouvelle offre d'emploi"""
        try:
            data = request.data
            if not data.get('text_offre'):
                return Response(
                    {'error': 'Le champ text_offre est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Sauvegarde en base de données d'abord
            offer_id = JobOfferService.create_job_offer(
                text_offre=data.get('text_offre'),
                offre_societe=data.get('offre_societe'),
                titre=data.get('titre')
            )

            # Analyse et catégorisation des compétences (optionnel)
            skills_categorization = None
            try:
                text_analyzer = TextAnalyzer()
                skills_categorization = text_analyzer.categorize_skills_with_kano(data.get('text_offre'))
            except Exception as e:
                print(f"Erreur lors de l'analyse des compétences: {str(e)}")

            # Vectorisation de l'offre (optionnel)
            try:
                model_manager = ModelManager()
                models = model_manager.get_models()
                if models and len(models) > 0:
                    offer_vector = models[0].encode(data.get('text_offre'))
                    VectorStore.store_vectors([offer_vector], [data.get('titre')], collection="offer_collection")
            except Exception as e:
                print(f"Erreur lors de la vectorisation: {str(e)}")
            
            response_data = {'offre_id': offer_id}
            if skills_categorization:
                response_data['skills_categorization'] = skills_categorization

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la création de l\'offre: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobOfferUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        """
        Endpoint pour télécharger une offre d'emploi
        """
        try:
            # Récupérer les données
            titre = request.data.get('titre')
            offre_societe = request.data.get('offre_societe')
            offer_file = request.FILES.get('offer_file')
            
            # Gestion du texte de l'offre
            text_offre = request.data.get('text_offre')
            if text_offre and hasattr(text_offre, 'strip'):
                text_offre = text_offre.strip()
            elif text_offre is None:
                text_offre = ''

            # Validation des champs obligatoires
            if not titre:
                return Response(
                    {'error': 'Le titre de l\'offre est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not offre_societe:
                return Response(
                    {'error': 'Le nom de la société est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extraction du texte de l'offre
            if offer_file is not None:
                try:
                    if offer_file.content_type == "application/pdf":
                        from pdfminer.high_level import extract_text
                        import tempfile
                        import os
                        
                        # Créer un fichier temporaire
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                            for chunk in offer_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name
                        
                        try:
                            text_offre = extract_text(temp_file_path)
                        except Exception as e:
                            print(f"Erreur lors de l'extraction du texte PDF: {str(e)}")
                            return Response(
                                {'error': f'Erreur lors de la lecture du PDF: {str(e)}'}, 
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        finally:
                            # Supprimer le fichier temporaire
                            os.unlink(temp_file_path)
                    
                    elif offer_file.content_type == "text/plain":
                        from io import StringIO
                        text_offre = offer_file.read().decode('utf-8')
                    
                    else:
                        return Response(
                            {'error': 'Format de fichier non supporté pour l\'offre d\'emploi'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                except Exception as e:
                    print(f"Erreur lors du traitement du fichier: {str(e)}")
                    return Response(
                        {'error': f'Erreur lors du traitement du fichier: {str(e)}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Vérifier qu'un texte d'offre est présent
            if not text_offre:
                return Response(
                    {'error': 'Le texte de l\'offre est requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prétraitement du texte de l'offre
            try:
                preprocessed_offre_text = JobOfferService.preprocess_offre_text(text_offre)

                # Enregistrement de l'offre
                offre_id = JobOfferService.save_to_offre(
                    text_offre=preprocessed_offre_text, 
                    offre_societe=offre_societe, 
                    titre=titre
                )
                
                if offre_id:  
                    return Response({
                        'message': 'Offre enregistrée avec succès',
                        'offre_id': offre_id
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {'error': 'Erreur lors de l\'enregistrement de l\'offre'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except Exception as e:
                print(f"Une erreur s'est produite : {e}")
                return Response(
                    {'error': f'Une erreur s\'est produite : {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            print(f"Erreur générale: {str(e)}")
            return Response(
                {'error': f'Une erreur s\'est produite: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SimilarityAPIView(APIView):
    def post(self, request):
        """Calcule la similarité entre CVs et offre"""
        cv_ids = request.data.get('cv_ids')
        offer_id = request.data.get('offer_id')
        
        if not cv_ids or not offer_id:
            return Response(
                {'error': 'cv_ids et offer_id sont requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        for cv_id in cv_ids:
            similarity = ResultService.create_result(cv_id, offer_id, 0.0)  # À calculer
            if similarity:
                results.append({
                    'cv_id': cv_id,
                    'similarity': similarity
                })
        
        return Response(results)

class InterviewQuestionAPIView(APIView):
    def post(self, request):
        """Génère des questions d'entretien"""
        profile = request.data.get('profile')
        if not profile:
            return Response(
                {'error': 'Le profil est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions = InterviewService.create_interview_question(
            profile=profile,
            question=request.data.get('question', '')
        )
        
        return Response({'questions': questions})

    def get(self, request, profile):
        """Récupère les questions pour un profil"""
        questions = InterviewService.get_questions_by_profile(profile)
        return Response({'questions': questions})

class SimilarityVisualizationAPIView(APIView):
    def get(self, request):
        """Retourne les données pour les visualisations de similarité"""
        results = ResultService.get_all_results()
        df_results = pd.DataFrame(results)
        
        visualizations = {
            'similarity_chart': DataVisualizer.prepare_similarity_data(df_results),
            'pie_chart': DataVisualizer.prepare_pie_chart_data(df_results),
            'histogram': DataVisualizer.prepare_histogram_data(df_results),
            'boxplot': DataVisualizer.prepare_boxplot_data(df_results),
            'scatter': DataVisualizer.prepare_scatter_data(df_results),
            'cumulative': DataVisualizer.prepare_cumulative_data(df_results)
        }
        
        return Response(visualizations)

class CompetencesVisualizationAPIView(APIView):
    def get(self, request):
        """Retourne les données pour les visualisations des compétences"""
        competences_data = CVService.get_competences_data()
        visualization_data = DataVisualizer.prepare_competences_data(competences_data)
        return Response(visualization_data)

class StatisticsVisualizationAPIView(APIView):
    def get(self, request):
        """Retourne les statistiques globales"""
        results = ResultService.get_all_results()
        df_results = pd.DataFrame(results)
        
        statistics = {
            'total_cvs': len(df_results),
            'average_similarity': float(df_results['Similarité Cosinus'].mean()),
            'median_similarity': float(df_results['Similarité Cosinus'].median()),
            'std_similarity': float(df_results['Similarité Cosinus'].std()),
            'top_candidates': df_results.nlargest(5, 'Similarité Cosinus')[['Nom du CV', 'Similarité Cosinus']].to_dict('records')
        }
        
        return Response(statistics)