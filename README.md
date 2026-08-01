# Sistema Ferretero

Sistema de gestión para ferreterías con soporte multi-sucursal, control de
inventario, punto de venta (POS), compras/proveedores, roles de usuario y
facturación fiscal para Honduras (SAR).

## Stack

- Python 3.11 + Django 5
- SQLite en desarrollo, PostgreSQL recomendado en producción
- Backend renderizado con templates de Django + Bootstrap 5 (vía CDN)

## Apps

| App          | Responsabilidad                                                        |
|--------------|-------------------------------------------------------------------------|
| `usuarios`   | Usuario custom con roles (Admin, Gerente, Vendedor, Bodeguero, Contador) |
| `sucursales` | Catálogo de sucursales (multi-sucursal)                                 |
| `inventario` | Categorías, productos, stock por sucursal, movimientos y transferencias |
| `clientes`   | Clientes (natural/jurídico, RTN, límite de crédito)                     |
| `compras`    | Proveedores y órdenes de compra (recepción incrementa stock)            |
| `ventas`     | Punto de venta: venta, detalle, cierres de caja (confirmar descuenta stock) |
| `facturacion`| Configuración fiscal, CAI/rangos autorizados y documentos fiscales       |
| `reportes`   | Dashboard con métricas básicas                                          |

## Facturación fiscal (Honduras)

El módulo `facturacion` modela el esquema vigente del SAR basado en **CAI**
(Código de Autorización de Impresión): cada sucursal/punto de emisión tiene
un `RangoAutorizado` con un rango de correlativos y una fecha límite de
emisión. Al confirmar una venta (`Venta.confirmar()`), se reserva el
siguiente correlativo con formato `EEE-PPP-TT-CCCCCCCC` y se crea un
`DocumentoFiscal`.

`facturacion/services.py` define la interfaz `ProveedorFacturacionElectronica`
para integrarse a futuro con el esquema de Documento Tributario Electrónico
(DTE) del SAR o un proveedor certificado (PAC). Mientras no se contrate un
proveedor real, se usa `FacturacionMock`, que genera un código de
verificación de marcador de posición. **Antes de operar en producción**,
reemplazar `get_proveedor_facturacion_electronica()` por la integración real
y cargar los CAI vigentes emitidos por el SAR en `RangoAutorizado`.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # ajustar SECRET_KEY, DB, etc.

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Accede a `http://localhost:8000/admin/` para administrar todos los módulos,
o `http://localhost:8000/` para el dashboard (requiere iniciar sesión en
`/login/`).

## Flujo típico

1. Crear `Sucursal`, `Categoria`, `UnidadMedida` y `Producto` desde el admin.
2. Cargar `Stock` inicial por producto/sucursal (o vía `OrdenCompra` →
   acción **"Recibir orden de compra"**, que incrementa el stock
   automáticamente).
3. Configurar `Empresa` (datos fiscales) y al menos un `RangoAutorizado`
   (CAI) por sucursal.
4. Registrar una `Venta` con sus `DetalleVenta` y usar la acción
   **"Confirmar venta(s)"**: valida stock, lo descuenta, calcula ISV/total y
   emite el `DocumentoFiscal` con el siguiente correlativo del CAI.
5. Revisar el dashboard (`/`) para ventas del día/mes y alertas de stock
   bajo.

## Pendiente / próximos pasos sugeridos

- Interfaz POS dedicada (hoy la carga de ventas se hace vía Django Admin).
- Integración real con un proveedor de facturación electrónica certificado
  por el SAR cuando el negocio lo contrate.
- Reportes más completos (ventas por vendedor/sucursal, rotación de
  inventario, cuentas por cobrar de clientes a crédito).
- Permisos granulares por rol (actualmente `rol` es informativo; falta
  restringir vistas/acciones del admin según rol).
