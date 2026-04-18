from django.urls import path
from .views import (
    CreateCourseApiView,
    CourseEnrollmentApiView,
    GetAllCoursesApiView,
    GetSingleCourseDetailApiView,
    SendInstructorInvite,
    AcceptInstructorInvite,
    RejectInstructorInvite,
    PaymentRequestApiView,
    PaymentConfirmApiView
)

urlpatterns = [
    path('create/', CreateCourseApiView.as_view(), name='create-course'),
    path('enroll/', CourseEnrollmentApiView.as_view(), name='enroll-course'),
    path('all/', GetAllCoursesApiView.as_view(), name='all-courses'),
    path('<slug:slug>/', GetSingleCourseDetailApiView.as_view(), name='course-detail'),

    path('invite/send/', SendInstructorInvite.as_view(), name='send-invite'),
    path('invite/accept/', AcceptInstructorInvite.as_view(), name='accept-invite'),
    path('invite/reject/', RejectInstructorInvite.as_view(), name='reject-invite'),

    path('payment/request/', PaymentRequestApiView.as_view(), name='payment-request'),
    path('payment/confirm/', PaymentConfirmApiView.as_view(), name='payment-confirm'),
]