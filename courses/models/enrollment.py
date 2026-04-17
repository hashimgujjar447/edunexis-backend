from django.db import models
from accounts.models import Account
from .course import Course


class Enrollment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="only_one_enrollment_for_user_per_course"
            )
        ]

    def __str__(self):
        return f"{self.user} enrolled in {self.course}"