from decimal import Decimal, InvalidOperation
from getpass import getpass

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from accounts.models import UserProfile
from leave_management.services.entitlement_service import EntitlementCalculations


class Command(BaseCommand):
    help = "Creates an initial Super HR user for testing. (Not django superuser)"

    # =================================================
    # Get required input
    # =================================================
    def get_required_input(self, prompt):
        while True:
            value = input(prompt).strip()

            if value:
                return value

            self.stdout.write(
                self.style.ERROR(
                    "This field cannot be left blank."
                )
            )

    # ==================================================
    # Validate email
    # ==================================================
    def get_email(self):
        while True:
            email = self.get_required_input(
                "Email: "
            )

            try:
                validate_email(email)
                return email

            except ValidationError:
                self.stdout.write(
                    self.style.ERROR(
                        "Enter a valid email address."
                    )
                )

    # ==================================================
    # Handle command
    # ==================================================

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "Create initial HR Superuser"
            )
        )

        username = self.get_required_input("Username: ")
        email = self.get_email()
        first_name = self.get_required_input("First name: ")
        last_name = self.get_required_input("Last name: ")
        job_title = self.get_required_input("Job title: ")

        # ==================================================
        # Start date
        # ==================================================

        start_date_input = input(
            "Start date (YYYY-MM-DD, leave blank for today): "
        ).strip()

        if start_date_input:
            start_date = parse_date(
                start_date_input
            )

            if not start_date:
                raise CommandError(
                    "Start date must be in YYYY-MM-DD format."
                )

        else:
            start_date = timezone.localdate()

        # ==================================================
        # Working days
        # ==================================================

        while True:
            working_days_input = self.get_required_input(
                "Working days: "
            )

            try:
                working_days = Decimal(working_days_input)

                if (
                    Decimal("0.5")
                    <= working_days
                    <= Decimal("7")
                ):
                    break

                self.stdout.write(
                    self.style.ERROR(
                        "Working days must be between 0.5 and 7."
                    )
                )

            except InvalidOperation:
                self.stdout.write(
                    self.style.ERROR(
                        "Working days must be a number."
                    )
                )

        # ==================================================
        # Duplicate checks
        # ==================================================

        if User.objects.filter(username__iexact=username
        ).exists():
            raise CommandError(
                f"User '{username}' already exists."
            )

        if User.objects.filter(email__iexact=email
        ).exists():
            raise CommandError(
                (
                    f"A user with email "
                    f"'{email}' already exists."
                )
            )

        # ==================================================
        # Password
        # ==================================================

        while True:
            password = getpass("Password: ")

            if not password:
                self.stdout.write(
                    self.style.ERROR(
                        "Password cannot be left blank."
                    )
                )
                continue

            if len(password) < 8:
                self.stdout.write(
                    self.style.ERROR(
                        "Password must contain at least 8 characters."
                    )
                )
                continue

            confirm_password = getpass("Confirm password: ")

            if password != confirm_password:
                self.stdout.write(
                    self.style.ERROR(
                        "Passwords do not match."
                    )
                )
                continue

            break

        # ==================================================
        # HR Superuser role
        # ==================================================

        try:
            role = Group.objects.get(name="HR Superuser")

        except Group.DoesNotExist:
            raise CommandError(
                (
                    "The 'HR Superuser' group does not exist. "
                    "Create or initialise the application's "
                    "groups before running this command."
                )
            )

        # ==================================================
        # Create user
        # ==================================================

        with transaction.atomic():
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )

            user.set_password(password)

            user.full_clean()
            user.save()

            UserProfile.objects.create(
                user=user,
                job_title=job_title,
                start_date=start_date,
                working_days=working_days,
                first_login=False,
            )

            user.groups.add(role)
            EntitlementCalculations().check_entitlement_record(user)

        # ==================================================
        # Success
        # ==================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Super HR '{username}' "
                    "created successfully."
                )
            )
        )