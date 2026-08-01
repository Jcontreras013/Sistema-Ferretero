from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "ciudad", "es_matriz", "activa")
    list_filter = ("activa", "es_matriz", "ciudad")
    search_fields = ("codigo", "nombre", "ciudad")
