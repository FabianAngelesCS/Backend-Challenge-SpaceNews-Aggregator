"""
Views para la API de artículos espaciales.

Incluye reportes mensuales calculados con ORM puro,
sin usar loops Python para aggregations.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import TruncMonth
from typing import List, Dict, Any
from .models import Article


class MonthlyReportView(APIView):
    """
    Endpoint público para reportes mensuales de artículos.

    Calcula estadísticas agrupadas por mes usando SOLO capacidades del ORM:
    - Total de artículos por mes
    - Sitio de noticias más frecuente (top_site) por mes

    **CRÍTICO**: Todos los cálculos se realizan a nivel de base de datos
    usando annotate/aggregate. NO se usan loops Python para calcular totales.

    Endpoint: GET /api/reports/monthly/

    Response:
        [
            {
                "month": "2023-11",
                "total": 45,
                "top_site": "SpaceNews"
            },
            ...
        ]
    """

    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        """
        Obtiene reportes mensuales de artículos.

        Estrategia de implementación:
        1. Usar TruncMonth para agrupar por mes
        2. Usar annotate(Count()) para totales por mes
        3. Usar Subquery para obtener top_site por mes
        4. Todo calculado en la base de datos (no loops Python)

        Returns:
            Response con lista de reportes mensuales ordenados por mes descendente
        """

        # Subquery para obtener el sitio con más artículos por mes
        # Esta subquery se ejecuta POR CADA mes en la query principal
        top_site_subquery = (
            Article.objects
            .filter(
                published_at__year=OuterRef('month__year'),
                published_at__month=OuterRef('month__month')
            )
            .values('news_site')
            .annotate(site_count=Count('id'))
            .order_by('-site_count')
            .values('news_site')[:1]
        )

        # Query principal: agrupa por mes y cuenta totales
        # Incluye el top_site usando la subquery
        monthly_reports = (
            Article.objects
            .annotate(month=TruncMonth('published_at'))
            .values('month')
            .annotate(
                total=Count('id'),
                top_site=Subquery(top_site_subquery)
            )
            .order_by('-month')
        )

        # Formatear respuesta
        # NOTA: Este loop SOLO formatea datos ya calculados por el ORM,
        # NO realiza cálculos. Esto es aceptable según las reglas.
        reports: List[Dict[str, Any]] = [
            {
                'month': report['month'].strftime('%Y-%m') if report['month'] else None,
                'total': report['total'],
                'top_site': report['top_site'] or 'Unknown'
            }
            for report in monthly_reports
        ]

        return Response(reports)
