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

## Despliegue en Render (Blueprint)

El repositorio incluye `render.yaml`, un [Blueprint de Render](https://render.com/docs/blueprint-spec)
que crea automáticamente un servicio web Python (`sistema-ferretero`) que
corre `gunicorn config.wsgi:application`.

> **Base de datos:** Render solo permite **una** base de datos PostgreSQL en
> plan free por cuenta. Si ya usas ese cupo en otro proyecto, el blueprint no
> puede crear una segunda gratis (`cannot have more than one active free
> tier database`). Por eso este blueprint **no** define su propia base de
> datos — usa una instancia externa gratuita en [Neon](https://neon.tech) y
> la conectas manualmente con `DATABASE_URL`.

### 1. Crear la base de datos en Neon (gratis)

1. Crea una cuenta en [neon.tech](https://neon.tech) y un proyecto nuevo
   (elige la región más cercana a tus usuarios).
2. En el dashboard del proyecto, copia el **Connection string** (modo
   "Pooled connection" recomendado para apps web). Tiene esta forma:
   `postgresql://usuario:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`

### 2. Desplegar el Blueprint en Render

1. En el dashboard de Render: **New +** → **Blueprint**, elige este
   repositorio y la rama a desplegar. Render detecta `render.yaml`
   automáticamente y solo propondrá crear el servicio web (sin base de datos).
2. Aplica el Blueprint. Al terminar, entra al servicio `sistema-ferretero` →
   **Environment** y pega la connection string de Neon en la variable
   `DATABASE_URL` (quedó marcada como manual en el blueprint, por eso no se
   pidió antes). Guarda: esto dispara un redeploy.
3. (Opcional) En las mismas variables de entorno, define
   `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y
   `DJANGO_SUPERUSER_PASSWORD` para que `build.sh` cree el superusuario
   inicial en el primer deploy.
4. El build corre `build.sh` (instala dependencias, `collectstatic` y
   `migrate` contra tu base de Neon) y luego levanta el servicio.
5. Carga los datos base (sucursales, CAI, productos) desde `/admin/` en
   `https://<tu-servicio>.onrender.com/admin/`.

Si más adelante prefieres una base de datos administrada por el propio
Render (por ejemplo si liberas el cupo free o subes a un plan pago), puedes
volver a agregar un bloque `databases:` en `render.yaml` con
`fromDatabase.property: connectionString` en vez de la `DATABASE_URL` manual.

### Notas importantes para producción

- **Archivos subidos (imágenes de producto):** el disco del servicio web es
  efímero en el plan free/starter sin disco persistente — las imágenes
  subidas vía `Producto.imagen` se pierden en cada deploy. Para producción,
  agrega un [disco persistente de Render](https://render.com/docs/disks) o
  cambia `MEDIA` a un backend como S3 (`django-storages`).
- **Facturación electrónica:** sigue usando `FacturacionMock` (ver sección
  anterior) hasta integrar un proveedor certificado del SAR.
- `SECRET_KEY` se genera automáticamente por Render (`generateValue: true`);
  no la definas tú mismo en el blueprint.

## Pendiente / próximos pasos sugeridos

- Interfaz POS dedicada (hoy la carga de ventas se hace vía Django Admin).
- Integración real con un proveedor de facturación electrónica certificado
  por el SAR cuando el negocio lo contrate.
- Reportes más completos (ventas por vendedor/sucursal, rotación de
  inventario, cuentas por cobrar de clientes a crédito).
- Permisos granulares por rol (actualmente `rol` es informativo; falta
  restringir vistas/acciones del admin según rol).
