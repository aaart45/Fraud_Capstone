from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("created_at","risk","confidence","anomaly_score","model_name","version")
    ordering = ("-created_at",)
