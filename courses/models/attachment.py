from django.db import models
from django.core.exceptions import ValidationError


class Attachment(models.Model):
    FILE_TYPES = [
        ("pdf", "PDF"),
        ("doc", "Word"),
        ("video", "Video"),
        ("other", "Other"),
    ]

    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="attachments")

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="lesson_attachments/", blank=True, null=True)
    extra_url = models.URLField(blank=True, null=True)

    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default="other")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if not self.file and not self.extra_url:
            raise ValidationError("Either file or URL is required")

        if self.file and self.extra_url:
            raise ValidationError("Provide either file or URL, not both")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title