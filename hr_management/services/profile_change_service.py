from django.db import transaction
from django.utils import timezone

from accounts.models import ProfileChangeRequest
from hr_management.models import TeamMembership


class ProfileChangeService:

    # ==================================================
    # Retrieve pending requests
    # ==================================================

    @staticmethod
    def get_pending_requests():
        return (
            ProfileChangeRequest.objects
            .filter(status="Pending")
            .select_related(
                "user",
                "requested_team"
            )
            .order_by("requested_at")
        )

    # ==================================================
    # Approve profile change request
    # ==================================================

    @staticmethod
    @transaction.atomic
    def approve_request(request_id, processed_by):
        try:
            change_request = (
                ProfileChangeRequest.objects
                .select_for_update()
                .select_related(
                    "user",
                    "requested_team"
                )
                .get(
                    id=request_id,
                    status="Pending"
                )
            )

        except ProfileChangeRequest.DoesNotExist:
            raise ValueError(
                "This profile change request does not exist "
                "or has already been processed."
            )

        if change_request.change_type == "Name":
            ProfileChangeService._approve_name_change(change_request)

        elif change_request.change_type == "Team":
            ProfileChangeService._approve_team_change(change_request)

        else:
            raise ValueError(
                "This profile change type is not supported."
            )

        change_request.status = "Approved"
        change_request.processed_by = processed_by
        change_request.processed_at = timezone.now()

        change_request.save(
            update_fields=[
                "status",
                "processed_by",
                "processed_at",
            ]
        )

        return change_request

    # ==================================================
    # Apply name change
    # ==================================================

    @staticmethod
    def _approve_name_change(change_request):
        user = change_request.user

        user.first_name = (change_request.requested_first_name)

        user.last_name = (change_request.requested_last_name)

        user.save(
            update_fields=[
                "first_name",
                "last_name",
            ]
        )

    # ==================================================
    # Apply team change
    # ==================================================

    @staticmethod
    def _approve_team_change(change_request):
        user = change_request.user
        requested_team = change_request.requested_team

        if requested_team is None:
            raise ValueError(
                "No requested team was provided."
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

        if current_membership is None:
            raise ValueError(
                "The user does not currently have an active "
                "team membership."
            )

        if current_membership.team_id == requested_team.id:
            raise ValueError(
                "The user is already assigned to the requested team."
            )

        current_membership.active = False

        current_membership.save(update_fields=["active"])

        TeamMembership.objects.create(
            user=user,
            team=requested_team,
            active=True
        )

    # ==================================================
    # Reject profile change request
    # ==================================================

    @staticmethod
    @transaction.atomic
    def reject_request(request_id, processed_by):
        try:
            change_request = (
                ProfileChangeRequest.objects
                .select_for_update()
                .select_related("user")
                .get(
                    id=request_id,
                    status="Pending"
                )
            )

        except ProfileChangeRequest.DoesNotExist:
            raise ValueError(
                "This profile change request does not exist "
                "or has already been processed."
            )

        change_request.status = "Rejected"
        change_request.processed_by = processed_by
        change_request.processed_at = timezone.now()

        change_request.save(
            update_fields=[
                "status",
                "processed_by",
                "processed_at",
            ]
        )

        return change_request