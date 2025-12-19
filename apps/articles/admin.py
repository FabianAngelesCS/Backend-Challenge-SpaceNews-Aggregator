from django.contrib import admin
from typing import List, Tuple
from .models import Article, Favorite


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Article.
    """

    list_display: Tuple[str, ...] = (
        'external_id',
        'title',
        'news_site',
        'sentiment_score',
        'published_at',
        'created_at',
    )

    list_filter: Tuple[str, ...] = (
        'news_site',
        'sentiment_score',
        'published_at',
        'created_at',
    )

    search_fields: Tuple[str, ...] = (
        'title',
        'news_site',
        'external_id',
    )

    readonly_fields: Tuple[str, ...] = (
        'created_at',
        'updated_at',
    )

    ordering: Tuple[str, ...] = ('-published_at',)

    date_hierarchy: str = 'published_at'

    fieldsets: Tuple[Tuple[str, dict], ...] = (
        ('Información Externa', {
            'fields': ('external_id', 'url')
        }),
        ('Contenido', {
            'fields': ('title', 'news_site', 'sentiment_score')
        }),
        ('Fechas', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Favorite.
    """

    list_display: Tuple[str, ...] = (
        'id',
        'user',
        'get_article_title',
        'created_at',
    )

    list_filter: Tuple[str, ...] = (
        'user',
        'created_at',
    )

    search_fields: Tuple[str, ...] = (
        'user__username',
        'article__title',
    )

    readonly_fields: Tuple[str, ...] = (
        'created_at',
    )

    ordering: Tuple[str, ...] = ('-created_at',)

    date_hierarchy: str = 'created_at'

    autocomplete_fields: List[str] = ['article']

    def get_article_title(self, obj: Favorite) -> str:
        """Muestra el título del artículo favorito (truncado)."""
        return obj.article.title[:50] + '...' if len(obj.article.title) > 50 else obj.article.title

    get_article_title.short_description = 'Article Title'
