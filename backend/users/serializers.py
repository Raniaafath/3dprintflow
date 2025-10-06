from django.contrib.auth import get_user_model
from django.db import IntegrityError
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from core.models import Membership, Workspace


User = get_user_model()


class WorkspaceRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    workspace_name = serializers.CharField(max_length=150)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = False

    def validate_email(self, value):
        value = super().validate_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_workspace_name(self, value):
        if Workspace.objects.filter(name=value).exists():
            raise serializers.ValidationError("A workspace with this name already exists.")
        return value

    def get_cleaned_data(self):
        cleaned_data = super().get_cleaned_data()
        cleaned_data["workspace_name"] = self.validated_data.get("workspace_name")
        cleaned_data["username"] = self.validated_data.get("username") or ""
        return cleaned_data

    def custom_signup(self, request, user):
        workspace = Workspace.objects.create(
            name=self.cleaned_data["workspace_name"],
            owner=user,
        )
        Membership.objects.create(user=user, workspace=workspace, role=Membership.OWNER)
        return user

    def save(self, request):
        try:
            return super().save(request)
        except IntegrityError as exc:
            raise serializers.ValidationError({"email": "A user with this email already exists."}) from exc
