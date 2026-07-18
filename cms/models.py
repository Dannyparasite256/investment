"""CMS pages, FAQ, announcements."""
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel, UUIDModel


class CMSPage(UUIDModel, TimeStampedModel):
    class PageType(models.TextChoices):
        TERMS = 'terms', 'Terms of Service'
        PRIVACY = 'privacy', 'Privacy Policy'
        ABOUT = 'about', 'About'
        FAQ_PAGE = 'faq', 'FAQ Page'
        CUSTOM = 'custom', 'Custom'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    page_type = models.CharField(max_length=20, choices=PageType.choices, default=PageType.CUSTOM)
    content = models.TextField(help_text='HTML or Markdown content')
    is_published = models.BooleanField(default=True)
    meta_description = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)


class FAQ(UUIDModel, TimeStampedModel):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True, default='General')
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class Announcement(UUIDModel, TimeStampedModel):
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    level = models.CharField(
        max_length=20,
        choices=[('info', 'Info'), ('warning', 'Warning'), ('success', 'Success'), ('danger', 'Danger')],
        default='info',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
