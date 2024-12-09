import os
import cv2
import wave
import pyaudio
import ffmpeg
import tempfile
import threading
from typing import List, Dict, Optional
from gtts import gTTS
import google.generativeai as genai
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import InterviewSession

class VideoInterviewManager:
    def __init__(self):
        self.api_key = settings.GENAI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
        )

    def generate_audio_question(self, question_text: str) -> str:
        """Generate audio file for a given question."""
        tts = gTTS(text=question_text, lang="fr")
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_audio.name)
        
        # Save to Django storage
        with open(temp_audio.name, 'rb') as f:
            path = f'interview_audio/question_{hash(question_text)}.mp3'
            default_storage.save(path, ContentFile(f.read()))
        
        os.unlink(temp_audio.name)
        return path

    def record_video_response(self, duration: int = 60) -> tuple[str, str]:
        """Record video response with audio."""
        # Setup temporary files
        video_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        audio_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        final_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        
        try:
            # Audio setup
            audio_format = pyaudio.paInt16
            channels = 1
            rate = 44100
            chunk = 1024
            audio_frames = []
            
            # Initialize audio
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=audio_format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )

            # Initialize video capture
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("Cannot access camera")

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(video_temp.name, fourcc, 20.0, (640, 480))

            # Recording flag
            recording = True

            # Audio recording thread
            def record_audio():
                while recording:
                    data = stream.read(chunk)
                    audio_frames.append(data)

            audio_thread = threading.Thread(target=record_audio)
            audio_thread.start()

            # Video recording
            frames_recorded = 0
            total_frames = duration * 20  # 20 fps for 'duration' seconds

            while frames_recorded < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frames_recorded += 1

            # Stop recording
            recording = False
            audio_thread.join()

            # Cleanup resources
            cap.release()
            out.release()
            stream.stop_stream()
            stream.close()
            audio.terminate()

            # Save audio
            with wave.open(audio_temp.name, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(audio.get_sample_size(audio_format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(audio_frames))

            # Merge video and audio
            video_input = ffmpeg.input(video_temp.name)
            audio_input = ffmpeg.input(audio_temp.name)
            ffmpeg.output(
                video_input, 
                audio_input, 
                final_temp.name,
                vcodec='copy',
                acodec='aac'
            ).run(overwrite_output=True)

            # Save to Django storage
            with open(final_temp.name, 'rb') as f:
                video_path = f'interview_videos/response_{os.path.basename(final_temp.name)}'
                default_storage.save(video_path, ContentFile(f.read()))

            # Extract audio for transcription
            audio_path = f'interview_audio/response_{os.path.basename(audio_temp.name)}'
            with open(audio_temp.name, 'rb') as f:
                default_storage.save(audio_path, ContentFile(f.read()))

            return video_path, audio_path

        finally:
            # Cleanup temporary files
            for temp_file in [video_temp, audio_temp, final_temp]:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Gemini AI."""
        try:
            # Get the file from storage
            with default_storage.open(audio_path) as f:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_file.write(f.read())
                temp_file.close()

            # Upload to Gemini
            file = genai.upload_file(temp_file.name, mime_type="audio/wav")
            
            # Start chat session for transcription
            chat = self.model.start_chat(
                history=[{"role": "user", "parts": [file]}]
            )
            response = chat.send_message("Veuillez transcrire cet audio.")
            
            return response.text

        finally:
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass

class InterviewSession:
    def __init__(self, email: str, profile: str):
        self.email = email
        self.profile = profile
        self.current_question = 0
        self.responses = []
        self.video_manager = VideoInterviewManager()

    def start_session(self) -> None:
        """Initialize a new interview session."""
        InterviewSession.objects.create(
            email=self.email,
            profile=self.profile,
            current_question=0,
            completed=False
        )

    def save_response(self, question: str, video_path: str, audio_path: str, transcription: str) -> None:
        """Save interview response."""
        self.responses.append({
            'question': question,
            'video_path': video_path,
            'audio_path': audio_path,
            'transcription': transcription
        })
        
        # Update session in database
        session = InterviewSession.objects.get(email=self.email, completed=False)
        session.current_question = self.current_question + 1
        session.responses = self.responses
        session.save()

    def complete_session(self) -> None:
        """Mark the interview session as complete."""
        session = InterviewSession.objects.get(email=self.email, completed=False)
        session.completed = True
        session.save()
