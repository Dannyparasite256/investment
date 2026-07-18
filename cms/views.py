from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from cms.models import Announcement, CMSPage, FAQ


def page_detail(request, slug):
    page = get_object_or_404(CMSPage, slug=slug, is_published=True)
    return render(request, 'cms/page.html', {'page': page})


def faq_list(request):
    faqs = FAQ.objects.filter(is_published=True)
    categories = {}
    for f in faqs:
        categories.setdefault(f.category or 'General', []).append(f)
    return render(request, 'cms/faq.html', {'categories': categories})


def terms(request):
    page = CMSPage.objects.filter(page_type=CMSPage.PageType.TERMS, is_published=True).first()
    return render(request, 'cms/page.html', {'page': page, 'fallback_title': 'Terms of Service'})


def privacy(request):
    page = CMSPage.objects.filter(page_type=CMSPage.PageType.PRIVACY, is_published=True).first()
    return render(request, 'cms/page.html', {'page': page, 'fallback_title': 'Privacy Policy'})
