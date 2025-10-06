from django.contrib import admin

from .models import Workspace, Membership


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__email")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "workspace", "role")
    list_filter = ("role",)
    search_fields = ("user__email", "workspace__name")
