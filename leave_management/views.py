from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from leave_management.forms.leave_forms import LeaveRequestForm
from leave_management.services.leave_service import LeaveCalculations, LeaveRequestService
from leave_management.services.calendar_service import calendar_service
from leave_management.models import LeaveRequest
from hr_management.models import TeamMembership
from leave_management.services.leave_service import LeaveRequestService


@login_required
def home(request):
    user = request.user
    calculations = LeaveCalculations()

    full_leave_history = LeaveRequest.objects.filter(
        user=user,
        end_date__gte=date.today()
    ).order_by('start_date')[:6]

    context = {
        'days_taken': calculations.get_days_taken(user),
        'remaining_leave': calculations.get_remaining_leave(user),
        'pending_count': calculations.get_pending_leave_count(user),
        'upcoming_leave': calculations.get_upcoming_leave(user),
        'full_leave_history': full_leave_history,
    }

    return render(request, 'accounts/home_page.html', context)

@login_required
def user_leave_requests(request):
    user = request.user

    full_leave_history = LeaveRequest.objects.filter(
        user=user
    ).order_by('-start_date')

    years = LeaveRequest.objects.filter(user=user).dates('start_date', 'year')

    selected_status = request.GET.get('status')
    selected_holiday_year = request.GET.get('holiday_year')
    selected_start = request.GET.get('start_date')
    selected_end = request.GET.get('end_date')

    if selected_status:
        full_leave_history = full_leave_history.filter(status=selected_status)

    if selected_holiday_year:
        full_leave_history = full_leave_history.filter(start_date__year=selected_holiday_year)

    if selected_start:
        full_leave_history = full_leave_history.filter(start_date__gte=selected_start)

    if selected_end:
        full_leave_history = full_leave_history.filter(end_date__lte=selected_end)

    context = {
        'full_leave_history': full_leave_history,
        'years': years,
        'selected_status': selected_status,
        'selected_holiday_year': selected_holiday_year,
        'selected_start': selected_start,
        'selected_end': selected_end,
    }

    return render(request, 'accounts/user_leave_history.html', context)

@login_required
def leave_request_form(request):
    form = LeaveRequestForm(
        request.POST or None,
        user=request.user
    )

    if request.method == "POST" and form.is_valid():
        LeaveRequestService.create_leave_request(
            user=request.user,
            cleaned_data=form.cleaned_data,
        )

        messages.success(
            request,
            "Your leave request has been submitted successfully.",
        )

        return redirect("leave_management:home")

    context = {
        "form": form,
    }

    return render(
        request,
        "accounts/leave_request_form.html",
        context,
    )

@login_required
def personal_calendar(request):
    context = calendar_service(request, False) #passes false for individual calendar
    return render(request, 'leave_management/calendar_page.html', context)


@login_required
def team_calendar(request):
    #Filtering to prevent view running for non managers
    if not request.user.groups.filter(name="Manager").exists():
        return HttpResponseForbidden()


    context = calendar_service(request, True) #passes true to confirm a team calendar
    return render(request, 'leave_management/calendar_page.html', context)


@login_required
def manager_dashboard(request):
    if not request.user.groups.filter(name="Manager").exists():
        return HttpResponseForbidden()

    return render(request, 'leave_management/manager_page.html')


@login_required
def leave_request_approval(request):
    if not request.user.groups.filter(name="Manager").exists():
        return HttpResponseForbidden()

    team = TeamMembership.objects.get(
        user = request.user,
        role__name="Manager",
        active = True
    ).team

    employees = User.objects.filter(
        teammembership__team=team,
        teammembership__active = True
    )

    team_leave = LeaveRequest.objects.filter(
        user__in=employees,
        status="Pending"
    ).exclude(user=request.user).order_by("start_date")


    return render(request, 'leave_management/request_list_page.html', {"team_leave":team_leave})


def view_leave_request(request, leave_id):
    if not request.user.groups.filter(name="Manager").exists():
        return HttpResponseForbidden()

    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    if leave_request.user == request.user:
        return HttpResponseForbidden()
    
    context = calendar_service(request, True, leave_request)
    context["leave_request"] = leave_request


    return render(request, 'leave_management/approval_calendar.html', context)


def approve_leave(request, leave_id):
    leave_request = get_object_or_404(LeaveRequest, id = leave_id)
    LeaveRequestService.approve_leave_request(leave_request, request.user)
    return redirect ('leave_management:manager_dashboard')


def reject_leave(request, leave_id):
    rejection_reason = request.GET.get('rejection_reason_area')
    leave_request = get_object_or_404(LeaveRequest, id = leave_id)
    LeaveRequestService.reject_leave_request(leave_request, request.user, rejection_reason)

    return redirect('leave_management:manager_dashboard')