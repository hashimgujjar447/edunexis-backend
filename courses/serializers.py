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
            "instructors"
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
    