import uuid
import hashlib
import threading
from django.core.mail import send_mail
from django.conf import settings


# 🔐 TOKEN GENERATOR
def generate_secure_token():
    raw_token = str(uuid.uuid4())
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, hashed_token


# 🔥 ASYNC EMAIL HELPER
def send_email_async(func, *args, **kwargs):
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.start()


# 📧 GENERIC EMAIL
def send_email(subject, message, recipient_list):
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print("Email Error:", str(e))
        return False


# 🔐 VERIFICATION EMAIL
def send_verification_code(email, code):
    subject = "Verify Your Account"

    message = f"""
Hi,

Your verification code is:

{code}

Expires in 10 minutes.
"""

    return send_email(subject, message, [email])


# 🔑 PASSWORD RESET EMAIL
def send_password_reset_token(email, token):
    subject = "Reset Your Password"

    message = f"""
Hi,

Your password reset token is:

http://localhost:3000/reset/password/{token}

Expires in 10 minutes.
"""

    return send_email(subject, message, [email])