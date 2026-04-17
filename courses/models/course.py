from django.db import models
from accounts.models import Account
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()

    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_paid = models.BooleanField(default=False)

    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    instructors = models.ManyToManyField(Account, related_name="courses")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 🔹 Properties
    @property
    def is_free(self):
        return not self.is_paid

    @property
    def final_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    # 🔹 Validation
    def clean(self):
        if self.is_paid:
            if self.price <= 0:
                raise ValidationError("Paid course must have price greater than 0")

            if self.discount_price:
                if self.discount_price >= self.price:
                    raise ValidationError("Discount price must be less than original price")

        else:
            if self.price != 0:
                raise ValidationError("Free course must have price 0")

            if self.discount_price:
                raise ValidationError("Free course cannot have discount")

    def save(self, *args, **kwargs):
        self.clean()

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