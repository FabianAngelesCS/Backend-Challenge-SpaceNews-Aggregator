from django.urls import path
from .views import (
    MonthlyReportView,
    FavoriteListView,
    favorite_article,
)

app_name = 'articles'

urlpatterns = [
    # Reportes
    path('reports/monthly/', MonthlyReportView.as_view(), name='monthly-reports'),

    # Favoritos
    path('articles/<int:article_id>/favorite/', favorite_article, name='favorite-article'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
]