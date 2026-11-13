from django.db import models
from django.contrib.auth.models import User, Group


# ==================================================
# Team
# ==================================================

class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


# ==================================================
# Team membership
# ==================================================

class TeamMembership(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE
    )
    date_joined = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"({self.user.username} - "
            f"{self.team.name} - "
        )


# ==================================================
# Password reset request
# ==================================================

class PasswordResetRequest(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Rejected", "Rejected"),
    ]

    # User requesting the password reset
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_requests"
    )

    # Date and time the request was submitted
    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    # Current status of the request
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    # To keep a record: 
    # HR Superuser who processed the request
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_password_reset_requests"
    )

    # Date and time the request was processed
    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.status}"