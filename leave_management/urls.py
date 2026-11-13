from . import views
from django.urls import path

app_name = 'leave_management'

urlpatterns = [
    path('', views.home, name='home'),
    path('leave-history/', views.user_leave_requests, name='leave_history'),
    path('leave-request-form/', views.leave_request_form, name = "leave_request_form"),
    path('calendar/', views.personal_calendar, name="personal_calendar"),
    path('team-calendar/', views.team_calendar, name="team_calendar"),
    path('manager-dashboard/', views.manager_dashboard, name="manager_dashboard"),
    path('manager-dashboard/request-list/', views.leave_request_approval, name="request_list"),
    path('manager-dashboard/view-leave-request/<int:leave_id>/', views.view_leave_request, name="view_leave_request"),
    path('manager-dashboard/approve-leave-request/<int:leave_id>/', views.approve_leave, name="approve_leave"),
    path('manager-dashboard/reject-leave-request/<int:leave_id>/', views.reject_leave, name="reject_leave")
]