from rest_framework import serializers
from courses.models.course import Course
from courses.models.payment import Payment
from courses.models.section import Section
from courses.models.lesson import Lesson
from courses.models.attachment import Attachment

from rest_framework import serializers
from courses.models.course import Course
from accounts.models import Account
from courses.models.review import Review
from courses.models.enrollment import Enrollment


from courses.models.course import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "email"]


from rest_framework import serializers

class CourseSerializer(serializers.ModelSerializer):
    instructors = InstructorSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    
    reviews_count = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "is_paid",
            
            "price",
            "discount_price",
            "thumbnail_url",
            "instructors",
            "created_at",
            "categories",
            "reviews_count",
            "is_enrolled",
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")

        if not obj.thumbnail:
            return None

        if request:
            return request.build_absolute_uri(obj.thumbnail.url)

        return obj.thumbnail.url
        

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
    
class LessonSerializerForSection(serializers.ModelSerializer):
    class Meta:
        model=Lesson
        fields=(
            'title','slug','order'
        )    

class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            'id',
            'title',
            'file',
            'file_type',
            'created_at',
            'file_url'
        )

    def get_file_url(self, obj):
        request = self.context.get("request")

        # ✅ Case 1: File exists
        if obj.file:
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url

        # ✅ Case 2: Use external URL
        if obj.extra_url:
            return obj.extra_url

        # ✅ Case 3: Nothing exists
        return None

class LessonDetailSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True)

    class Meta:
        model = Lesson
        fields = (
            'id',
            'title',
            'slug',
            'order',
            'video',        # ya video_url
            'content',      # description / text
            'attachments'
        )


class CourseSectionDetailSerializer(serializers.ModelSerializer):
   
    lessons=LessonSerializerForSection(many=True)
    class Meta:
        model=Section
        fields=(
            'title','order','slug','lessons','id'
        )

 

class SectionLessonCreateSerializer(serializers.ModelSerializer):
    section_id = serializers.IntegerField(write_only=True)
    course_id = serializers.IntegerField(write_only=True)
    content = serializers.CharField(required=True)
    video = serializers.FileField(required=False, allow_null=True)  # ✅ optional

    class Meta:
        model = Lesson
        fields = [
            "title",
            "content",   # ✅ ADD THIS
           
            "section_id",
            "course_id",
            "video"
        ]

  

class LessonAttachmentsCreateSerializer(serializers.ModelSerializer):
    lesson_id = serializers.IntegerField(write_only=True)
    file = serializers.FileField()

    class Meta:
        model = Attachment
        fields = [
            "title",
            "file",
            "file_type",
            "lesson_id",
        ]
# class LessonAttachmentsCreateSerializer(serializers.ModelSerializer):
#     lesson_id = serializers.IntegerField(write_only=True)
#     section_id = serializers.IntegerField(source="section.id", read_only=True)
#     course_id = serializers.IntegerField(source="section.course.id", read_only=True)

#     file = serializers.FileField()
#     extra_url = serializers.URLField(required=False, allow_null=True)

#     class Meta:
#         model = Attachment
#         fields = [
#             "title",
#             "file",
#             "extra_url",
#             "file_type",
#             "lesson_id",
#             "section_id",
#             "course_id",
#         ]

