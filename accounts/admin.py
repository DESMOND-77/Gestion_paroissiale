from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserActivity


class UserAdmin(BaseUserAdmin):
    # model = User
    list_display = ("nom", "email", "role", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "role")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Infos personnelles",
            {
                "fields": (
                    "prenom",
                    "nom",
                    "email",
                    "profile_picture",
                    "phone_number",
                    "role",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_verified",
                    "is_staff",
                    "is_superuser",
                    "user_permissions",
                )
            },
        ),
        (
            "Dates importantes",
            {
                "fields": ("last_login", "created_at", "updated_at"),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "nom",
                    "prenom",
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    search_fields = ("email", "nom", "prenom")
    ordering = ("nom",)
    readonly_fields = ["updated_at", "created_at"]


class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "ip_address", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("user__email", "user__nom", "details")
    readonly_fields = (
        "user",
        "action",
        "details",
        "ip_address",
        "user_agent",
        "timestamp",
    )


admin.site.register(User, UserAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
