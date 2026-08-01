from django.contrib import admin

from .models import CierreCaja, DetalleVenta, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "sucursal", "cliente", "vendedor", "forma_pago", "estado", "total", "fecha",
    )
    list_filter = ("estado", "sucursal", "forma_pago")
    search_fields = ("id", "cliente__nombre", "cliente__rtn")
    inlines = [DetalleVentaInline]
    readonly_fields = ("subtotal", "total_isv", "total", "fecha_anulacion")
    actions = ["confirmar_ventas", "anular_ventas"]

    @admin.action(description="Confirmar venta(s): descuenta stock y emite factura")
    def confirmar_ventas(self, request, queryset):
        confirmadas = 0
        for venta in queryset:
            try:
                venta.confirmar(usuario=request.user)
                confirmadas += 1
            except Exception as exc:
                self.message_user(request, f"Error en venta #{venta.pk}: {exc}", level="error")
        if confirmadas:
            self.message_user(request, f"{confirmadas} venta(s) confirmada(s).")

    @admin.action(description="Anular venta(s) completada(s)")
    def anular_ventas(self, request, queryset):
        anuladas = 0
        for venta in queryset:
            try:
                venta.anular()
                anuladas += 1
            except Exception as exc:
                self.message_user(request, f"Error en venta #{venta.pk}: {exc}", level="error")
        if anuladas:
            self.message_user(request, f"{anuladas} venta(s) anulada(s).")


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ("sucursal", "usuario", "estado", "monto_inicial", "monto_final", "fecha_apertura", "fecha_cierre")
    list_filter = ("sucursal", "estado")
