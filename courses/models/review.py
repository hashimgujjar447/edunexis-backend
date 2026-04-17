from django.db import models
from .course import Course
from accounts.models import Account
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="reviews")

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="user_have_one_review_per_course"
            )
        ]

    def __str__(self):
        return f"{self.user} rated {self.rating}"