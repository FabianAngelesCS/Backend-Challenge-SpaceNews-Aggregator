"""
Views para la API de artículos espaciales.

Incluye reportes mensuales calculados con ORM puro,
sin usar loops Python para aggregations.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import TruncMonth
from typing import List, Dict, Any
from .models import Article, Favorite
from .serializers import FavoriteSerializer, ArticleSerializer


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorite_article(request, article_id: int) -> Response:
    """
    Marca un artículo como favorito para el usuario autenticado.

    Endpoint: POST /api/articles/{id}/favorite/

    Args:
        request: Request object con usuario autenticado
        article_id: ID del artículo a marcar como favorito

    Returns:
        Response con mensaje de éxito o error

    Status Codes:
        201: Favorito creado exitosamente
        200: Ya estaba en favoritos
        404: Artículo no encontrado
        401: No autenticado
    """

    # Verificar que el artículo existe
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return Response(
            {'error': 'Artículo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Crear favorito para el usuario autenticado
    # get_or_create previene duplicados automáticamente
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        article=article
    )

    if created:
        return Response(
            {
                'message': 'Artículo agregado a favoritos',
                'article_id': article.id,
                'article_title': article.title
            },
            status=status.HTTP_201_CREATED
        )
    else:
        return Response(
            {
                'message': 'El artículo ya está en tus favoritos',
                'article_id': article.id
            },
            status=status.HTTP_200_OK
        )


class FavoriteListView(generics.ListAPIView):
    """
    Lista los artículos favoritos del usuario autenticado.

    Endpoint: GET /api/favorites/

    **SEGURIDAD CRÍTICA**:
    - Solo retorna favoritos del usuario que hace la petición
    - Usa request.user para filtrar el QuerySet
    - Un usuario NO puede ver favoritos de otros

    Permissions:
        - IsAuthenticated: Solo usuarios autenticados

    Returns:
        Lista de favoritos con información del artículo incluida
    """

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna favoritos SOLO del usuario autenticado.

        CRÍTICO: Este filtrado previene fuga de datos entre usuarios.
        """
        # ⚠️ CRITICAL: Filtrar por request.user
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('article').order_by('-created_at')
