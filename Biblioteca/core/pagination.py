"""Paginación sencilla de listas en memoria (los datos de este proyecto son pequeños)."""
from django.conf import settings
from django.core.paginator import Paginator


def paginate(request, items, per_page=None):
    """Devuelve el contexto de paginación para los templates.

    - page_obj: la página actual (sus elementos, número, si hay anterior/siguiente…)
    - page_range: números a mostrar, con "…" cuando hay muchas páginas
    - querystring: los filtros actuales (q, status…) sin `page`, para conservarlos en los enlaces
    """
    paginator = Paginator(items, per_page or settings.PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return {
        'page_obj': page_obj,
        'page_range': list(paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)),
        'querystring': params.urlencode(),
    }
