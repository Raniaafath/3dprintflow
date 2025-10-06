from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    workspace_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "workspace_name", "username")
        extra_kwargs = {
            "username": {"required": False, "allow_blank": True},
        }

    def validate_workspace_name(self, value):
        from core.models import Workspace

        if Workspace.objects.filter(name=value).exists():
            raise serializers.ValidationError("A workspace with this name already exists.")
        return value

    def create(self, validated_data):
        from core.models import Workspace, Membership

        workspace_name = validated_data.pop("workspace_name")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        workspace = Workspace.objects.create(name=workspace_name, owner=user)
        Membership.objects.create(user=user, workspace=workspace, role=Membership.OWNER)
        return user
