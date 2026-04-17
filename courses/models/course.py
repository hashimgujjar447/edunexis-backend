from django.db import models
from accounts.models import Account
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    instructors = models.ManyToManyField(Account, related_name="courses")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_free(self):
        return self.price == 0

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            old = Course.objects.get(pk=self.pk)

            if old.title != self.title:
                raise ValidationError("Title cannot be changed once set")
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Course.objects.filter(slug__iexact=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)