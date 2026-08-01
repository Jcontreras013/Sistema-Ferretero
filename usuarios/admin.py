from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos de ferretería", {"fields": ("rol", "sucursal", "telefono")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Datos de ferretería", {"fields": ("rol", "sucursal", "telefono")}),
    )
    list_display = ("username", "get_full_name", "rol", "sucursal", "is_active", "is_staff")
    list_filter = ("rol", "sucursal", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
