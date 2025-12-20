from rest_framework import serializers
from .models import Article, Favorite


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información básica de artículos.

    Se usa cuando listamos favoritos para mostrar detalles del artículo.
    """

    class Meta:
        model = Article
        fields = [
            'id',
            'external_id',
            'title',
            'url',
            'news_site',
            'sentiment_score',
            'published_at',
        ]
        read_only_fields = fields


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Favorite.

    Incluye información completa del artículo asociado mediante
    nested serialization.
    """

    article = ArticleSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = [
            'id',
            'article',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
