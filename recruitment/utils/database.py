from recruitment.models import Candidate, CV, JobOffer, Result, Interview
from django.core.exceptions import ObjectDoesNotExist

# Gestion des candidats
def save_to_user(nom_prenom, mail, numero_tlfn):
    """
    Enregistre un candidat dans la base de données.
    """
    candidate = Candidate.objects.create(
        full_name=nom_prenom,
        email=mail,
        phone_number=numero_tlfn
    )
    return candidate.user_id

def get_all_candidates():
    """
    Retourne tous les candidats sous forme de dictionnaires.
    """
    candidates = Candidate.objects.all()
    return [
        {
            "user_id": c.user_id,
            "nom_prenom": c.full_name,
            "mail": c.email,
            "numero_tlfn": c.phone_number,
            "profil": c.profile
        } for c in candidates
    ]

def update_candidate(user_id, updated_data):
    """
    Met à jour les informations d'un candidat.
    """
    try:
        candidate = Candidate.objects.get(user_id=user_id)
        candidate.full_name = updated_data.get('nom_prenom', candidate.full_name)
        candidate.email = updated_data.get('mail', candidate.email)
        candidate.phone_number = updated_data.get('numero_tlfn', candidate.phone_number)
        candidate.save()
        return candidate.user_id
    except ObjectDoesNotExist:
        return None

# Gestion des CVs
def save_to_cv(user_id, cv_text, competences):
    """
    Enregistre un CV associé à un candidat.
    """
    try:
        candidate = Candidate.objects.get(user_id=user_id)
        cv = CV.objects.create(
            candidate=candidate,
            cv_text=cv_text,
            competences=competences
        )
        return cv.cv_id
    except ObjectDoesNotExist:
        return None

def get_all_cvs():
    """
    Retourne tous les CVs sous forme de dictionnaires.
    """
    cvs = CV.objects.select_related('candidate').all()
    return [
        {
            "cv_id": cv.cv_id,
            "user_id": cv.candidate.user_id,
            "nom_prenom": cv.candidate.full_name,
            "cv_text": cv.cv_text,
            "competences": cv.competences
        } for cv in cvs
    ]

# Gestion des offres d'emploi
def save_to_offre(text_offre, offre_societe, titre):
    """
    Enregistre une offre d'emploi.
    """
    job_offer = JobOffer.objects.create(
        text_offre=text_offre,
        company_name=offre_societe,
        title=titre
    )
    return job_offer.offre_id

def get_all_offres():
    """
    Retourne toutes les offres d'emploi sous forme de dictionnaires.
    """
    offres = JobOffer.objects.all()
    return [
        {
            "offre_id": o.offre_id,
            "text_offre": o.text_offre,
            "offre_societe": o.company_name,
            "titre": o.title
        } for o in offres
    ]

def update_offre(offre_id, updated_data):
    """
    Met à jour les informations d'une offre.
    """
    try:
        job_offer = JobOffer.objects.get(offre_id=offre_id)
        job_offer.text_offre = updated_data.get('text_offre', job_offer.text_offre)
        job_offer.company_name = updated_data.get('offre_societe', job_offer.company_name)
        job_offer.title = updated_data.get('titre', job_offer.title)
        job_offer.save()
        return job_offer.offre_id
    except ObjectDoesNotExist:
        return None

# Gestion des résultats
def save_to_resultat(cv_id, offre_id, cosine_similarity):
    """
    Enregistre un résultat de correspondance entre un CV et une offre.
    """
    try:
        cv = CV.objects.get(cv_id=cv_id)
        job_offer = JobOffer.objects.get(offre_id=offre_id)
        result = Result.objects.create(
            cv=cv,
            job_offer=job_offer,
            cosine_similarity=cosine_similarity
        )
        return result.resultat_id
    except ObjectDoesNotExist:
        return None

def get_all_resultats():
    """
    Retourne tous les résultats sous forme de dictionnaires.
    """
    results = Result.objects.select_related('cv', 'job_offer').all()
    return [
        {
            "resultat_id": r.resultat_id,
            "cv_id": r.cv.cv_id,
            "offre_id": r.job_offer.offre_id,
            "cosine_similarity": r.cosine_similarity
        } for r in results
    ]

# Gestion des entretiens
def save_question(profil, question):
    """
    Enregistre une question associée à un profil dans la table d'entretiens.
    """
    try:
        interview = Interview.objects.get(profile=profil)
        interview.questions = question
        interview.save()
        return interview.profile
    except ObjectDoesNotExist:
        return None

def get_all_profil():
    """
    Retourne tous les profils et leurs questions.
    """
    interviews = Interview.objects.all()
    return [
        {
            "profil": i.profile,
            "questions": i.questions
        } for i in interviews
    ]

def get_empty_profil():
    """
    Retourne les profils sans questions associées.
    """
    interviews = Interview.objects.filter(questions__isnull=True)
    return [{"profil": i.profile} for i in interviews]

def delete_profil(profil_name):
    """
    Supprime un profil spécifique dans la table d'entretiens.
    """
    try:
        interview = Interview.objects.get(profile=profil_name)
        interview.delete()
        return True
    except ObjectDoesNotExist:
        return False

def update_profil_questions(profil, questions):
    """
    Met à jour les questions pour un profil spécifique.
    """
    try:
        interview = Interview.objects.get(profile=profil)
        interview.questions = questions
        interview.save()
        return True
    except ObjectDoesNotExist:
        return False

def get_profil_questions(profil):
    """
    Retourne les questions associées à un profil spécifique.
    """
    try:
        interview = Interview.objects.get(profile=profil)
        return interview.questions
    except ObjectDoesNotExist:
        return None
