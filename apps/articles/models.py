from django.db import models
from django.conf import settings
from typing import Optional


class Article(models.Model):
    """
    Modelo para almacenar artículos de noticias espaciales.

    Los artículos se sincronizan desde la API externa de Spaceflight News
    y se analizan para determinar su contenido (Mars/Moon keywords).
    """

    # Identificador de la API externa
    external_id = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="ID único del artículo en la API externa"
    )

    # Información del artículo
    title = models.CharField(
        max_length=500,
        help_text="Título del artículo"
    )
    url = models.URLField(
        max_length=1000,
        help_text="URL del artículo original"
    )
    news_site = models.CharField(
        max_length=200,
        help_text="Sitio de noticias que publicó el artículo"
    )

    # Análisis de sentimientos
    sentiment_score = models.IntegerField(
        default=0,
        help_text="1 si contiene Mars/Moon, 0 en otro caso"
    )

    # Timestamps
    published_at = models.DateTimeField(
        db_index=True,
        help_text="Fecha de publicación del artículo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación en nuestra DB"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Fecha de última actualización"
    )

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        indexes = [
            models.Index(fields=['published_at', 'news_site']),
        ]

    def __str__(self) -> str:
        return self.title


class Favorite(models.Model):
    """
    Modelo para gestionar los artículos favoritos de los usuarios.

    Relación Many-to-Many entre User y Article con información adicional
    (timestamp de cuándo se marcó como favorito).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text="Usuario que marcó el artículo como favorito"
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        help_text="Artículo marcado como favorito"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha en que se marcó como favorito"
    )

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-created_at']
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.article.title[:50]}"
