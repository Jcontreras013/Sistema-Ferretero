from django.contrib import admin

from .models import DetalleOrdenCompra, OrdenCompra, Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rtn", "contacto", "telefono", "activo")
    search_fields = ("nombre", "rtn")
    list_filter = ("activo",)


class DetalleOrdenCompraInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 1


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ("id", "proveedor", "sucursal", "estado", "fecha", "total")
    list_filter = ("estado", "sucursal", "proveedor")
    inlines = [DetalleOrdenCompraInline]
    actions = ["marcar_recibida"]

    @admin.action(description="Recibir orden de compra seleccionada (incrementa stock)")
    def marcar_recibida(self, request, queryset):
        recibidas = 0
        for orden in queryset:
            try:
                orden.recibir(usuario=request.user)
                recibidas += 1
            except Exception as exc:
                self.message_user(request, f"Error en orden #{orden.pk}: {exc}", level="error")
        if recibidas:
            self.message_user(request, f"{recibidas} orden(es) recibida(s) y stock actualizado.")
