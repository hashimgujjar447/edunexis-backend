from django.contrib import admin
from courses.models.course import Course
from courses.models.enrollment import Enrollment
from courses.models.review import Review
from courses.models.section import Section
from courses.models.lesson import Lesson
from courses.models.attachment import Attachment
from courses.models.invite import CourseInstructorInvite
from courses.models.payment import Payment
from courses.models.course import Category

# Register your models here.


admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Review)
admin.site.register(Section)
admin.site.register(Lesson)
admin.site.register(Attachment)
admin.site.register(CourseInstructorInvite)
admin.site.register(Payment)
admin.site.register(Category)