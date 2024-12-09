import re
import os
from typing import Set, List
import nltk
from nltk.corpus import stopwords
from pdfminer.high_level import extract_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import random
import string
import google.generativeai as genai
from django.conf import settings
from django.core.mail import send_mail
from .models import InterviewCode

# Download NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class TextProcessor:
    @staticmethod
    def get_stop_words() -> Set[str]:
        """Get stopwords for French and English."""
        return set(stopwords.words('french') + stopwords.words('english'))

    @staticmethod
    def preprocess_text(text: str) -> str:
        """Preprocess text: lowercase, remove special characters and stopwords."""
        stop_words = TextProcessor.get_stop_words()
        text = text.lower()
        text = re.sub(r'\W+', ' ', text)
        tokens = text.split()
        tokens = [word for word in tokens if word not in stop_words]
        return ' '.join(tokens)

    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        """Extract text from a PDF file."""
        try:
            text = extract_text(pdf_file)
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return bool(re.match(email_regex, email))

class EmailService:
    @staticmethod
    def generate_random_code(length: int = 6) -> str:
        """Generate a random code of specified length."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def send_interview_email(recipient: str, subject: str, message_body: str, profile: str) -> bool:
        """Send interview email with generated code."""
        try:
            code = EmailService.generate_random_code()
            message_body_with_code = f"{message_body}\n\nVotre code d'entretien : {code}"
            
            # Using Django's send_mail
            send_mail(
                subject,
                message_body_with_code,
                settings.EMAIL_HOST_USER,
                [recipient],
                fail_silently=False,
            )
            
            # Save the code to database
            InterviewCode.objects.create(
                email=recipient,
                code=code,
                profile=profile
            )
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

class AIQuestionGenerator:
    def __init__(self):
        self.api_key = settings.GENAI_API_KEY
        genai.configure(api_key=self.api_key)
        
        self.generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 512,
            "top_p": 0.95,
            "top_k": 50
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
        )

    def generate_questionnaire(self, profile_info: dict) -> List[str]:
        """Generate interview questions based on candidate profile."""
        profil = profile_info.get("profil", "N/A")
        
        chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        "Génère un questionnaire de 10 questions basées sur le profil suivant :",
                        f"Profil : {profil}",
                    ],
                }
            ]
        )

        response = chat_session.send_message(
            "Crée un questionnaire de 10 questions en fonction du profil donné. "
            "Donne juste les questions, pas besoin de commenter"
        )

        questions = response.text.split("\n") if response.text else ["Aucune question générée."]
        return questions

    def categorize_skills(self, text_offre: str) -> str:
        """Categorize skills using Kano model."""
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
                        "Catégorise les compétences en fonction du modèle de Kano "
                        "(Indispensable, Proportionnelle, Attractive, Indifférente). "
                        "Donne juste les compétences classées sans explication ni commentaire. "
                        "Enléve aussi les notes",
                    ],
                }
            ]
        )

        response = chat_session.send_message(
            "Catégorise les compétences selon le modèle de Kano sans note ni commentaire."
        )
        
        return response.text if response.text else "Aucune réponse générée."
