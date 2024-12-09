from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('profil', models.TextField(primary_key=True)),
                ('question', ArrayField(models.TextField(), null=True)),
            ],
            options={
                'db_table': 'entretien',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('user_id', models.AutoField(primary_key=True)),
                ('mail', models.CharField(max_length=255, null=True)),
                ('numero_tlfn', models.CharField(max_length=255, null=True)),
                ('code', models.TextField(null=True)),
                ('nom_prenom', models.CharField(max_length=255, null=True)),
                ('profil', models.ForeignKey('Interview', on_delete=models.SET_NULL, null=True, db_column='profil')),
            ],
            options={
                'db_table': 'candidat',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CV',
            fields=[
                ('cv_id', models.AutoField(primary_key=True)),
                ('date_insertion', models.DateTimeField(auto_now_add=True)),
                ('cv_text', models.TextField(null=True)),
                ('competences', ArrayField(models.TextField(), null=True)),
                ('user', models.ForeignKey('Candidate', on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)),
            ],
            options={
                'db_table': 'cv',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='JobOffer',
            fields=[
                ('offre_id', models.AutoField(primary_key=True)),
                ('text_offre', models.TextField(null=True)),
                ('offre_societe', models.TextField(null=True)),
                ('titre', models.TextField(null=True)),
            ],
            options={
                'db_table': 'offre',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('resultat_id', models.AutoField(primary_key=True)),
                ('cosine_similarity', models.DecimalField(max_digits=10, decimal_places=4, null=True)),
                ('score_entretien', models.DecimalField(max_digits=10, decimal_places=4, null=True)),
                ('reponse_entretien', ArrayField(models.TextField(), null=True)),
                ('cv', models.ForeignKey('CV', on_delete=models.CASCADE, db_column='cv_id')),
                ('job_offer', models.ForeignKey('JobOffer', on_delete=models.CASCADE, db_column='offre_id')),
            ],
            options={
                'db_table': 'resultat',
                'managed': False,
            },
        ),
    ]
