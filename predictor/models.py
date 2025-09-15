from django.db import models

class Submission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    input_json = models.JSONField()
    is_fraud = models.BooleanField()
    risk = models.CharField(max_length=10)
    confidence = models.FloatField()
    anomaly_score = models.FloatField()
    model_name = models.CharField(max_length=50)
    version = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} | {self.risk} ({self.confidence:.2f})"
