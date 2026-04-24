from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions
from courses.serializers import CategorySerializer,LessonDetailSerializer,CourseCreateSerializer,CourseSectionDetailSerializer,LessonAttachmentsCreateSerializer, CourseSerializer,CourseSectionCreateSerializer,SectionLessonCreateSerializer
from courses.models.course import Course
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.models import Account
from courses.models.invite import CourseInstructorInvite
from django.db import transaction
from courses.models.enrollment import Enrollment
from rest_framework import status
from courses.models.payment import Payment
import stripe
from decouple import config
from courses.models.section import Section
from courses.models.lesson import Lesson
from courses.models.attachment import Attachment
from courses.models.course import Category



stripe.api_key = config("STRIPE_SECRET_KEY")


class CreateCategoryApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")

        if not name:
            return Response(
                {"error": "Category name is required"},
                status=400
            )

        if Category.objects.filter(name__iexact=name).exists():
            return Response(
                {"error": "Category already exists"},
                status=400
            )

        category = Category.objects.create(name=name)

        return Response({
            "message": "Category created successfully",
            "data": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug
            }
        }, status=201)

class GetAllCategoriesApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)

        return Response({
            "message": "Categories fetched successfully",
            "data": serializer.data
        })    


class CreateCourseApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            category_ids = request.data.get("category_ids", [])
            categories = Category.objects.filter(id__in=category_ids)

            course = Course.objects.create(
                title=data["title"],
                description=data["description"],
                price=data["price"],
                thumbnail=data.get("thumbnail"),
                is_paid=data.get("is_paid", False),
                discount_price=data.get("discount_price"),
            )

            course.categories.set(categories)

            

            course.instructors.add(request.user)

            return Response({"message": "Course created successfully"}, status=201)

        return Response(serializer.errors, status=400)


class CourseEnrollmentApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get("course_id")

        if not course_id:
            return Response(
                {"error": "Course id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, id=course_id)

        if request.user in course.instructors.all():
            return Response(
                {"error": "Instructor cannot enroll"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response(
                {"message": "You are already enrolled"},
                status=status.HTTP_200_OK
            )

        if course.is_paid:
            return Response(
                {
                    "payment_required": True,
                    "message": "Please complete payment first"
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        Enrollment.objects.create(
            user=request.user,
            course=course
        )

        return Response(
            {
                "message": "User enrolled successfully",
                "course_id": course.id,
                "course_title": course.title
            },
            status=status.HTTP_201_CREATED
        )


class GetAllCoursesApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all().prefetch_related("instructors")
        serializer = CourseSerializer(courses, many=True, context={"request": request})

        return Response({
            "message": "All courses fetched",
            "data": serializer.data
        })
    
 


class GetSingleCourseDetailApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug):
        course = get_object_or_404(
            Course.objects.prefetch_related("instructors"),
            slug=slug
        )

        serializer = CourseSerializer(course,context={"request":request})

        return Response({
            "message": "Course fetched successfully",
            "data": serializer.data
        })

class GetCourseSectionsApiView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request,slug):
        course_sections = Section.objects.prefetch_related("lessons").filter(course__slug=slug).order_by("order")
        serializer=CourseSectionDetailSerializer(course_sections,many=True)
        return Response({
            "message":"All course sections are fetched",
            "data":serializer.data
        })
    




class LessonDetailApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_slug, section_slug, lesson_slug):
        lesson = get_object_or_404(
            Lesson.objects.select_related("section__course")
            .prefetch_related("attachments"),
            slug=lesson_slug,
            section__slug=section_slug,
            section__course__slug=course_slug
        )

        if not Enrollment.objects.filter(
                    user=request.user,
                    course=lesson.section.course
                ).exists():
            return Response(
                {"message": "You are not enrolled in this course"},
                status=403
            )
       

        serializer = LessonDetailSerializer(
            lesson,
            context={"request": request}
        )

        return Response({
            "message": "Lesson detail fetched successfully",
            "data": serializer.data
        })

class SendInstructorInvite(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get("course_id")
        user_id = request.data.get("user_id")

        course = get_object_or_404(Course, id=course_id)
        user = get_object_or_404(Account, id=user_id)

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


class PaymentRequestApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get("course_id")
        user = request.user

        course = get_object_or_404(Course, id=course_id)

        if not course.is_paid:
            Enrollment.objects.get_or_create(user=user, course=course)
            return Response({
                "message": "Free course enrolled successfully"
            }, status=status.HTTP_200_OK)

        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({
                "message": "Already enrolled"
            }, status=status.HTTP_200_OK)

        if Payment.objects.filter(user=user, course=course, status="success").exists():
            Enrollment.objects.get_or_create(user=user, course=course)
            return Response({
                "message": "Payment already done, enrolled successfully"
            }, status=status.HTTP_200_OK)

        pending_payment = Payment.objects.filter(
            user=user,
            course=course,
            status="pending"
        ).first()

        if pending_payment:
            return Response({
                "payment_id": pending_payment.id,
                "amount": pending_payment.amount,
                "message": "Pending payment already exists"
            }, status=status.HTTP_200_OK)

        amount = course.discount_price if course.discount_price else course.price

        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=amount,
            status="pending"
        )

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": course.title
                            },
                            "unit_amount": int(amount * 100)
                        },
                        "quantity": 1
                    }
                ],
                success_url=f"http://localhost:3000/success?payment_id={payment.id}",
                cancel_url="http://localhost:3000/cancel",
                metadata={
                    "payment_id": payment.id,
                    "user_id": user.id,
                    "course_id": course.id
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        payment.stripe_session_id = checkout_session.id
        payment.save()

        return Response({
            "payment_id": payment.id,
            "checkout_url": checkout_session.url
        }, status=201)


class PaymentConfirmApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get("payment_id")
        user = request.user

        payment = get_object_or_404(
            Payment,
            id=payment_id,
            user=user
        )

        course = payment.course

        if payment.status == "success":
            Enrollment.objects.get_or_create(user=user, course=course)
            return Response({
                "message": "Payment already confirmed"
            }, status=status.HTTP_200_OK)

        if not payment.stripe_session_id:
            return Response({"error": "No Stripe session found"}, status=400)

        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        if session.payment_status != "paid":
            return Response({
                "error": "Payment not completed"
            }, status=400)

        if Payment.objects.filter(transaction_id=session.payment_intent).exists():
            return Response({
                "error": "Duplicate transaction"
            }, status=400)

        with transaction.atomic():
            payment.status = "success"
            payment.transaction_id = session.payment_intent
            payment.save()

            Enrollment.objects.get_or_create(
                user=user,
                course=course
            )

        return Response({
            "message": "Payment successful, enrolled"
        }, status=status.HTTP_200_OK)
    


class CreateCourseSectionApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CourseSectionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        course = get_object_or_404(Course, id=data["course_id"])

        if request.user not in course.instructors.all():
            return Response(
                {"message": "Not allowed"},
                status=403
            )

        if Section.objects.filter(course=course, title=data["title"]).exists():
            return Response(
                {"message": "Title must be unique per course"},
                status=400
            )

        if Section.objects.filter(course=course, order=data["order"]).exists():
            return Response(
                {"message": "Order must be unique per course"},
                status=400
            )

        section = Section.objects.create(
            course=course,
            title=data["title"],
            order=data["order"]
        )

        return Response({
            "message": "Section created successfully",
            "section_id": section.id
        }, status=201)

class SectionLessonCreateApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SectionLessonCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        course = get_object_or_404(Course, id=data["course_id"])
        section = get_object_or_404(Section, id=data["section_id"])

        if section.course != course:
            return Response({"message": "Invalid section for this course"}, status=400)

        if request.user not in course.instructors.all():
            return Response({"message": "Not allowed"}, status=403)

        if Lesson.objects.filter(section=section, title=data["title"]).exists():
            return Response({"message": "Title must be unique"}, status=400)

        if Lesson.objects.filter(section=section, order=data["order"]).exists():
            return Response({"message": "Order must be unique"}, status=400)

        lesson = Lesson.objects.create(
            course=course,
            section=section,
            title=data["title"],
            order=data["order"],
            video=data["video"],
        )

        return Response({
            "message": "Lesson created successfully",
            "lesson_id": lesson.id
        }, status=201)
    

class LessonAttachmentApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LessonAttachmentsCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        course = get_object_or_404(Course, id=data["course_id"])
        section = get_object_or_404(Section, id=data["section_id"], course=course)
        lesson = get_object_or_404(
            Lesson,
            id=data["lesson_id"],
            course=course,
            section=section
        )

        if request.user not in course.instructors.all():
            return Response({"message": "Not allowed"}, status=403)

        if Attachment.objects.filter(lesson=lesson, title=data["title"]).exists():
            return Response({
                "message": "Title must be unique per lesson"
            }, status=400)

        attachment = Attachment.objects.create(
            file=data["file"],
            title=data["title"],
            lesson=lesson,
            file_type=data["file_type"],
            extra_url=data.get("extra_url")
        )

        return Response({
            "message": "Lesson attachment created successfully",
            "attachment_id": attachment.id
        }, status=201)