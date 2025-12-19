from django.urls import path
from .views import MonthlyReportView

app_name = 'articles'

urlpatterns = [
    # Reportes mensuales
    path('reports/monthly/', MonthlyReportView.as_view(), name='monthly-reports'),
]
