from django.urls import path
from .views import (
    CandidateListAPIView,
    CVUploadAPIView,
    CVListAPIView,
    JobOfferAPIView,
    JobOfferUploadAPIView,  
    SimilarityAPIView,
    InterviewQuestionAPIView,
    SimilarityVisualizationAPIView,
    CompetencesVisualizationAPIView,
    StatisticsVisualizationAPIView,
    InterviewLoginView,
    InterviewQuestionView,
    InterviewResponseView,
    CompleteInterviewView,
    PrivacyPolicyView
)
from .similarity_views import SimilarityCVJobOfferView

urlpatterns = [
    # Gestion des candidats
    path('candidates/', CandidateListAPIView.as_view(), name='candidate-list'),
    
    # Gestion des CVs
    path('cv/upload/', CVUploadAPIView.as_view(), name='cv-upload'),
    path('cv/list/', CVListAPIView.as_view(), name='cv-list'),
    
    # Gestion des offres d'emploi
    path('job-offers/', JobOfferAPIView.as_view(), name='job-offer-list'),
    path('job-offers/upload/', JobOfferUploadAPIView.as_view(), name='job-offer-upload'),  
    path('job-offers/similarity/', SimilarityCVJobOfferView.as_view(), name='job-offer-similarity'),
    
    # Calcul de similarité
    path('similarity/', SimilarityAPIView.as_view(), name='calculate-similarity'),
    
    # Gestion des questions d'entretien
    path('interview/questions/', InterviewQuestionAPIView.as_view(), name='interview-questions'),
    path('interview/questions/<str:profile>/', InterviewQuestionAPIView.as_view(), name='profile-questions'),
    
    # Interview URLs
    path('interview/login/', InterviewLoginView.as_view(), name='interview-login'),
    path('interview/question/', InterviewQuestionView.as_view(), name='interview-question'),
    path('interview/response/', InterviewResponseView.as_view(), name='interview-response'),
    path('interview/complete/', CompleteInterviewView.as_view(), name='interview-complete'),
    path('interview/privacy-policy/', PrivacyPolicyView.as_view(), name='privacy-policy'),
    
    # Visualisations et statistiques
    path('visualizations/similarity/', SimilarityVisualizationAPIView.as_view(), name='similarity-visualizations'),
    path('visualizations/competences/', CompetencesVisualizationAPIView.as_view(), name='competences-visualizations'),
    path('visualizations/statistics/', StatisticsVisualizationAPIView.as_view(), name='statistics'),
]
