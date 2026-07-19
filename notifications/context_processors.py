def unread_notifications(request):
    """Expose unread count + recent inbox items for topbar dropdown / sidebar bubble."""
    if not request.user.is_authenticated:
        return {'unread_count': 0, 'recent_notifications': []}

    qs = request.user.notifications.all()
    count = qs.filter(is_read=False).count()
    # Prefer unread first, then newest overall (up to 8)
    recent = list(qs.filter(is_read=False)[:8])
    if len(recent) < 8:
        seen = {n.pk for n in recent}
        for n in qs[:8]:
            if n.pk not in seen:
                recent.append(n)
                seen.add(n.pk)
            if len(recent) >= 8:
                break
    return {'unread_count': count, 'recent_notifications': recent}
