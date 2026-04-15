from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            refresh = response.data.get("refresh")
            access = response.data.get("access")

            res = Response(
                {"access": access},
                status=status.HTTP_200_OK
            )

            res.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                secure=False,  # 🔴 True in production
                samesite="Lax",  # use "None" with HTTPS
                max_age=7 * 24 * 60 * 60,
                path="/api/accounts/token/refresh/"
            )

            return res

        return response


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



class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie("refresh_token", path="/api/accounts/token/refresh/")
        return response