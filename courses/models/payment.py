from django.db import models
from accounts.models import Account
from courses.models.course import Course


class Payment(models.Model):

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=8, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        unique_together = ["user", "course"]

    def __str__(self):
        return f"{self.user} - {self.course} - {self.status}"