from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Customer, CustomerGroup

admin.site.unregister(User)


class CustomUserInline(admin.StackedInline):
    model = Customer
    can_delete = False
    fields = ['city', 'phone', 'loyal_group', 'balance', 'qty_buy']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (CustomUserInline,)


admin.site.register(CustomerGroup)
