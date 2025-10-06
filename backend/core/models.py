from django.conf import settings
from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=120, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_workspaces",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or f"Workspace #{self.pk}"


class Membership(models.Model):
    OWNER = "owner"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"

    ROLE_CHOICES = [
        (OWNER, "Owner"),
        (MANAGER, "Manager"),
        (OPERATOR, "Operator"),
        (VIEWER, "Viewer"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=OWNER)

    class Meta:
        unique_together = ("user", "workspace")

    def __str__(self) -> str:
        return f"{self.user.email} → {self.workspace.name} ({self.role})"
