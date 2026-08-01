from django.contrib import admin

from .models import DocumentoFiscal, Empresa, RangoAutorizado


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rtn", "telefono", "email")


@admin.register(RangoAutorizado)
class RangoAutorizadoAdmin(admin.ModelAdmin):
    list_display = (
        "sucursal", "punto_emision", "tipo_documento", "cai",
        "numero_actual", "rango_final", "fecha_limite_emision", "activo",
    )
    list_filter = ("sucursal", "tipo_documento", "activo")


@admin.register(DocumentoFiscal)
class DocumentoFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "numero_documento", "venta", "nombre_receptor", "rtn_receptor",
        "total", "estado", "fecha_emision",
    )
    list_filter = ("estado", "tipo_documento")
    search_fields = ("numero_documento", "rtn_receptor", "nombre_receptor")
    readonly_fields = ("numero_documento", "codigo_verificacion", "fecha_emision")
    actions = ["anular_documentos"]

    @admin.action(description="Anular documento(s) fiscal(es) seleccionado(s)")
    def anular_documentos(self, request, queryset):
        anulados = 0
        for documento in queryset:
            try:
                documento.anular()
                anulados += 1
            except Exception as exc:
                self.message_user(request, f"Error en {documento.numero_documento}: {exc}", level="error")
        if anulados:
            self.message_user(request, f"{anulados} documento(s) anulado(s).")
