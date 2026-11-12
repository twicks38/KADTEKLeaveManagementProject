from django import forms
from django.contrib.auth.models import Group, User

from hr_management.models import Team


class UserManagementForm(forms.Form):
    username = forms.CharField(
        max_length=150
    )

    first_name = forms.CharField(
        max_length=150
    )

    last_name = forms.CharField(
        max_length=150
    )

    email = forms.EmailField()

    job_title = forms.CharField(
        max_length=255
    )

    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        )
    )

    working_days = forms.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0.5,
        max_value=7,
        required=False
    )

    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.none()
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        self.fields["team"].queryset = (
            Team.objects
            .all()
            .order_by("name")
        )

        self.fields["role"].queryset = (
            Group.objects
            .all()
            .order_by("name")
        )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        existing_users = User.objects.filter(
            username__iexact=username
        )

        if self.user:
            existing_users = existing_users.exclude(
                id=self.user.id
            )

        if existing_users.exists():
            raise forms.ValidationError(
                "A user with this username already exists."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        existing_users = User.objects.filter(
            email__iexact=email
        )

        if self.user:
            existing_users = existing_users.exclude(
                id=self.user.id
            )

        if existing_users.exists():
            raise forms.ValidationError(
                "A user with this email address already exists."
            )

        return email


class CreateUserForm(UserManagementForm):
    temporary_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(
            render_value=True
        )
    )


class ModifyUserForm(UserManagementForm):
    pass