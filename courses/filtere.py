from courses.models.course import Course
from django.db.models import Count
import django_filters


class CourseFilter(django_filters.FilterSet):
    is_paid = django_filters.BooleanFilter(method="filter_is_paid")
    category = django_filters.CharFilter(method="filter_category")
    newest = django_filters.BooleanFilter(method="filter_newest")
    popular = django_filters.BooleanFilter(method="filter_popular")

    class Meta:
        model = Course
        fields = ["category", "is_paid"]

    def filter_is_paid(self, queryset, name, value):
        return queryset.filter(is_paid=value)

    def filter_category(self, queryset, name, value):
        return queryset.filter(categories__slug=value)

    def filter_newest(self, queryset, name, value):
        if value:
            return queryset.order_by("-created_at")
        return queryset

    def filter_popular(self, queryset, name, value):
        if value:
            return (
                queryset
                .annotate(enrollment_count=Count("enrollments", distinct=True))
                .order_by("-enrollment_count")
            )
        return queryset