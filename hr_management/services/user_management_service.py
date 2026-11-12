from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import Q

from hr_management.models import Team, TeamMembership


class UserManagementService:

    # ==================================================
    # Retrieve filtered users
    # ==================================================

    @staticmethod
    def get_users(
        search=None,
        status=None,
        team=None,
        role=None
    ):
        users = (
            User.objects
            .select_related("profile")
            .prefetch_related("groups")
        )

        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        if status == "active":
            users = users.filter(is_active=True)

        elif status == "disabled":
            users = users.filter(is_active=False)

        if role:
            users = users.filter(
                groups__id=role
            )

        memberships = (
            TeamMembership.objects
            .filter(active=True)
            .select_related("team")
        )

        if team:
            memberships = memberships.filter(
                team_id=team
            )

        membership_by_user = {
            membership.user_id: membership
            for membership in memberships
        }

        if team:
            users = users.filter(
                id__in=membership_by_user.keys()
            )

        users = (
            users
            .distinct()
            .order_by("username")
        )

        return [
            {
                "user": user,
                "profile": getattr(
                    user,
                    "profile",
                    None
                ),
                "team_membership": (
                    membership_by_user.get(user.id)
                ),
                "roles": list(
                    user.groups.all()
                ),
                "role_names": ", ".join(
                    group.name
                    for group in user.groups.all()
                ) or "Not assigned",
            }
            for user in users
        ]

    # ==================================================
    # Retrieve user filter options
    # ==================================================

    @staticmethod
    def get_user_filter_options():
        return {
            "teams": (
                Team.objects
                .all()
                .order_by("name")
            ),
            "roles": (
                Group.objects
                .all()
                .order_by("name")
            ),
        }

    # ==================================================
    # Assign user role
    # ==================================================

    @staticmethod
    @transaction.atomic
    def assign_user_role(user, role):
        """
        Replace the user's existing application roles with
        the selected role and synchronise the active team
        membership's legacy role field.
        """

        if not isinstance(role, Group):
            role = Group.objects.get(id=role)

        user.groups.clear()
        user.groups.add(role)

        active_membership = (
            TeamMembership.objects
            .select_for_update()
            .filter(
                user=user,
                active=True
            )
            .first()
        )

        if active_membership:
            active_membership.save(
                update_fields=["role"]
            )

        return role

    # ==================================================
    # Assign user team
    # ==================================================

    @staticmethod
    @transaction.atomic
    def assign_user_team(user, team, role):
        """
        Deactivate an existing team membership and create a
        new membership with the selected team and role.
        """

        if not isinstance(team, Team):
            team = Team.objects.get(id=team)

        if not isinstance(role, Group):
            role = Group.objects.get(id=role)

        TeamMembership.objects.filter(
            user=user,
            active=True
        ).update(
            active=False
        )

        membership = TeamMembership.objects.create(
            user=user,
            team=team,
            active=True
        )

        UserManagementService.assign_user_role(
            user=user,
            role=role,
        )

        return membership