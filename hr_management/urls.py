from . import views
from django.urls import path

app_name = 'hr_management'

urlpatterns = [
    path('', views.hr_management, name='hr_dashboard'),

    # Password Resets
    path('passwords_requests', views.password_reset_requests, name='password_reset_requests'),
    path(
        "password-reset-requests/<int:reset_id>/reset/",
        views.reset_user_password,
        name="reset_user_password"
    ),
    path(
        "password-reset-requests/<int:reset_id>/reject/",
        views.reject_password_reset,
        name="reject_password_reset"
    ),
    # End

    # Profile Changes
    path(
        "profile-change-requests/",
        views.profile_change_requests,
        name="profile_change_requests"
    ),
    path(
        "profile-change-requests/<int:request_id>/approve/",
        views.approve_profile_change,
        name="approve_profile_change"
    ),
    path(
        "profile-change-requests/<int:request_id>/reject/",
        views.reject_profile_change,
        name="reject_profile_change"
    ),
    # End

    # User Management
    path(
        "users/",
        views.user_list,
        name="user_list"
    ),
    path(
        "users/create/",
        views.create_user,
        name="create_user"
    ),
    path(
        "users/<int:user_id>/modify/",
        views.modify_user,
        name="modify_user"
    ),
    path(
        "users/<int:user_id>/status/",
        views.change_user_status,
        name="change_user_status"
    ),
    
]