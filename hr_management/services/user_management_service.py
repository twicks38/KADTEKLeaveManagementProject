from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import Q

from hr_management.models import Team, TeamMembership
from accounts.models import UserProfile


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
        Replace the user's existing application role with
        the selected Django group.
        """

        if not isinstance(role, Group):
            role = Group.objects.get(id=role)

        user.groups.clear()
        user.groups.add(role)

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

    # ==================================================
    # Retrieve user for modification
    # ==================================================

    @staticmethod
    def get_user(user_id):
        try:
            return (
                User.objects
                .select_related("profile")
                .prefetch_related("groups")
                .get(id=user_id)
            )

        except User.DoesNotExist:
            raise ValueError(
                "The selected user could not be found."
            )

    # ==================================================
    # Create user
    # ==================================================

    @staticmethod
    @transaction.atomic
    def create_user(data):
        user = User(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            is_active=True,
        )

        user.set_password(
            data["temporary_password"]
        )

        user.full_clean()
        user.save()

        UserProfile.objects.create(
            user=user,
            job_title=data["job_title"],
            start_date=data["start_date"],
            working_days=data["working_days"],
            first_login=True,
        )

        if data["team"]:
            UserManagementService.assign_user_team(
                user=user,
                team=data["team"],
                role=data["role"],
            )
        else:
            UserManagementService.assign_user_role(
                user=user,
                role=data["role"],
            )

        return user

    # ==================================================
    # Modify user
    # ==================================================

    @staticmethod
    @transaction.atomic
    def modify_user(user, data):
        user.username = data["username"]
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.email = data["email"]

        user.full_clean()
        user.save(
            update_fields=[
                "username",
                "first_name",
                "last_name",
                "email",
            ]
        )

        profile, created = (
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "job_title": data["job_title"],
                    "start_date": data["start_date"],
                    "working_days": data["working_days"],
                    "first_login": True,
                }
            )
        )

        if not created:
            profile.job_title = data["job_title"]
            profile.start_date = data["start_date"]
            profile.working_days = data["working_days"]

            profile.save(
                update_fields=[
                    "job_title",
                    "start_date",
                    "working_days",
                ]
            )

        current_membership = (
            TeamMembership.objects
            .select_for_update()
            .filter(
                user=user,
                active=True
            )
            .first()
        )

        selected_team = data["team"]

        if selected_team:
            team_changed = (
                not current_membership
                or current_membership.team_id != selected_team.id
            )

            if team_changed:
                UserManagementService.assign_user_team(
                    user=user,
                    team=selected_team,
                    role=data["role"],
                )

            else:
                UserManagementService.assign_user_role(
                    user=user,
                    role=data["role"],
                )

        else:
            if current_membership:
                current_membership.active = False

                current_membership.save(
                    update_fields=["active"]
                )

            UserManagementService.assign_user_role(
                user=user,
                role=data["role"],
            )

        return user

    # ==================================================
    # Change user's active status
    # ==================================================

    @staticmethod
    @transaction.atomic
    def set_user_status(user, is_active):
        user.is_active = is_active

        user.save(
            update_fields=["is_active"]
        )

        return user