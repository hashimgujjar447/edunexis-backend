from rest_framework import serializers
from courses.models.course import Course
from courses.models.payment import Payment
from courses.models.section import Section
from courses.models.lesson import Lesson
from courses.models.attachment import Attachment

from rest_framework import serializers
from courses.models.course import Course
from accounts.models import Account

class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "email"]


class CourseSerializer(serializers.ModelSerializer):
    instructors = InstructorSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "thumbnail",
            "instructors",
            "created_at"
        ]



class CourseCreateSerializer(serializers.ModelSerializer):


    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "price",
            "discount_price",
            "is_paid",
            "thumbnail",
           
        ]

    def validate(self, data):
        is_paid = data.get("is_paid")
        price = data.get("price", 0)
        discount_price = data.get("discount_price")

        # Paid validation
        if is_paid:
            if price <= 0:
                raise serializers.ValidationError("Paid course must have price > 0")

            if discount_price:
                if discount_price >= price:
                    raise serializers.ValidationError(
                        "Discount must be less than price"
                    )

        # Free validation
        else:
            if price != 0:
                raise serializers.ValidationError(
                    "Free course must have price 0"
                )

            if discount_price:
                raise serializers.ValidationError(
                    "Free course cannot have discount"
                )

        return data
    


class CourseSectionCreateSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Section
        fields = ["title", "order", "course_id"]

    def validate(self, data):
        if data["order"] < 1:
            raise serializers.ValidationError("Order must be >= 1")
        return data


class SectionLessonCreateSerializer(serializers.ModelSerializer):
    section_id = serializers.IntegerField(write_only=True)
    course_id = serializers.IntegerField(write_only=True)
    video = serializers.FileField()

    class Meta:
        model = Lesson
        fields = ["title", "order", "section_id", "course_id", "video"]

    def validate(self, data):
        if data["order"] < 1:
            raise serializers.ValidationError("Order must be >=1")
        return data
    

class LessonAttachmentsCreateSerializer(serializers.ModelSerializer):
    lesson_id = serializers.IntegerField(write_only=True)
    section_id = serializers.IntegerField(write_only=True)
    course_id = serializers.IntegerField(write_only=True)
    file = serializers.FileField()
    extra_url = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = Attachment
        fields = [
            "title",
            "file",
            "extra_url",
            "file_type",
            "lesson_id",
            "section_id",
            "course_id",
        ]