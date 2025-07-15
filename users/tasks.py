from celery import shared_task
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model


@shared_task
def send_course_update_email(course_title: str, user_email: str) -> None:
    subject = f"Обновление курса: {course_title}"
    message = (
        f"Здравствуйте!\n\nМатериалы курса \"{course_title}\" были обновлены. "
        "Зайдите на платформу, чтобы ознакомиться с новыми материалами."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False
    )

User = get_user_model()

@shared_task
def deactivate_inactive_users():
    cutoff_date = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(last_login__lt=cutoff_date, is_active=True)
    count = inactive_users.update(is_active=False)
    return f'Deactivated {count} users who were inactive for over 30 days.'