"""
Tests de integración para el sincronizador de noticias.

Incluye mocking de la API externa de Spaceflight News según
requerimientos del challenge.
"""

from unittest.mock import patch, Mock
from django.test import TestCase
from django.core.management import call_command
from apps.articles.models import Article
from apps.articles.services import NewsService


class SyncNewsCommandTest(TestCase):
    """
    Tests para el comando sync_news con mocks de API externa.

    Este test cumple el requisito del challenge:
    "Al menos 1 test de integración con mocks para la API externa"
    """

    @patch('apps.articles.services.requests.get')
    def test_sync_filters_spacex_articles(self, mock_get):
        """
        Test de integración: Verifica que el sincronizador filtra
        artículos con palabras censuradas (SpaceX/Musk).

        Mock: API externa de Spaceflight News
        """
        # Configurar mock de la API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 1,
                    'title': 'NASA launches new Mars rover',
                    'url': 'http://test.com/1',
                    'news_site': 'NASA',
                    'published_at': '2023-12-01T00:00:00Z'
                },
                {
                    'id': 2,
                    'title': 'SpaceX breaks launch record',  # Debe filtrarse
                    'url': 'http://test.com/2',
                    'news_site': 'SpaceX News',
                    'published_at': '2023-12-01T00:00:00Z'
                },
                {
                    'id': 3,
                    'title': 'Elon Musk announces new plans',  # Debe filtrarse
                    'url': 'http://test.com/3',
                    'news_site': 'TechNews',
                    'published_at': '2023-12-01T00:00:00Z'
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Ejecutar comando
        call_command('sync_news', '--limit=10')

        # Verificaciones
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.first()
        self.assertIn('NASA', article.title)
        self.assertNotIn('SpaceX', article.title)
        self.assertNotIn('Musk', article.title)

    @patch('apps.articles.services.requests.get')
    def test_sync_calculates_sentiment_score(self, mock_get):
        """
        Test: Verifica el cálculo correcto del sentiment score
        basado en keywords (Mars/Moon).
        """
        # Mock de la API con artículos sobre Mars y Moon
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 10,
                    'title': 'New discoveries on Mars surface',
                    'url': 'http://test.com/10',
                    'news_site': 'NASA',
                    'published_at': '2023-12-01T00:00:00Z'
                },
                {
                    'id': 11,
                    'title': 'Moon mission scheduled for 2025',
                    'url': 'http://test.com/11',
                    'news_site': 'NASA',
                    'published_at': '2023-12-01T00:00:00Z'
                },
                {
                    'id': 12,
                    'title': 'ISS conducts new experiments',
                    'url': 'http://test.com/12',
                    'news_site': 'NASA',
                    'published_at': '2023-12-01T00:00:00Z'
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Limpiar DB
        Article.objects.all().delete()

        # Ejecutar sincronización
        service = NewsService()
        stats = service.sync_articles(limit=10)

        # Verificaciones
        self.assertEqual(stats['saved'], 3)

        # Verificar sentiment scores
        mars_article = Article.objects.get(external_id=10)
        self.assertEqual(mars_article.sentiment_score, 1)

        moon_article = Article.objects.get(external_id=11)
        self.assertEqual(moon_article.sentiment_score, 1)

        iss_article = Article.objects.get(external_id=12)
        self.assertEqual(iss_article.sentiment_score, 0)

    @patch('apps.articles.services.requests.get')
    def test_sync_handles_duplicates(self, mock_get):
        """
        Test: Verifica que update_or_create previene duplicados.
        """
        # Mock de API
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 100,
                    'title': 'Test Article',
                    'url': 'http://test.com/100',
                    'news_site': 'NASA',
                    'published_at': '2023-12-01T00:00:00Z'
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Limpiar DB
        Article.objects.all().delete()

        # Primera sincronización
        service = NewsService()
        service.sync_articles(limit=1)
        count_after_first = Article.objects.count()

        # Segunda sincronización (mismo artículo)
        service.sync_articles(limit=1)
        count_after_second = Article.objects.count()

        # Verificar que no se duplicó
        self.assertEqual(count_after_first, count_after_second)
        self.assertEqual(Article.objects.count(), 1)


class NewsServiceTest(TestCase):
    """
    Tests unitarios para el NewsService.
    """

    def test_should_filter_spacex(self):
        """Test: Detecta correctamente keyword 'spacex'."""
        service = NewsService()

        self.assertTrue(service._should_filter('SpaceX launches satellite'))
        self.assertTrue(service._should_filter('spacex news'))
        self.assertFalse(service._should_filter('NASA mission'))

    def test_should_filter_musk(self):
        """Test: Detecta correctamente keyword 'musk'."""
        service = NewsService()

        self.assertTrue(service._should_filter('Elon Musk interview'))
        self.assertTrue(service._should_filter('MUSK announces'))
        self.assertFalse(service._should_filter('NASA announcement'))

    def test_calculate_sentiment_mars(self):
        """Test: Sentiment score = 1 para 'Mars'."""
        service = NewsService()

        self.assertEqual(service._calculate_sentiment('Mission to Mars'), 1)
        self.assertEqual(service._calculate_sentiment('mars rover'), 1)

    def test_calculate_sentiment_moon(self):
        """Test: Sentiment score = 1 para 'Moon'."""
        service = NewsService()

        self.assertEqual(service._calculate_sentiment('Moon landing'), 1)
        self.assertEqual(service._calculate_sentiment('lunar moon base'), 1)

    def test_calculate_sentiment_neutral(self):
        """Test: Sentiment score = 0 para otros títulos."""
        service = NewsService()

        self.assertEqual(service._calculate_sentiment('ISS experiment'), 0)
        self.assertEqual(service._calculate_sentiment('NASA announcement'), 0)