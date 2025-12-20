"""
Tests de seguridad para el sistema de favoritos.

Valida que los usuarios solo puedan acceder a sus propios favoritos.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.articles.models import Article, Favorite


class FavoriteSecurityTest(TestCase):
    """
    Tests de seguridad crítica: aislamiento de datos entre usuarios.
    """

    def setUp(self):
        """Configurar datos de prueba."""
        # Crear usuarios
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )

        # Crear artículos
        self.article1 = Article.objects.create(
            external_id=1001,
            title='Test Article 1',
            url='http://test.com/1',
            news_site='NASA',
            published_at='2023-12-01T00:00:00Z',
            sentiment_score=0
        )
        self.article2 = Article.objects.create(
            external_id=1002,
            title='Test Article 2',
            url='http://test.com/2',
            news_site='NASA',
            published_at='2023-12-01T00:00:00Z',
            sentiment_score=1
        )

        # Cliente API
        self.client = APIClient()

    def test_user_can_only_see_own_favorites(self):
        """
        TEST CRÍTICO: Los usuarios solo ven sus propios favoritos.
        """
        # User1 crea favorito
        Favorite.objects.create(user=self.user1, article=self.article1)

        # User2 crea favorito
        Favorite.objects.create(user=self.user2, article=self.article2)

        # User1 lista favoritos
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/favorites/')

        # Verificar que User1 solo ve su favorito
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['article']['id'],
            self.article1.id
        )

    def test_unauthenticated_cannot_access_favorites(self):
        """
        Test: Usuarios no autenticados reciben 401.
        """
        response = self.client.get('/api/favorites/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_favorite_requires_authentication(self):
        """
        Test: Crear favorito requiere autenticación.
        """
        response = self.client.post(f'/api/articles/{self.article1.id}/favorite/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_favorite_with_invalid_article(self):
        """
        Test: Crear favorito con artículo inexistente retorna 404.
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/articles/99999/favorite/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_favorite_returns_200(self):
        """
        Test: Crear favorito duplicado retorna 200 OK.
        """
        self.client.force_authenticate(user=self.user1)

        # Primera vez - 201 Created
        response1 = self.client.post(f'/api/articles/{self.article1.id}/favorite/')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Segunda vez - 200 OK
        response2 = self.client.post(f'/api/articles/{self.article1.id}/favorite/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verificar que solo hay 1 favorito
        self.assertEqual(Favorite.objects.filter(user=self.user1).count(), 1)