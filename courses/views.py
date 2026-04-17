from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions
from courses.serializers import CourseCreateSerializer,CourseSerializer
from courses.models.course import Course
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.models import Account
from courses.models.invite import CourseInstructorInvite
from django.db import transaction


class CreateCourseApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            course = Course.objects.create(
                title=data["title"],
                description=data["description"],
                price=data["price"],
                thumbnail=data.get("thumbnail")
            )

            # Always include the creator
            instructors = data.get("instructors", [])
            instructors.append(request.user.id)

            course.instructors.set(instructors)

            return Response({"message": "Course created successfully"}, status=201)

        return Response(serializer.errors, status=400)
    

class GetAllCoursesApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all().prefetch_related("instructors")

        serializer = CourseSerializer(courses, many=True)

        return Response({
            "message": "All courses fetched",
            "data": serializer.data
        })

class GetSingleCourseDetailApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        slug = request.query_params.get("slug")

        course = get_object_or_404(
            Course.objects.prefetch_related("instructors"),
            slug=slug
        )

        serializer = CourseSerializer(course)

        return Response({
            "message": "Course fetched successfully",
            "data": serializer.data
        })      

class SendInstructorInvite(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get("course_id")
        user_id = request.data.get("user_id")

        course = get_object_or_404(Course, id=course_id)
        user = get_object_or_404(Account, id=user_id)

      

        # Only instructor can invite
        if request.user not in course.instructors.all():
            return Response({"error": "Not allowed"}, status=403)
        
        if user == request.user:
            return Response({"error": "You cannot invite yourself"}, status=400)
        
        if user in course.instructors.all():
            return Response({"error": "User already instructor"}, status=400)

        invite, created = CourseInstructorInvite.objects.get_or_create(
            course=course,
            invited_user=user,
            defaults={
                "invited_by": request.user,
                "status": "pending"
            }
        )

        if not created:
            return Response({"message": "Invite already exists"}, status=400)

        return Response({"message": "Invite sent"}, status=201)



class AcceptInstructorInvite(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invite_id = request.data.get("invite_id")

        invite = get_object_or_404(
            CourseInstructorInvite,
            id=invite_id,
            invited_user=request.user
        )

        if invite.status != "pending":
            return Response({"message": "Invite already processed"}, status=400)

        with transaction.atomic():
            invite.status = "accepted"
            invite.save()

            invite.course.instructors.add(request.user)

        return Response({"message": "You are now instructor"}, status=200)
        

class RejectInstructorInvite(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invite_id = request.data.get("invite_id")

        invite = get_object_or_404(
            CourseInstructorInvite,
            id=invite_id,
            invited_user=request.user
        )

        if invite.status != "pending":
            return Response({"message": "Invite already processed"}, status=400)

        invite.status = "rejected"
        invite.save()

        return Response({"message": "Invite rejected successfully"}, status=200)