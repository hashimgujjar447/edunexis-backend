from django.db import models
from django.utils.text import slugify
from .course import Course


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_section_order_per_course"
            ),
            models.UniqueConstraint(
                fields=["course", "slug"],
                name="unique_section_slug_per_course"
            ),
            models.UniqueConstraint(
                fields=["course", "title"],
                name="unique_section_title_per_course"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Section.objects.filter(
                        course=self.course,
                        slug__iexact=slug
                    ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title