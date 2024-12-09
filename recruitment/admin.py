from django.contrib import admin

from .models import Candidate, CV, JobOffer, Result, Interview

admin.site.register(Candidate)
admin.site.register(CV)
admin.site.register(JobOffer)
admin.site.register(Result)
admin.site.register(Interview)
