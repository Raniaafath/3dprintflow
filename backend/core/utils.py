# core/utils.py
from .models import Membership, Workspace

def user_workspaces(user):
    return Workspace.objects.filter(memberships__user=user)

def enforce_workspace(queryset, workspace_id, user):
    # ensure user belongs to the workspace before filtering
    if not Membership.objects.filter(user=user, workspace_id=workspace_id).exists():
        return queryset.none()
    return queryset.filter(workspace_id=workspace_id)
