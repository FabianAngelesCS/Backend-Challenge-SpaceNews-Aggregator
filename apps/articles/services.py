"""
Service Layer - Business Logic

Este módulo contiene la lógica de negocio para la sincronización
de noticias espaciales desde la API externa de Spaceflight News.

Arquitectura:
- Separación clara entre lógica de negocio y presentación
- Single Responsibility Principle en cada método
- Manejo robusto de errores con logging
- Transaction safety con decoradores Django
"""

import requests
import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils.dateparse import parse_datetime
from .models import Article

logger = logging.getLogger(__name__)


class NewsService:
    """
    Servicio para sincronizar noticias espaciales desde API externa.

    Responsabilidades:
    - Consumir Spaceflight News API v4
    - Filtrar contenido según keywords censuradas
    - Analizar sentimiento basado en keywords (Mars/Moon)
    - Persistir artículos en base de datos
    """

    # Configuración de la API externa
    BASE_URL: str = "https://api.spaceflightnewsapi.net/v4/articles/"

    # Keywords para filtrado de contenido
    CENSORED_KEYWORDS: List[str] = ['spacex', 'musk']

    # Keywords para análisis de sentimiento
    SENTIMENT_KEYWORDS: List[str] = ['mars', 'moon']

    def sync_articles(self, limit: int = 100) -> Dict[str, int]:
        """
        Método principal que orquesta la sincronización de artículos.

        Args:
            limit: Número máximo de artículos a sincronizar (default: 100)

        Returns:
            Dict con estadísticas de la sincronización:
            {
                'processed': int,  # Total de artículos procesados
                'saved': int,      # Artículos guardados exitosamente
                'filtered': int,   # Artículos filtrados (censurados)
                'errors': int      # Errores encontrados
            }
        """
        logger.info(f"Iniciando sincronización de artículos (limit={limit})")

        stats: Dict[str, int] = {
            'processed': 0,
            'saved': 0,
            'filtered': 0,
            'errors': 0
        }

        try:
            # Obtener artículos desde la API externa
            articles: List[Dict] = self._fetch_articles(limit=limit)
            logger.info(f"Obtenidos {len(articles)} artículos de la API")

            # Procesar cada artículo
            for article_data in articles:
                stats['processed'] += 1

                try:
                    # Verificar si el artículo debe ser filtrado
                    title: str = article_data.get('title', '')

                    if self._should_filter(title):
                        stats['filtered'] += 1
                        logger.debug(f"Artículo filtrado: {title[:50]}...")
                        continue

                    # Guardar artículo en la base de datos
                    self._save_article(article_data)
                    stats['saved'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    logger.error(
                        f"Error procesando artículo {article_data.get('id')}: {str(e)}",
                        exc_info=True
                    )

            logger.info(
                f"Sincronización completada. "
                f"Procesados: {stats['processed']}, "
                f"Guardados: {stats['saved']}, "
                f"Filtrados: {stats['filtered']}, "
                f"Errores: {stats['errors']}"
            )

        except Exception as e:
            logger.error(f"Error crítico en sincronización: {str(e)}", exc_info=True)
            stats['errors'] += 1

        return stats

    def _fetch_articles(self, limit: int = 100) -> List[Dict]:
        """
        Consume la API externa de Spaceflight News.

        Args:
            limit: Número máximo de artículos a obtener

        Returns:
            Lista de diccionarios con los datos de los artículos

        Raises:
            requests.RequestException: Si hay error en la petición HTTP
        """
        logger.debug(f"Consultando API: {self.BASE_URL}")

        params: Dict[str, any] = {
            'search': 'NASA',
            'limit': limit,
            'ordering': '-published_at'
        }

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            articles: List[Dict] = data.get('results', [])

            logger.debug(f"API respondió con {len(articles)} artículos")
            return articles

        except requests.RequestException as e:
            logger.error(f"Error en petición a API externa: {str(e)}", exc_info=True)
            raise

    def _should_filter(self, title: str) -> bool:
        """
        Verifica si un artículo debe ser filtrado por contener keywords censuradas.

        Args:
            title: Título del artículo a verificar

        Returns:
            True si el artículo debe ser filtrado, False en caso contrario
        """
        if not title:
            return False

        title_lower: str = title.lower()

        for keyword in self.CENSORED_KEYWORDS:
            if keyword.lower() in title_lower:
                logger.debug(f"Keyword censurada detectada: '{keyword}' en título")
                return True

        return False

    def _calculate_sentiment(self, title: str) -> int:
        """
        Analiza el sentimiento del artículo basado en keywords (Mars/Moon).

        Args:
            title: Título del artículo a analizar

        Returns:
            1 si contiene alguna keyword de sentimiento positivo,
            0 en caso contrario
        """
        if not title:
            return 0

        title_lower: str = title.lower()

        for keyword in self.SENTIMENT_KEYWORDS:
            if keyword.lower() in title_lower:
                logger.debug(f"Keyword de sentimiento detectada: '{keyword}'")
                return 1

        return 0

    @transaction.atomic
    def _save_article(self, article_data: Dict) -> Article:
        """
        Guarda o actualiza un artículo en la base de datos.

        Args:
            article_data: Diccionario con los datos del artículo desde la API

        Returns:
            Instancia del Article guardado

        Raises:
            ValueError: Si faltan campos requeridos
            Exception: Si hay error en la persistencia
        """
        # Validar campos requeridos
        required_fields: List[str] = ['id', 'title', 'url', 'news_site', 'published_at']

        for field in required_fields:
            if field not in article_data or not article_data[field]:
                raise ValueError(f"Campo requerido faltante: {field}")

        # Extraer datos del artículo
        external_id: int = article_data['id']
        title: str = article_data['title']
        url: str = article_data['url']
        news_site: str = article_data['news_site']
        published_at_str: str = article_data['published_at']

        # Parsear fecha
        published_at = parse_datetime(published_at_str)
        if not published_at:
            raise ValueError(f"Fecha inválida: {published_at_str}")

        # Calcular sentiment score
        sentiment_score: int = self._calculate_sentiment(title)

        # Guardar o actualizar artículo
        article, created = Article.objects.update_or_create(
            external_id=external_id,
            defaults={
                'title': title,
                'url': url,
                'news_site': news_site,
                'published_at': published_at,
                'sentiment_score': sentiment_score,
            }
        )

        action: str = "creado" if created else "actualizado"
        logger.debug(f"Artículo {action}: {title[:50]}... (external_id={external_id})")

        return article
