from django.db import models
from django.utils.text import slugify
from .section import Section

class Lesson(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    content = models.TextField()

 
    video = models.FileField(upload_to="lessons/videos/", null=True, blank=True)
    order = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["section", "title"],
                name="unique_lesson_title_per_section"
            ),
            models.UniqueConstraint(
                fields=["section", "slug"],
                name="unique_lesson_slug_per_section"
            ),
            models.UniqueConstraint(
                fields=["section", "order"],
                name="unique_lesson_order_per_section"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Lesson.objects.filter(
                section=self.section,
                slug__iexact=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title