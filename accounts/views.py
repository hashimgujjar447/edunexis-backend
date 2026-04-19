import hashlib
import random
import threading
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.shortcuts import get_object_or_404

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .throttles import RegisterThrottle,ResetConfirmThrottle,VerifyThrottle

from .serializers import (
    RegisterSerializer,
    RequestPasswordSerializer,
    PasswordResetConfirmSerializer,
    RegisterationTokenVerifySerializer,
    RequestRegisterationCodeSerializer,
    UserDetailSerializer
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
    throttle_classes=[RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        user = Account.objects.filter(email=email).first()

        if user:
            if user.is_active:
                return Response({"message": "Account already exists"}, status=400)
        else:
            user = serializer.save()

      
        UserToken.objects.filter(
            user=user,
            token_type='email_verification',
            is_used=False
        ).update(is_used=True)

       
        otp_code = str(random.randint(100000, 999999))
        hashed_otp = hashlib.sha256(otp_code.encode()).hexdigest()

        UserToken.objects.create(
            user=user,
            token_type='email_verification',
            token=hashed_otp,
            expires_at=timezone.now() + timedelta(minutes=15),
            attempts=0
        )

        send_email_async(send_verification_code, user.email, otp_code)

        return Response(
            {"message": "Verification code sent"},
            status=201
        )



from django.contrib.auth import authenticate

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)

        # ❌ invalid credentials
        if not user:
            return Response(
                {"message": "Invalid credentials"},
                status=401
            )

        print(user.id)
        # 🚫 inactive user block
        if not user.is_active:
            return Response(
                {"message": "Please verify your email"},
                status=400
            )

        # ✅ now generate tokens
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            refresh = response.data.get("refresh")
            access = response.data.get("access")

            res = Response({"access": access}, status=200)

            res.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                secure=False,  # testing
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
            )

            return res

        return response



class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get("refresh_token")

        if not refresh:
            return Response(
                {"error": "No refresh token"},
                status=401
            )

        serializer = self.get_serializer(data={"refresh": refresh})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=401
            )

        return Response({"access": serializer.validated_data["access"]})



class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie("refresh_token")
        return response



class RequestPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        token_type = serializer.validated_data["token_type"]

        user = Account.objects.filter(email=email).first()

      
        if not user:
            return Response(
                {"message": "If account exists, email sent"},
                status=200
            )

       
        UserToken.objects.filter(
            user=user,
            token_type=token_type,
            is_used=False
        ).update(is_used=True)

        expiry = timezone.now() + timedelta(minutes=15)
        raw_token, hashed_token = generate_secure_token()

        UserToken.objects.create(
            user=user,
            token=hashed_token,
            token_type=token_type,
            expires_at=expiry,
            attempts=0
        )

        send_email_async(send_password_reset_token, user.email, raw_token)

        return Response({"message": "If account exists, email sent"}, status=200)



class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResetConfirmThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            raw_token = request.data.get("token")

            if raw_token:
                hashed = hashlib.sha256(raw_token.encode()).hexdigest()

                token = UserToken.objects.filter(
                    token=hashed,
                    token_type="reset_password",
                    is_used=False
                ).first()

                if token:
                    if token.attempts >= 5:
                        token.is_used = True
                        token.save(update_fields=["is_used"])

                        return Response(
                            {"message": "Too many attempts"},
                            status=429
                        )

                    token.attempts += 1
                    token.save(update_fields=["attempts"])

            return Response(serializer.errors, status=400)

        token_obj = serializer.validated_data["token_obj"]
        password = serializer.validated_data["password"]

        if token_obj.attempts >= 5:
            return Response({"message": "Too many attempts"}, status=429)

        with transaction.atomic():
            user = token_obj.user
            user.set_password(password)
            user.save()

            token_obj.is_used = True
            token_obj.save(update_fields=["is_used"])

        return Response({"message": "Password changed successfully"})


# 🔐 VERIFY EMAIL
class VerifyRegisterationCode(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [VerifyThrottle]

    def post(self, request):
        serializer = RegisterationTokenVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        user = Account.objects.filter(email=email, is_active=False).first()

        if not user:
            return Response({"message": "No Account with email available please register"}, status=400)

        token = UserToken.objects.filter(
            user=user,
            token_type='email_verification',
            is_used=False
        ).first()

        if not token:
            return Response({"message": "Invalid code"}, status=400)

        if token.is_expired():
            return Response({"message": "Token expired"}, status=400)

        if token.attempts >= 5:
            token.is_used = True
            token.save(update_fields=["is_used"])

            return Response(
                {"message": "Too many attempts. Request new code"},
                status=429
            )

        hashed = hashlib.sha256(code.encode()).hexdigest()

        if token.token != hashed:
            token.attempts += 1
            token.save(update_fields=["attempts"])

            return Response({"message": "Invalid code"}, status=400)

        with transaction.atomic():
            user.is_active = True
            user.save(update_fields=["is_active"])

            token.is_used = True
            token.save(update_fields=["is_used"])

        return Response({"message": "User verified successfully"})
    

class RequestVerificationCode(APIView):

    permission_classes=[AllowAny]

    def post(self,request):
        serializer=RequestRegisterationCodeSerializer(data=request.data)
        if serializer.is_valid():
            email=serializer.validated_data["email"]
            print(email)
            user=Account.objects.filter(email=serializer.validated_data["email"]).first()
            print(user)
            if not user:
                return Response(
                    {"message": "If account exists, email sent"},
                    status=200
                )

           
            if user.is_active:
                return Response(
                    {"message": "Account already verified"},
                    status=400
                )
           


            token = UserToken.objects.filter(
                user=user,
                token_type="email_verification",
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
   
            if token:
                token.is_used = True
                token.save(update_fields=["is_used"])
            otp_code = str(random.randint(100000, 999999))
            hashed_code=hashlib.sha256(otp_code.encode()).hexdigest()
            expiry=timezone.now() + timedelta(minutes=15)

            UserToken.objects.create(
                user=user,
                token=hashed_code,
                token_type='email_verification',
                attempts=0,
                 expires_at=expiry
            )


            send_email_async(send_verification_code, user.email, otp_code)

            return Response({"message":"Code send again please check your email"})

        return Response(serializer.errors,status=400)    
            

class UserProfileApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)

        return Response({
            "message": "Profile fetched",
            "data": serializer.data
        })