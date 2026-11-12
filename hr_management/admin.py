from django.contrib import admin
from .models import Team, TeamMembership

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "manager")
    search_fields = ("name", "manager_user_username")
    ordering = ("name",)


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "team",
        "active",
        "date_joined",
    )

    list_filter = (
        "team",
        "active",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "team__name",
    )