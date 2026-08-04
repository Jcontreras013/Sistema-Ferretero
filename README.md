# Sistema Ferretero

Aplicación web construida con Django para administrar una ferretería de una
sola tienda: punto de venta (POS), inventario, clientes/proveedores, caja y
reportes, adaptada al régimen fiscal de Honduras (SAR).

## Funcionalidades

- **Configuración fiscal del negocio:** RTN, régimen de facturación (CAI
  impreso o CFE electrónico), rango de facturas autorizado, fecha límite de
  emisión, tasa de ISV por defecto.
- **Numeración de factura formato Honduras:** `000-001-01-00000001`, con
  control automático del rango autorizado por el CAI.
- **Punto de venta (POS):** búsqueda o escaneo de código de barras (Enter
  agrega el producto), carrito interactivo, ISV diferenciado por producto,
  forma de pago, y selección de cliente con buscador. Al elegir un cliente ya
  registrado, su RTN se autocompleta; si no lo tiene, puedes escribirlo ahí
  mismo y se guarda al cobrar. También puedes crear un cliente nuevo sin salir
  del POS.
- **Caja:** apertura y cierre con arqueo (monto esperado vs. contado,
  diferencia), historial de sesiones.
- **Notas de crédito:** devoluciones parciales o totales sobre una factura,
  con restitución automática de stock.
- **Inventario:** productos con código, código de barras, categoría,
  proveedor, precios de compra/venta, ISV, stock, unidad de medida (unidad,
  par, docena, caja, rollo, metro, pie, libra, kilogramo, litro, galón, saco,
  quintal — para vender tornillos por caja, cable por metro, cemento por
  saco, pintura por galón, etc.); alertas de stock bajo; movimientos de
  inventario con motivo (compra, venta, merma, daño, robo, devolución, otro).
- **Clientes y proveedores:** administración (CRUD) de ambos, historial de
  compras por cliente.
- **Compras y gastos (solo administradores):** registro de facturas
  clasificadas en tres categorías — compra a proveedor (mercadería), gasto
  operativo (servicios, renta, etc.) o pago a acreedor (préstamos, cuentas
  por pagar a terceros) — con proveedor/acreedor, no. de factura, subtotal y
  tasa de ISV (0% para pagos que no generan crédito fiscal, como cuotas de
  préstamo). No afecta el stock — es un registro fiscal, independiente de
  los movimientos de inventario.
- **Declaración jurada de ISV (solo administradores):** cruza el débito
  fiscal (ISV cobrado en ventas, neto de notas de crédito) contra el crédito
  fiscal (ISV pagado en las facturas de Compras y gastos, de cualquier
  categoría) por tasa, y calcula el ISV a pagar o el excedente de crédito
  fiscal a favor para el período — listo para transcribir en el formulario
  del SAR. No sustituye la declaración oficial ni asesoría de un contador.
- **Reporte de compras y gastos para el contador (solo administradores):**
  el mismo registro de facturas agrupado por categoría (proveedor, gasto
  operativo, acreedor), con subtotales por categoría y total general,
  pensado para entregarle al contador junto con la declaración de ISV.
- **Ventas:** historial con filtros por fecha y cliente, detalle de factura
  imprimible, anulación de ventas (solo administradores).
- **Roles:** Administrador (todo) y Cajero (POS, ventas, clientes, consulta
  de productos) — los reportes, configuración del negocio, categorías,
  proveedores y edición de productos son solo para administradores.
- **Gestión de usuarios (solo administradores):** crear, editar rol/contraseña
  y eliminar usuarios desde el panel (Admin → Usuarios).
- **Bitácora de auditoría (solo administradores):** registro de quién creó,
  modificó o eliminó cada producto, cliente, venta, nota de crédito, sesión
  de caja o usuario.
- **Reportes (solo administradores):** ventas por período, productos más
  vendidos, ganancias, stock bajo, ISV cobrado por tasa (para la declaración
  ante el SAR), flujo de caja.
- **Impresión de tickets:** formato configurable (térmica 80mm, térmica
  58mm o matriz de puntos/carta), con opción de impresión automática al
  cobrar.
- **Importar inventario desde otro sistema (solo administradores):** en
  Productos → Importar, sube un archivo `.xlsx`, `.xls` o `.csv`. El sistema
  detecta automáticamente las columnas y muestra una vista previa para
  corregir el mapeo antes de confirmar.

## Stack

