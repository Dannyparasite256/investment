from django.contrib import admin

from cms.models import Announcement, CMSPage, FAQ


@admin.register(CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'page_type', 'is_published', 'sort_order')
    list_filter = ('page_type', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_published', 'sort_order')
    list_filter = ('category', 'is_published')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'is_active', 'created_at')
    list_filter = ('is_active', 'level')
