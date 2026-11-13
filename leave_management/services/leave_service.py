from datetime import date
from leave_management.models import AuditLog, LeaveRequest, Entitlement
from django.db import transaction
from .util import calculate_working_days
from .entitlement_service import EntitlementCalculations
from django.core.exceptions import ValidationError

#This service class handles the business logic related to leave requests, including calculations for leave days taken, remaining leave, and managing the approval or rejection of leave requests.


#This class provides methods to calculate leave days taken, remaining leave, pending leave count, and upcoming leave for a user.
class LeaveCalculations:

    def calculate_days_taken(self, start_date, end_date):
        return calculate_working_days(start_date, end_date)

#Function returns the number of leave days already used or reserved by a user in a specific holiday year
#The value is stored directly in the Entitlement model and includes both approved and pending leave requests.
    def get_days_taken(self, user, holiday_year=None):
        if holiday_year is None:
            holiday_year = date.today().year

        entitlement = Entitlement.objects.get(user=user, holiday_year=holiday_year)

        return entitlement.days_taken

#Function returns the number of leave days remaining for a user in a specific holiday year
#The value is calculated by subtracting the days taken from the total entitlement for that year.
    def get_remaining_leave(self, user):
        current_year = date.today().year

        entitlement = Entitlement.objects.get(user=user, holiday_year=current_year)

        return (entitlement.total_entitlement - entitlement.days_taken)


    def get_pending_leave_count(self, user):
        return LeaveRequest.objects.filter(
            user=user,
            status="Pending"
        ).count()

    def get_upcoming_leave(self, user):
        today = date.today()

        return LeaveRequest.objects.filter(
            user=user,
            start_date__gte=today
        ).order_by("start_date")[:6]

#This class provides methods to create, approve and reject leave requests including logging actions in the AuditLog model
class LeaveRequestService:

 #Function for user to request leave, checks for sufficient leave balance, updates entitlement and logs the action in the AuditLog model.
 #Pending leave requests are counted towards the days taken so users cannot submit requests that exceed their entitlement when combined with pending requests.
 #Only annual leave requests affect the entitlement balance, any other leave types don't.   
    @staticmethod
    @transaction.atomic # DjangoDB feature that ensures either all operations succeed or none do.
    def create_leave_request(user, cleaned_data):

        start_date = cleaned_data["start_date"]
        end_date = cleaned_data["end_date"]
        leave_type = cleaned_data["leave_type"]

        requested_days = calculate_working_days(start_date, end_date)

        holiday_year = start_date.year
        entitlement = Entitlement.objects.get(user=user, holiday_year=holiday_year)

        remaining = entitlement.total_entitlement - entitlement.days_taken

        if leave_type == "Annual" and requested_days > remaining:
            raise ValidationError(f"Insufficient leave balance. Requested: {requested_days}, Remaining: {remaining}")


        if leave_type == "Annual":
            entitlement.days_taken += requested_days
            entitlement.save()

        leave_request = LeaveRequest(
            user=user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
        )

        if leave_type == "Special":
            special_leave_reason = cleaned_data.get("special_leave_reason")

            if special_leave_reason and special_leave_reason.name == "Other":
                leave_request.other_special_leave = cleaned_data.get("other_special_leave")

            else:
                leave_request.special_leave_type = special_leave_reason

        leave_request.save()

        AuditLog.objects.create(
            action=f"Submitted Leave Request: {leave_request.id}",
            performed_by=user,
        )

        return leave_request

    @staticmethod
    @transaction.atomic
    def approve_leave_request(leave_request, approver):
        if leave_request.status != "Pending":
            raise ValidationError("Only pending leave requests can be approved.")
        leave_request.status = "Approved"
        leave_request.approved_by = approver
        leave_request.approved_at = date.today()
        leave_request.save()

        AuditLog.objects.create(
            action=f"Approved Leave Request: {leave_request.id}",
            performed_by=approver,
        )

        return leave_request

#Function to reject a leave request, restoring the entitlement that was reserved when the request was submitted and logging the action in the AuditLog model.
    @staticmethod
    @transaction.atomic
    def reject_leave_request(leave_request, approver, rejection_reason):
        if leave_request.status != "Pending":
            raise ValidationError("Only pending leave requests can be approved.")
        if leave_request.leave_type =="Annual":
            entitlement = Entitlement.objects.get(user=leave_request.user, holiday_year=leave_request.start_date.year)
            entitlement.days_taken -= (leave_request.total_days)

            entitlement.save()

        leave_request.status = "Rejected"
        leave_request.rejected_by = approver
        leave_request.rejected_at = date.today()
        leave_request.rejection_reason = rejection_reason
        leave_request.save()

        AuditLog.objects.create(
            action=f"Rejected Leave Request: {leave_request.id}",
            performed_by = approver,
            )

        return leave_request



        
        