- Python 3.11 + Django 5.2
- SQLite en desarrollo, PostgreSQL en producción (vía `DATABASE_URL`)
- Bootstrap 5 + Bootstrap Icons (vendorizados localmente, sin depender de un
  CDN)

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_groups        # crea los grupos "Administrador" y "Cajero"
python manage.py createsuperuser    # tu usuario administrador
python manage.py seed_demo          # datos de ejemplo opcionales (empresa, categorías, productos, clientes)

python manage.py runserver
```

Luego visita `http://localhost:8000/`, inicia sesión con el usuario creado y
entra a **Admin → Configuración del negocio** para poner el RTN, CAI y rango
de facturas reales de tu ferretería.

Para crear un usuario cajero (sin acceso a reportes/configuración), usa
**Admin → Usuarios** desde el panel, o por línea de comandos:

```bash
python manage.py shell -c "
from django.contrib.auth.models import User, Group
u = User.objects.create_user('cajero1', password='una-contraseña-segura')
u.groups.add(Group.objects.get(name='Cajero'))
"
```

## Despliegue en Railway + Neon

El repositorio incluye `railway.json` para desplegar en
[Railway](https://railway.app), usando PostgreSQL externo gratuito en
[Neon](https://neon.tech) en vez de un plugin de base de datos de Railway.

### 1. Base de datos en Neon

1. Crea una cuenta en [neon.tech](https://neon.tech) y un proyecto.
2. En **Connection Details**, copia el connection string (usa el host con
   `-pooler` para conexiones desde una app web).
3. Guárdalo solo en las variables de entorno de Railway (paso siguiente) —
   nunca lo subas al repo ni lo compartas en texto plano.

### 2. Desplegar en Railway

1. En Railway: **New Project** → **Deploy from GitHub repo**, elige este
   repositorio y la rama a desplegar. Railway detecta `railway.json` y usa
   Nixpacks para el build de Python.
2. En **Variables**, define:
   - `DATABASE_URL`: el connection string de Neon.
   - `SECRET_KEY`: una clave larga y aleatoria.
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: tu dominio de Railway (ver paso 3), separado por comas
     junto con `localhost,127.0.0.1`.
   - `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`,
     `DJANGO_SUPERUSER_EMAIL`: crean el superusuario automáticamente en el
     arranque (`ensure_admin`), sin necesidad de shell interactivo.
   - (Opcional) `SEED_DEMO=true` para cargar datos de ejemplo la primera vez.
3. En **Settings → Networking**, activa **Generate Domain**. Copia ese
   dominio y agrégalo a `ALLOWED_HOSTS` (con esquema `https://` no hace
   falta, `settings.py` ya arma `CSRF_TRUSTED_ORIGINS` a partir de
   `ALLOWED_HOSTS`), luego guarda para forzar un redeploy.
4. El arranque corre `migrate`, `seed_groups`, `ensure_admin` y (si aplica)
   `seed_demo` antes de levantar `gunicorn`.
5. Entra a **Admin → Configuración del negocio** y reemplaza los datos de
   ejemplo con el RTN, CAI y rango de facturas reales de tu ferretería antes
   de facturar en producción.

## Estructura del proyecto

- `config/` – configuración del proyecto Django (settings, urls).
- `core/` – panel principal (dashboard), configuración fiscal del negocio
  (`Company`), roles/permisos, comandos `seed_demo`/`seed_groups`/`ensure_admin`.
- `inventory/` – categorías, proveedores, productos y movimientos de
  inventario.
- `clients/` – clientes.
- `sales/` – punto de venta, caja, facturas, notas de crédito.
- `reports/` – reportes de ventas, productos top, ganancias, stock bajo,
  impuestos y flujo de caja.

## Notas

- **Eliminar una factura ya emitida rompe la secuencia correlativa
  autorizada por el CAI y normalmente no es válido ante el SAR** — lo
  correcto fiscalmente es anular, no eliminar.
- El régimen CFE (Factura Electrónica) usa por ahora una numeración interna
  simple; la integración real con el webservice del SAR para timbrado
  electrónico **no está implementada** — requiere las especificaciones
  técnicas del SAR y el certificado/credenciales del negocio.
- La base de datos por defecto es SQLite (`db.sqlite3`) para desarrollo. En
  producción se usa PostgreSQL vía `DATABASE_URL`.
- La impresión funciona a través del diálogo de impresión del navegador
  hacia la impresora instalada en el sistema operativo — no requiere
  hardware especial ni drivers propios, pero sí que la impresora esté
  correctamente instalada.
- Pendiente para una próxima fase: órdenes de compra y cuentas por pagar a
  proveedores, crédito/fiado a clientes, modo offline con sincronización, e
  integración directa con hardware (impresión ESC/POS por USB).
