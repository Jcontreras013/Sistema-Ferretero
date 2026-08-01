from django.contrib import admin

from .models import (
    Categoria,
    MovimientoInventario,
    Producto,
    Stock,
    TransferenciaInventario,
    UnidadMedida,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "abreviatura")


class StockInline(admin.TabularInline):
    model = Stock
    extra = 0


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo", "nombre", "categoria", "precio_compra", "precio_venta",
        "porcentaje_isv", "stock_total", "activo",
    )
    list_filter = ("categoria", "activo", "unidad_medida")
    search_fields = ("codigo", "codigo_barras", "nombre")
    inlines = [StockInline]


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("producto", "sucursal", "cantidad", "hay_stock_bajo", "actualizado")
    list_filter = ("sucursal",)
    search_fields = ("producto__codigo", "producto__nombre")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "producto", "sucursal", "tipo", "cantidad", "usuario", "referencia")
    list_filter = ("tipo", "sucursal")
    search_fields = ("producto__codigo", "producto__nombre", "referencia")
    date_hierarchy = "fecha"


@admin.register(TransferenciaInventario)
class TransferenciaInventarioAdmin(admin.ModelAdmin):
    list_display = (
        "producto", "sucursal_origen", "sucursal_destino", "cantidad", "estado", "fecha_solicitud",
    )
    list_filter = ("estado", "sucursal_origen", "sucursal_destino")
    actions = ["marcar_completada"]

    @admin.action(description="Completar transferencia seleccionada (mueve stock)")
    def marcar_completada(self, request, queryset):
        completadas = 0
        for transferencia in queryset:
            try:
                transferencia.completar(usuario=request.user)
                completadas += 1
            except Exception as exc:
                self.message_user(request, f"Error en transferencia #{transferencia.pk}: {exc}", level="error")
        if completadas:
            self.message_user(request, f"{completadas} transferencia(s) completada(s).")
