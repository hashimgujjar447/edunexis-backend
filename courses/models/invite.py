from django.db import models
from accounts.models import Account
from courses.models.course import Course

class CourseInstructorInvite(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    invited_user = models.ForeignKey(Account, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="sent_invites")

    status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ),
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["course", "invited_user"]