import re
from nltk.corpus import stopwords
from pdfminer.high_level import extract_text
import nltk
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import google.generativeai as genai
import random
import string
import os

# Configuration NLTK
nltk.download('stopwords')
stop_words = set(stopwords.words('french') + stopwords.words('english'))

# Configuration Gemini
genai.configure(api_key=settings.GENAI_API_KEY)
generation_config = {
    "temperature": 0.7,
    "max_output_tokens": 512,
    "top_p": 0.95,
    "top_k": 50
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",  
    generation_config=generation_config,
)

def preprocess_text(text):
    """Prétraitement du texte : minuscules, suppression des caractères spéciaux et des stopwords."""
    text = text.lower()
    text = re.sub(r'\W+', ' ', text)
    tokens = text.split()
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

def extract_text_from_pdf(pdf_file):
    """Extraction du texte d'un fichier PDF."""
    try:
        text = extract_text(pdf_file)
        return text
    except Exception as e:
        print("Erreur lors de l'extraction du texte du PDF:", e)
        return ""

def is_valid_email(email):
    """Vérifie si l'adresse e-mail a un format valide."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def generate_random_code(length=6):
    """Génère un code aléatoire de 6 caractères."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_interview_email(recipient, subject, message_body, profil):
    """
    Envoie un email avec Django's email system.
    """
    code = generate_random_code()
    message_body_with_code = f"{message_body}\n\nVoici votre code d'entretien : {code}"
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=message_body_with_code,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient]
    )
    
    try:
        email.send()
        return code
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return None

def generate_questionnaire(profile_info):
    """
    Génère un questionnaire d'entretien basé sur le profil et les compétences du candidat.
    """
    prompt = f"""En tant que recruteur expérimenté, générez un questionnaire d'entretien pertinent pour un candidat avec le profil suivant:
    
    Profil: {profile_info}
    
    Générez 5 questions techniques et 3 questions comportementales appropriées pour ce profil.
    Format de sortie souhaité:
    Questions Techniques:
    1. ...
    2. ...
    
    Questions Comportementales:
    1. ...
    2. ...
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erreur lors de la génération du questionnaire: {e}")
        return None

def categorize_skills_with_kano(text_offre):
    """
    Utilise Gemini AI pour catégoriser les compétences selon le modèle de Kano.
    """
    prompt = f"""Analysez le texte suivant et catégorisez les compétences selon le modèle de Kano:

    {text_offre}

    Catégories:
    - Indispensable: compétences essentielles
    - Attractive: compétences qui apportent une valeur ajoutée
    - Proportionnelle: compétences dont l'importance augmente avec le niveau
    - Indifférent: compétences non cruciales
    - Double-tranchant: compétences qui peuvent être positives ou négatives

    Format JSON souhaité:
    {{"Indispensable": ["comp1", "comp2"], "Attractive": ["comp3"]...}}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erreur lors de la catégorisation des compétences: {e}")
        return None
