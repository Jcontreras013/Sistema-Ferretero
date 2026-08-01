from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from inventario.models import Stock
from ventas.models import Venta


@login_required
def dashboard(request):
    hoy = timezone.localdate()

    ventas_hoy = Venta.objects.filter(estado=Venta.Estado.COMPLETADA, fecha__date=hoy)
    ventas_mes = Venta.objects.filter(
        estado=Venta.Estado.COMPLETADA, fecha__year=hoy.year, fecha__month=hoy.month
    )
    stock_bajo = (
        Stock.objects.filter(cantidad__lte=F("producto__stock_minimo"))
        .select_related("producto", "sucursal")
        .order_by("cantidad")[:20]
    )
    ultimas_ventas = Venta.objects.select_related("sucursal", "cliente").order_by("-fecha")[:10]

    context = {
        "total_ventas_hoy": ventas_hoy.aggregate(t=Sum("total"))["t"] or 0,
        "cantidad_ventas_hoy": ventas_hoy.count(),
        "total_ventas_mes": ventas_mes.aggregate(t=Sum("total"))["t"] or 0,
        "stock_bajo": stock_bajo,
        "ultimas_ventas": ultimas_ventas,
    }
    return render(request, "dashboard.html", context)
