from django.urls import path
from .views import RegisterView,LoginView,RefreshView,LogoutView,RequestPasswordView,PasswordResetConfirmView,VerifyRegisterationCode
urlpatterns=[
    path('register/',RegisterView.as_view()),
       path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshView.as_view(), name='token_refresh'),
      path('logout/', LogoutView.as_view(), name='logout'),

     path('request_reset_password_token/', RequestPasswordView.as_view(), name='reset_password'),
     path('password_reset_confirm/',PasswordResetConfirmView.as_view()),
     path('user/verify/',VerifyRegisterationCode.as_view())

]