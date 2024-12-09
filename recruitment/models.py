from django.db import models
from django.contrib.postgres.fields import ArrayField

class Interview(models.Model):
    profil = models.TextField(primary_key=True)
    question = ArrayField(models.TextField(), null=True)

    class Meta:
        db_table = 'entretien'
        managed = False

    def __str__(self):
        return f"Entretien pour le profil {self.profil}"

class Candidate(models.Model):
    user_id = models.AutoField(primary_key=True)
    mail = models.CharField(max_length=255, null=True)
    numero_tlfn = models.CharField(max_length=255, null=True)
    profil = models.ForeignKey(Interview, on_delete=models.SET_NULL, null=True, db_column='profil')
    code = models.TextField(null=True)
    nom_prenom = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'candidat'
        managed = False

    def __str__(self):
        return self.nom_prenom or "Candidat sans nom"

class CV(models.Model):
    cv_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Candidate, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    date_insertion = models.DateTimeField(auto_now_add=True)
    cv_text = models.TextField(null=True)
    competences = ArrayField(models.TextField(), null=True)

    class Meta:
        db_table = 'cv'
        managed = False

    def __str__(self):
        return f"CV de {self.user.nom_prenom if self.user else 'Utilisateur inconnu'} (ID: {self.cv_id})"

class JobOffer(models.Model):
    offre_id = models.AutoField(primary_key=True)
    text_offre = models.TextField(null=True)
    offre_societe = models.TextField(null=True)
    titre = models.TextField(null=True)

    class Meta:
        db_table = 'offre'
        managed = False

    def __str__(self):
        return self.titre or "Offre sans titre"

class Result(models.Model):
    resultat_id = models.AutoField(primary_key=True)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, db_column='cv_id')
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, db_column='offre_id')
    cosine_similarity = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    score_entretien = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    reponse_entretien = ArrayField(models.TextField(), null=True)

    class Meta:
        db_table = 'resultat'
        managed = False

    def __str__(self):
        return f"Résultat pour CV {self.cv.cv_id} et Offre {self.job_offer.offre_id}"
