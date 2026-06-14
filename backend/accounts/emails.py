from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .tokens import (
    make_email_verify_token,
    make_password_reset_token,
    make_invite_token,
    make_parent_invite_token,
)


@shared_task
def send_verification_email(user_id, email, first_name):
    token = make_email_verify_token(user_id)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_mail(
        subject='Verify your CBC Guidance account',
        message=(
            f"Hi {first_name},\n\n"
            f"Please verify your email address by clicking the link below:\n\n"
            f"{verify_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"If you did not create an account, please ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )


@shared_task
def send_password_reset_email(user_id, email, first_name):
    token = make_password_reset_token(user_id)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    send_mail(
        subject='Reset your CBC Guidance password',
        message=(
            f"Hi {first_name},\n\n"
            f"Click the link below to reset your password:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in 1 hour.\n\n"
            f"If you did not request a password reset, please ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )


@shared_task
def send_staff_invite_email(invitee_email, role):
    token = make_invite_token(email=invitee_email, role=role)
    accept_url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    role_display = role.replace('_', ' ').title()
    send_mail(
        subject=f'You have been invited to CBC Guidance as {role_display}',
        message=(
            f"You have been invited to join CBC Career Guidance as a {role_display}.\n\n"
            f"Click the link below to accept the invitation and set up your account:\n\n"
            f"{accept_url}\n\n"
            f"This invitation expires in 48 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitee_email],
    )


@shared_task
def send_parent_invite_email(student_id, parent_email, student_name):
    token = make_parent_invite_token(student_id=student_id, email=parent_email)
    accept_url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    send_mail(
        subject=f'{student_name} has invited you to CBC Guidance',
        message=(
            f"{student_name} has invited you to join CBC Career Guidance to view "
            f"their career pathway recommendations.\n\n"
            f"Click the link below to create your parent account:\n\n"
            f"{accept_url}\n\n"
            f"This invitation expires in 48 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[parent_email],
    )
