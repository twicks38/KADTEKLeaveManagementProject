from datetime import date

from hr_management.models import TeamMembership, PasswordResetRequest
from leave_management.models import LeaveRequest

from leave_management.services.entitlement_service import (
    EntitlementCalculations,
)
from leave_management.services.leave_service import (
    LeaveCalculations,
)

from accounts.models import ProfileChangeRequest


class ProfileService:

    # ==================================================
    # Profile overview
    # ==================================================

    @staticmethod
    def get_overview(user):
        leave_calculations = LeaveCalculations()
        entitlement_calculations = EntitlementCalculations()

        entitlement = (
            entitlement_calculations
            .check_entitlement_record(user)
        )

        team_membership = (
            TeamMembership.objects
            .filter(
                user=user,
                active=True
            )
            .select_related("team")
            .first()
        )

        return {
            "profile": user.profile,
            "team_membership": team_membership,
            "role_names": ", ".join(
                user.groups.values_list(
                    "name",
                    flat=True
                )
            ) or "Not assigned",
            "total_entitlement": entitlement.total_entitlement,
            "days_taken": leave_calculations.get_days_taken(user),
            "remaining_leave": leave_calculations.get_remaining_leave(user),
            "pending_leave": leave_calculations.get_pending_leave_count(user),
        }


    # ==================================================
    # Employment details
    # ==================================================

    @staticmethod
    def get_employment_details(user):
        team_membership = (
            TeamMembership.objects
            .filter(
                user=user,
                active=True
            )
            .select_related(
                "team",
                "team__manager"
            )
            .first()
        )

        return {
            "profile": user.profile,
            "team_membership": team_membership,
            "role_names": ", ".join(
                user.groups.values_list(
                    "name",
                    flat=True
                )
            ) or "Not assigned",
        }


    # ==================================================
    # Leave details
    # ==================================================

    @staticmethod
    def get_leave_details(user):
        leave_calculations = LeaveCalculations()
        entitlement_calculations = EntitlementCalculations()

        entitlement = (
            entitlement_calculations
            .check_entitlement_record(user)
        )

        return {
            "profile": user.profile,
            "holiday_year": date.today().year,
            "total_entitlement": entitlement.total_entitlement,
            "days_taken": leave_calculations.get_days_taken(user),
            "remaining_leave": leave_calculations.get_remaining_leave(user),
            "pending_leave": leave_calculations.get_pending_leave_count(user),
        }

    # ==================================================
    # User requests
    # ==================================================

    @staticmethod
    def get_requests(user):

        leave_requests = (
            LeaveRequest.objects
            .filter(user=user)
            .order_by("-created_at")
        )

        password_reset_requests = (
            PasswordResetRequest.objects
            .filter(user=user)
            .order_by("-requested_at")
        )

        profile_change_requests = (
            ProfileChangeRequest.objects
            .filter(user=user)
            .select_related("requested_team")
            .order_by("-requested_at")
        )

        return {
            "leave_requests": leave_requests,
            "password_reset_requests": password_reset_requests,
            "profile_change_requests": profile_change_requests,
        }

    # ==================================================
    # Profile change request details
    # ==================================================

    @staticmethod
    def get_change_request_details(user):
        current_membership = (
            TeamMembership.objects
            .filter(
                user=user,
                active=True
            )
            .select_related("team")
            .first()
        )

        return {
            "current_team": (
                current_membership.team
                if current_membership
                else None
            ),
        }