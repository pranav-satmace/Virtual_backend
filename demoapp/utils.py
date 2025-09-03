import re
from django.core.mail import send_mail

# --- Helpers + signals to auto-create and auto-assign short codes for teneant and reporting tenant ---

def _prefix_from_name(text: str) -> str:
    """Take first 3 alphanumerics of name, uppercased; pad with X if shorter."""
    cleaned = re.sub(r'[^A-Za-z0-9]', '', (text or '')).upper()
    return (cleaned[:3] or 'XXX').ljust(3, 'X')

# def _next_running(model, prefix: str) -> str:
#     """Generate next AAA### code for the given model."""
#     last = model.objects.filter(short_code__startswith=prefix).order_by('-short_code').first()
#     n = int(last.short_code[-3:]) + 1 if last else 1
#     return f'{prefix}{n:03d}'

# utils.py
def _next_running(model, prefix: str, field: str = "short_code") -> str:
    """
    Generate next AAA### code for the given model.
    Works for any field (short_code or short_name)
    """
    filter_kwargs = {f"{field}__startswith": prefix}
    last = model.objects.filter(**filter_kwargs).order_by(f"-{field}").first()
    n = int(getattr(last, field)[-3:]) + 1 if last else 1
    return f"{prefix}{n:03d}"


def send_email_otp(to_email: str, code: int):
    subject = 'Your Virtual IO verification code'
    message = f'Your verification code is: {code}\nIt expires in 10 minutes.'
    send_mail(subject, message, None, [to_email], fail_silently=False)