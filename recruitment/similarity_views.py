from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CV, JobOffer
from .services import SimilarityService

class SimilarityCVJobOfferView(APIView):
    def post(self, request):
        """
        Calculer la similarité entre des CVs et une offre d'emploi
        """
        try:
            # Récupérer les paramètres de la requête
            cv_ids = request.data.get('cv_ids', [])
            offre_id = request.data.get('offre_id')

            # Validation des paramètres
            if not cv_ids:
                return Response({'error': 'Aucun CV sélectionné'}, status=status.HTTP_400_BAD_REQUEST)
            if not offre_id:
                return Response({'error': 'Aucune offre sélectionnée'}, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer l'offre
            try:
                offre = JobOffer.objects.get(offre_id=offre_id)
            except JobOffer.DoesNotExist:
                return Response({'error': 'Offre non trouvée'}, status=status.HTTP_404_NOT_FOUND)

            # Récupérer les CVs
            cvs = CV.objects.filter(cv_id__in=cv_ids)
            if not cvs:
                return Response({'error': 'Aucun CV trouvé'}, status=status.HTTP_404_NOT_FOUND)

            # Calculer la similarité pour chaque CV
            results = []
            for cv in cvs:
                # Calculer la similarité cosinus
                similarity = SimilarityService.calculate_similarity(cv.cv_text, offre.text_offre)

                # Catégoriser les compétences
                categorized_skills = SimilarityService.categorize_skills_with_kano(offre.text_offre)

                # Calculer le score Kano
                kano_score = 0.0
                if categorized_skills:
                    # Extraction des compétences du CV et de l'offre
                    cv_competences = cv.competences or []
                    offre_competences = self._extract_skills_from_kano(categorized_skills)
                    
                    kano_score = SimilarityService.calculate_kano_score(cv_competences, offre_competences)

                results.append({
                    'cv_id': cv.cv_id,
                    'nom_prenom': cv.user.nom_prenom if cv.user else 'Candidat inconnu',
                    'similarite_cosinus': similarity,
                    'score_kano': kano_score,
                    'competences_kano': categorized_skills
                })

            # Trier les résultats par similarité décroissante
            results.sort(key=lambda x: x['similarite_cosinus'], reverse=True)

            return Response({
                'resultats': results,
                'offre_titre': offre.titre
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _extract_skills_from_kano(self, kano_text):
        """
        Extraire les compétences du texte Kano
        """
        categories = ["Indispensable", "Proportionnelle", "Attractive", "Indifférente", "Double tranchant"]
        skills = []

        for category in categories:
            if f"**{category}:**" in kano_text:
                category_section = kano_text.split(f"**{category}:**")[1].split("**")[0].strip()
                category_skills = [skill.strip() for skill in category_section.split("\n") if skill.strip()]
                skills.extend([(skill, category) for skill in category_skills])

        return skills
