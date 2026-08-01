from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "rtn", "telefono", "limite_credito", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("nombre", "rtn", "email")
