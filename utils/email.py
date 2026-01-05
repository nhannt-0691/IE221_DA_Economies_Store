import random
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
from accounts.models import EmailOTP


def send_verification_email(request, user):
    verification_code = str(random.randint(100000, 999999))
    
    EmailOTP.objects.update_or_create(
        user=user,
        defaults={
            "otp": verification_code,
            "expires_at": timezone.now() + timedelta(minutes=5)
        }
    )

    subject = "Verify Your Email Address"

    html_content = render_to_string(
        "verify_account.html",
        {
            "user": user,
            "verification_code": verification_code,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

def send_reset_password_email(request, user):
    verification_code = str(random.randint(100000, 999999))
    
    EmailOTP.objects.update_or_create(
        user=user,
        defaults={
            "otp": verification_code,
            "expires_at": timezone.now() + timedelta(minutes=5)
        }
    )

    subject = "Reset Your Password"

    html_content = render_to_string(
        "reset_password.html",
        {
            "user": user,
            "verification_code": verification_code,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

def send_order_email(request, user):
    subject = "Order successfully!"

    html_content = render_to_string(
        "order_success.html",
        {
            "user": user
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

def send_locked_email(request, user):
    subject = "Notification: Locked account!"

    html_content = render_to_string(
        "locked_account.html",
        {
            "user": user
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
    