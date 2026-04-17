from rest_framework import serializers
from courses.models.course import Course



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

class CourseCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    thumbnail = serializers.ImageField(required=False, allow_null=True)
    instructors = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError("Title is required field")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    