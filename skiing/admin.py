from django.contrib import admin

from .models import SkiLiftLimit, User


class UserAdmin(admin.ModelAdmin):
    fields = ["username", "partnered_ski_resorts", "status", "ski_lift_uses_in_row"]


admin.site.register(User, UserAdmin)
admin.site.register(SkiLiftLimit)

# Register your models here.
