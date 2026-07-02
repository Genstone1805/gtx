import json

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Notification,
    NotificationEvent,
    PushNotificationSubscriber,
    PushNotificationLog,
)

admin.site.register(Notification)
admin.site.register(NotificationEvent)


@admin.register(PushNotificationSubscriber)
class PushNotificationSubscriberAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "short_token", "device_id", "updated_at")
    list_filter = ("platform", "is_active", "created_at")
    search_fields = ("user__email", "token", "device_id")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Token")
    def short_token(self, obj):
        if len(obj.token) <= 32:
            return obj.token
        return f"{obj.token[:24]}…{obj.token[-6:]}"


def _pretty_json(value):
    """Render a JSON field as a readable, scrollable block in the admin."""
    if value in (None, "", [], {}):
        return "—"
    try:
        text = json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        text = str(value)
    return format_html(
        '<pre style="white-space:pre-wrap;max-height:400px;overflow:auto;'
        'background:#1e1e1e;color:#dcdcdc;padding:10px;border-radius:6px;">{}</pre>',
        text,
    )


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "status_badge",
        "trigger",
        "attempted",
        "sent",
        "failed",
        "deactivated",
        "title",
    )
    list_filter = ("status", "trigger", "created_at")
    search_fields = ("user__email", "title", "body")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "user",
        "trigger",
        "status",
        "title",
        "body",
        "attempted",
        "sent",
        "failed",
        "deactivated",
        "tokens_pretty",
        "request_payload_pretty",
        "response_pretty",
        "errors_pretty",
    )
    exclude = ("tokens", "request_payload", "response", "errors")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colors = {
            "success": "#1a7f37",
            "partial": "#9a6700",
            "failed": "#cf222e",
            "no_tokens": "#57606a",
            "skipped": "#57606a",
        }
        color = colors.get(obj.status, "#57606a")
        return format_html(
            '<b style="color:{}">{}</b>', color, obj.get_status_display()
        )

    @admin.display(description="Tokens targeted")
    def tokens_pretty(self, obj):
        return _pretty_json(obj.tokens)

    @admin.display(description="Request sent to Expo")
    def request_payload_pretty(self, obj):
        return _pretty_json(obj.request_payload)

    @admin.display(description="Response from Expo")
    def response_pretty(self, obj):
        return _pretty_json(obj.response)

    @admin.display(description="Errors")
    def errors_pretty(self, obj):
        return _pretty_json(obj.errors)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # View-only: logs are records, not editable.
        return False
