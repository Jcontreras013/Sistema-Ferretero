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

## Despliegue en Railway + Neon

El repositorio incluye `railway.json` para desplegar el servicio web en
[Railway](https://railway.app), usando una base de datos PostgreSQL externa
en [Neon](https://neon.tech) (gratuita) en vez de un plugin de base de datos
de Railway.

### 1. Base de datos en Neon

1. Crea una cuenta en [neon.tech](https://neon.tech) y un proyecto (p. ej.
   `hardware-store`).
2. En **Connection Details**, copia el connection string (usa el host con
   `-pooler` para conexiones desde una app web). Tiene esta forma:
   `postgresql://usuario:password@ep-xxxx-pooler.region.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
3. Guárdalo solo en el gestor de variables de entorno de Railway (paso
   siguiente) — nunca lo subas al repo ni lo compartas en texto plano.

### 2. Desplegar en Railway

1. En Railway: **New Project** → **Deploy from GitHub repo**, elige este
   repositorio y la rama `claude/sistema-ferreterias-c9pcst`. Railway detecta
   `railway.json` y usa Nixpacks para el build de Python.
2. En el servicio creado, ve a la pestaña **Variables** y define:
   - `DATABASE_URL`: el connection string de Neon del paso anterior.
   - `SECRET_KEY`: una clave larga y aleatoria (por ejemplo generada con
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`).
   - `DEBUG`: `False`
   - (Opcional) `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`,
     `DJANGO_SUPERUSER_PASSWORD` si quieres crear el superusuario a mano
     luego con `railway run python manage.py createsuperuser`.
3. En **Settings** → **Networking**, activa **Generate Domain** para obtener
   una URL pública (`*.up.railway.app`). Railway expone esa URL en la
   variable `RAILWAY_PUBLIC_DOMAIN`, que `settings.py` ya agrega
   automáticamente a `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`.
4. Railway ejecuta el build (`pip install` + `collectstatic`) y el deploy
   (`migrate` + `gunicorn`) definidos en `railway.json`.
5. Carga los datos base (sucursales, CAI, productos) desde `/admin/` en tu
   dominio de Railway.

### Notas importantes para producción

- **Archivos subidos (imágenes de producto):** el sistema de archivos del
  servicio es efímero — las imágenes subidas vía `Producto.imagen` se
  pierden en cada deploy. Para producción, monta un
  [volumen de Railway](https://docs.railway.app/reference/volumes) en
  `MEDIA_ROOT` o cambia `MEDIA` a un backend como S3 (`django-storages`).
- **Facturación electrónica:** sigue usando `FacturacionMock` (ver sección
  anterior) hasta integrar un proveedor certificado del SAR.
- El connection string de Neon incluye el password de la base de datos:
  trátalo como secreto (solo en variables de entorno de Railway, nunca en
  commits, capturas o chats) y rótalo si llega a exponerse.

## Pendiente / próximos pasos sugeridos

- Interfaz POS dedicada (hoy la carga de ventas se hace vía Django Admin).
- Integración real con un proveedor de facturación electrónica certificado
  por el SAR cuando el negocio lo contrate.
- Reportes más completos (ventas por vendedor/sucursal, rotación de
  inventario, cuentas por cobrar de clientes a crédito).
- Permisos granulares por rol (actualmente `rol` es informativo; falta
  restringir vistas/acciones del admin según rol).
