import hashlib
import random
import threading
from datetime import timedelta
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    RegisterSerializer,
    RequestPasswordSerializer,
    PasswordResetConfirmSerializer
)
from .models import Account, UserToken
from .utils import generate_secure_token, send_password_reset_token, send_verification_code


# 🔥 async email helper
def send_email_async(func, *args, **kwargs):
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.start()


# 🔐 REGISTER
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # inactive until verified
            user.is_active = False
            user.save()

            # 🔢 OTP
            otp_code = str(random.randint(100000, 999999))
            hashed_otp = hashlib.sha256(otp_code.encode()).hexdigest()

            otp_expiry = timezone.now() + timedelta(minutes=15)

            UserToken.objects.create(
                user=user,
                token_type='email_verification',
                token=hashed_otp,
                expires_at=otp_expiry
            )

            # 📧 async email
            send_email_async(send_verification_code, user.email, otp_code)

            return Response(
                {
                    "message": "Verification code sent",
                    "email": user.email
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🔐 LOGIN
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            refresh = response.data.get("refresh")
            access = response.data.get("access")

            res = Response({"access": access}, status=status.HTTP_200_OK)

            res.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
            )

            return res

        return response


# 🔄 REFRESH
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get("refresh_token")

        if not refresh:
            return Response(
                {"error": "No refresh token, please login"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data={"refresh": refresh})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response({
            "access": serializer.validated_data["access"]
        })


# 🚪 LOGOUT
class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie("refresh_token")
        return response


# 🔑 REQUEST PASSWORD RESET
class RequestPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            token_type = serializer.validated_data["token_type"]

            try:
                user = Account.objects.get(email=email)
            except Account.DoesNotExist:
                return Response(
                    {"message": "No account found", "success": False},
                    status=404
                )

            expiry_date = timezone.now() + timedelta(minutes=15)

            raw_token, hashed_token = generate_secure_token()

            UserToken.objects.create(
                user=user,
                token=hashed_token,
                token_type=token_type,
                expires_at=expiry_date
            )

            # 📧 async
            send_email_async(send_password_reset_token, user.email, raw_token)

            return Response({"success": True}, status=200)

        return Response(serializer.errors, status=400)


# 🔐 CONFIRM PASSWORD RESET
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            token_obj = serializer.validated_data["token_obj"]
            password = serializer.validated_data["password"]

            user = token_obj.user
            user.set_password(password)
            user.save()

            token_obj.is_used = True
            token_obj.save()

            return Response(
                {"message": "Password changed successfully"},
                status=200
            )

        return Response(serializer.errors, status=400)