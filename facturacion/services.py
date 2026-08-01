"""
Capa de facturación electrónica.

Honduras factura hoy bajo el esquema de CAI (Código de Autorización de
Impresión, RangoAutorizado en este proyecto). El SAR viene migrando a un
esquema de Documento Tributario Electrónico (DTE) que exige integrarse con
un proveedor certificado (o el propio portal del SAR) para timbrar/validar
cada documento y obtener un código de verificación.

Como esa integración requiere credenciales y un proveedor certificado que
el negocio aún no ha contratado, se deja esta interfaz desacoplada:
`emitir_documento` guarda siempre el DocumentoFiscal usando el correlativo
CAI (que ya es válido fiscalmente), y adicionalmente invoca al proveedor de
facturación electrónica configurado para obtener `codigo_verificacion`.
Mientras no haya proveedor real, se usa `FacturacionMock`.
"""

import uuid
from abc import ABC, abstractmethod


class ProveedorFacturacionElectronica(ABC):
    """Interfaz que debe implementar cualquier proveedor real (PAC/SAR)."""

    @abstractmethod
    def emitir(self, documento_fiscal) -> str:
        """Envía el documento al proveedor y devuelve el código de verificación."""
        raise NotImplementedError

    @abstractmethod
    def anular(self, documento_fiscal) -> None:
        """Notifica al proveedor la anulación del documento."""
        raise NotImplementedError


class FacturacionMock(ProveedorFacturacionElectronica):
    """Implementación de referencia. Sustituir por el proveedor certificado real."""

    def emitir(self, documento_fiscal) -> str:
        return uuid.uuid4().hex.upper()

    def anular(self, documento_fiscal) -> None:
        return None


def get_proveedor_facturacion_electronica() -> ProveedorFacturacionElectronica:
    return FacturacionMock()


def emitir_documento_fiscal(venta, rango, rtn_receptor="", nombre_receptor=""):
    """Crea y timbra el DocumentoFiscal para una Venta usando el rango CAI dado."""
    from .models import DocumentoFiscal

    numero_documento = rango.siguiente_numero()
    rango.save()

    documento = DocumentoFiscal.objects.create(
        venta=venta,
        rango=rango,
        numero_documento=numero_documento,
        tipo_documento=rango.tipo_documento,
        rtn_receptor=rtn_receptor,
        nombre_receptor=nombre_receptor,
        subtotal=venta.subtotal,
        total_isv=venta.total_isv,
        total=venta.total,
    )

    proveedor = get_proveedor_facturacion_electronica()
    documento.codigo_verificacion = proveedor.emitir(documento)
    documento.save(update_fields=["codigo_verificacion"])
    return documento
