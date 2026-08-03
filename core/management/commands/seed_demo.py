import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand

from clients.models import Client
from core.models import Company
from inventory.models import Category, Product, Provider


class Command(BaseCommand):
    help = "Carga datos de ejemplo para una ferretería: empresa, categorías, proveedores, productos y clientes."

    def handle(self, *args, **options):
        call_command("seed_groups")

        company = Company.load()
        if not company.trade_name:
            company.business_name = "Ferretería Demo, S. de R.L."
            company.trade_name = "Ferretería Demo"
            company.rtn = "08019999123456"
            company.address = "Col. Centro, Tegucigalpa, Honduras"
            company.phone = "2222-0000"
            company.email = "contacto@ferreteriademo.hn"
            company.invoice_regime = Company.REGIME_CAI
            company.cai_code = "1A2B3C-4D5E6F-7A8B9C-0D1E2F-A1B2C3"
            company.establishment_code = "001"
            company.emission_point_code = "001"
            company.document_type_code = "01"
            company.range_start = 1
            company.range_end = 10000
            company.next_correlative = 1
            company.emission_limit_date = datetime.date.today() + datetime.timedelta(days=365)
            company.default_isv_rate = 15
            company.save()

        categories = {}
        for name in [
            "Herramientas manuales", "Herramientas eléctricas", "Plomería", "Electricidad",
            "Pintura", "Tornillería y anclajes", "Cemento y construcción", "Seguridad industrial",
        ]:
            category, _ = Category.objects.get_or_create(name=name)
            categories[name] = category

        provider1, _ = Provider.objects.get_or_create(
            name="Ferretera Industrial de Honduras",
            defaults={"contact_name": "Carlos Pérez", "phone": "5555-1234", "email": "ventas@ferreind.hn"},
        )
        provider2, _ = Provider.objects.get_or_create(
            name="Distribuidora de Materiales del Valle",
            defaults={"contact_name": "María López", "phone": "5555-5678", "email": "pedidos@matvalle.hn"},
        )

        soon = datetime.date.today() + datetime.timedelta(days=60)

        products = [
            ("HM001", "7501234560014", "Martillo de uña 16oz", categories["Herramientas manuales"], provider1, "unidad", 120.00, 185.00, 15, 12, None),
            ("HM002", "7501234560021", "Destornillador plano 6\"", categories["Herramientas manuales"], provider1, "unidad", 45.00, 79.00, 15, 20, None),
            ("HM003", "7501234560038", "Cinta métrica 5m", categories["Herramientas manuales"], provider1, "unidad", 60.00, 110.00, 15, 15, None),
            ("HM004", "7501234560045", "Llave ajustable 10\"", categories["Herramientas manuales"], provider1, "unidad", 150.00, 240.00, 15, 8, None),
            ("HE001", "7501234560052", "Taladro percutor 1/2\" 650W", categories["Herramientas eléctricas"], provider2, "unidad", 1450.00, 2200.00, 15, 4, None),
            ("HE002", "7501234560069", "Amoladora angular 4.5\"", categories["Herramientas eléctricas"], provider2, "unidad", 980.00, 1450.00, 15, 5, None),
            ("PL001", "7501234560076", "Tubo PVC 1/2\" (6m)", categories["Plomería"], provider2, "unidad", 65.00, 105.00, 15, 30, None),
            ("PL002", "7501234560083", "Codo PVC 1/2\"", categories["Plomería"], provider2, "unidad", 3.50, 6.00, 15, 100, None),
            ("PL003", "7501234560090", "Cinta teflón 1/2\"", categories["Plomería"], provider2, "unidad", 5.00, 9.00, 15, 50, None),
            ("EL001", "7501234560106", "Cable eléctrico #12 THHN", categories["Electricidad"], provider1, "metro", 8.50, 13.00, 15, 200, None),
            ("EL002", "7501234560113", "Interruptor sencillo", categories["Electricidad"], provider1, "unidad", 25.00, 42.00, 15, 40, None),
            ("EL003", "7501234560120", "Toma corriente doble", categories["Electricidad"], provider1, "unidad", 28.00, 48.00, 15, 35, None),
            ("PI001", "7501234560137", "Pintura látex blanca (galón)", categories["Pintura"], provider2, "galon", 320.00, 495.00, 15, 18, soon),
            ("PI002", "7501234560144", "Brocha 3\"", categories["Pintura"], provider2, "unidad", 35.00, 65.00, 15, 25, None),
            ("TO001", "7501234560151", "Tornillo para madera 1\" (caja 100u)", categories["Tornillería y anclajes"], provider1, "caja", 45.00, 75.00, 15, 20, None),
            ("TO002", "7501234560168", "Anclaje de expansión 3/8\"", categories["Tornillería y anclajes"], provider1, "unidad", 6.00, 11.00, 15, 80, None),
            ("CE001", "7501234560175", "Cemento gris (saco 42.5kg)", categories["Cemento y construcción"], provider2, "saco", 165.00, 215.00, 15, 40, None),
            ("CE002", "7501234560182", "Varilla de hierro 3/8\" (6m)", categories["Cemento y construcción"], provider2, "unidad", 95.00, 140.00, 15, 25, None),
            ("SI001", "7501234560199", "Guantes de cuero para trabajo", categories["Seguridad industrial"], provider1, "par", 45.00, 79.00, 15, 30, None),
            ("SI002", "7501234560205", "Casco de seguridad", categories["Seguridad industrial"], provider1, "unidad", 110.00, 175.00, 15, 15, None),
        ]

        for code, barcode, name, category, provider, unit, purchase_price, sale_price, tax_rate, stock, expiration_date in products:
            Product.objects.get_or_create(
                code=code,
                defaults={
                    "barcode": barcode,
                    "name": name,
                    "category": category,
                    "provider": provider,
                    "unit": unit,
                    "purchase_price": purchase_price,
                    "sale_price": sale_price,
                    "tax_rate": tax_rate,
                    "stock": stock,
                    "min_stock": 10,
                    "expiration_date": expiration_date,
                },
            )

        clients = [
            ("Consumidor Final", "", "", ""),
            ("Juan Gómez", "08019876543210", "5555-1111", "juan.gomez@example.com"),
            ("Constructora Martínez S. de R.L.", "08011234567890", "5555-2222", "compras@constructoramartinez.hn"),
        ]
        for name, document, phone, email in clients:
            Client.objects.get_or_create(name=name, defaults={"document": document, "phone": phone, "email": email})

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados correctamente."))
