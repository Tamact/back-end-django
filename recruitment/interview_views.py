from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .video_interview import VideoInterviewManager, InterviewSession
from .models import InterviewCode
import json

class InterviewLoginView(APIView):
    def post(self, request):
        """Handle interview login with email and code."""
        email = request.data.get('email')
        code = request.data.get('code')
        
        try:
            # Verify interview code
            interview_code = InterviewCode.objects.get(email=email, code=code, used=False)
            
            # Mark code as used
            interview_code.used = True
            interview_code.save()
            
            # Create new interview session
            session = InterviewSession(email=email, profile=interview_code.profile)
            session.start_session()
            
            return Response({
                'status': 'success',
                'profile': interview_code.profile
            })
        except InterviewCode.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid email or code'
            }, status=status.HTTP_401_UNAUTHORIZED)

class InterviewQuestionView(APIView):
    def get(self, request):
        """Get current interview question."""
        email = request.query_params.get('email')
        try:
            session = InterviewSession.objects.get(email=email, completed=False)
            questions = get_questions_for_profil(session.profile)
            
            if session.current_question >= len(questions):
                return Response({
                    'status': 'completed',
                    'message': 'Interview completed'
                })
            
            # Generate audio for question
            video_manager = VideoInterviewManager()
            current_question = questions[session.current_question]
            audio_path = video_manager.generate_audio_question(current_question)
            
            return Response({
                'status': 'success',
                'question': current_question,
                'question_number': session.current_question + 1,
                'total_questions': len(questions),
                'audio_url': settings.MEDIA_URL + audio_path
            })
        except InterviewSession.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No active interview session found'
            }, status=status.HTTP_404_NOT_FOUND)

class InterviewResponseView(APIView):
    def post(self, request):
        """Handle interview response submission."""
        email = request.data.get('email')
        
        try:
            session = InterviewSession.objects.get(email=email, completed=False)
            video_manager = VideoInterviewManager()
            
            # Record video response
            video_path, audio_path = video_manager.record_video_response()
            
            # Transcribe audio
            transcription = video_manager.transcribe_audio(audio_path)
            
            # Get current question
            questions = get_questions_for_profil(session.profile)
            current_question = questions[session.current_question]
            
            # Save response
            session.save_response(
                question=current_question,
                video_path=video_path,
                audio_path=audio_path,
                transcription=transcription
            )
            
            return Response({
                'status': 'success',
                'video_url': settings.MEDIA_URL + video_path,
                'transcription': transcription
            })
        except InterviewSession.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No active interview session found'
            }, status=status.HTTP_404_NOT_FOUND)

class CompleteInterviewView(APIView):
    def post(self, request):
        """Complete the interview session."""
        email = request.data.get('email')
        
        try:
            session = InterviewSession(email=email)
            session.complete_session()
            
            return Response({
                'status': 'success',
                'message': 'Interview completed successfully'
            })
        except InterviewSession.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No active interview session found'
            }, status=status.HTTP_404_NOT_FOUND)

class PrivacyPolicyView(APIView):
    def get(self, request):
        """Get privacy policy and interview instructions."""
        return Response({
            'status': 'success',
            'privacy_policy': {
                'title': 'Charte de Confidentialité',
                'content': [
                    'Vos données personnelles (y compris les enregistrements vidéo) seront utilisées uniquement pour le traitement de votre candidature.',
                    'Ces données ne seront pas partagées avec des tiers non autorisés.',
                    'Une fois le traitement terminé, toutes vos données personnelles seront définitivement supprimées.'
                ],
                'instructions': [
                    'Assurez-vous d\'être dans un endroit calme et bien éclairé.',
                    'Vérifiez que votre caméra et microphone fonctionnent correctement.',
                    'Lisez attentivement les questions avant d\'y répondre.',
                    'Parlez de manière claire et concise.'
                ]
            }
        })
