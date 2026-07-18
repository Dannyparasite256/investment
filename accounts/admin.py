from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import ActivityEvent, KYCDocument, PasswordResetToken, User
from accounts.security_models import AdminActivityLog, LoginHistory, UserSuspension


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('-date_joined',)
    list_display = ('email', 'first_name', 'last_name', 'email_verified', 'is_kyc_verified', 'preferred_currency', 'two_factor_enabled', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'email_verified', 'is_kyc_verified', 'two_factor_enabled')
    search_fields = ('email', 'first_name', 'last_name', 'referral_code')
    actions = ['verify_emails', 'unverify_emails']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone', 'country', 'date_of_birth', 'profile_picture', 'preferred_theme')}),
        ('Verification', {'fields': ('email_verified', 'is_kyc_verified', 'two_factor_enabled')}),
        ('Referral', {'fields': ('referral_code', 'referred_by', 'referral_earnings')}),
        ('Role & notes', {'fields': ('role', 'preferred_language', 'preferred_currency', 'last_login_ip', 'notes_internal')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('referral_code', 'date_joined', 'last_login')

    @admin.action(description='Mark email as verified')
    def verify_emails(self, request, queryset):
        updated = queryset.update(email_verified=True, email_verification_token='')
        self.message_user(request, f'{updated} user(s) email marked verified.')

    @admin.action(description='Mark email as unverified')
    def unverify_emails(self, request, queryset):
        updated = queryset.update(email_verified=False)
        self.message_user(request, f'{updated} user(s) email marked unverified.')


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'document_type')
    search_fields = ('user__email', 'document_number')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_kyc', 'reject_kyc']

    @admin.action(description='Approve selected KYC submissions')
    def approve_kyc(self, request, queryset):
        from core.models import AuditLog
        from core.utils import create_audit_log
        from notifications.models import Notification, notify

        for doc in queryset.exclude(status=KYCDocument.Status.APPROVED):
            doc.approve(request.user)
            notify(doc.user, 'KYC Approved', 'Your identity verification was approved.', level=Notification.Level.SUCCESS, category=Notification.Category.KYC)
            create_audit_log(request=request, user=request.user, action=AuditLog.Action.KYC_APPROVE, message=f'Approved KYC {doc.id}', object_id=str(doc.id))
        self.message_user(request, 'Selected KYC documents approved.')

    @admin.action(description='Reject selected KYC submissions')
    def reject_kyc(self, request, queryset):
        from core.models import AuditLog
        from core.utils import create_audit_log
        from notifications.models import Notification, notify

        for doc in queryset.exclude(status=KYCDocument.Status.REJECTED):
            doc.reject(request.user, reason='Rejected by admin')
            notify(doc.user, 'KYC Rejected', 'Your KYC was rejected. Please resubmit.', level=Notification.Level.WARNING, category=Notification.Category.KYC)
            create_audit_log(request=request, user=request.user, action=AuditLog.Action.KYC_REJECT, message=f'Rejected KYC {doc.id}', object_id=str(doc.id))
        self.message_user(request, 'Selected KYC documents rejected.')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'used', 'created_at')
    list_filter = ('used',)
    search_fields = ('user__email', 'token')


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'email_attempted', 'ip_address', 'result', 'is_suspicious')
    list_filter = ('result', 'is_suspicious')
    search_fields = ('user__email', 'email_attempted', 'ip_address')
    readonly_fields = [f.name for f in LoginHistory._meta.fields]


@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'admin', 'action', 'target_type', 'target_id', 'ip_address')
    search_fields = ('admin__email', 'action', 'message')


@admin.register(UserSuspension)
class UserSuspensionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'suspended_by', 'created_at', 'lifted_at')
    list_filter = ('is_active',)


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'event_type', 'title')
    list_filter = ('event_type',)
    search_fields = ('user__email', 'title')
