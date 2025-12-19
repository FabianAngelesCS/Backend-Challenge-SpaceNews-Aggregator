"""
Management command para sincronizar noticias espaciales.

Este comando consume la API externa de Spaceflight News y
almacena los artículos en la base de datos local aplicando
filtros y análisis de sentimiento.

Uso:
    python manage.py sync_news --limit 100
"""

from django.core.management.base import BaseCommand, CommandParser
from typing import Any
from apps.articles.services import NewsService


class Command(BaseCommand):
    """
    Comando de Django para sincronizar noticias espaciales.

    Utiliza el NewsService (Service Layer) para mantener la
    separación entre lógica de negocio y presentación.
    """

    help = 'Sincroniza noticias espaciales desde la API externa de Spaceflight News'

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define los argumentos del comando.

        Args:
            parser: Parser de argumentos de Django
        """
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Número máximo de artículos a sincronizar (default: 100)'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Ejecuta el comando de sincronización.

        Args:
            *args: Argumentos posicionales
            **options: Argumentos opcionales del comando
        """
        limit: int = options['limit']

        self.stdout.write(
            self.style.HTTP_INFO(f'\n{"="*60}')
        )
        self.stdout.write(
            self.style.HTTP_INFO('SINCRONIZADOR DE NOTICIAS ESPACIALES')
        )
        self.stdout.write(
            self.style.HTTP_INFO(f'{"="*60}\n')
        )

        self.stdout.write(f'Iniciando sincronización con límite de {limit} artículos...\n')

        # Instanciar el servicio y ejecutar sincronización
        service = NewsService()

        try:
            stats = service.sync_articles(limit=limit)

            # Mostrar estadísticas con colores
            self.stdout.write(
                self.style.HTTP_INFO(f'\n{"="*60}')
            )
            self.stdout.write(
                self.style.HTTP_INFO('RESULTADOS DE LA SINCRONIZACIÓN')
            )
            self.stdout.write(
                self.style.HTTP_INFO(f'{"="*60}\n')
            )

            # Artículos procesados
            self.stdout.write(
                f'Total procesados:  {stats["processed"]}'
            )

            # Artículos guardados (éxito)
            if stats['saved'] > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Guardados:        {stats["saved"]}')
                )
            else:
                self.stdout.write(f'     Guardados:        {stats["saved"]}')

            # Artículos filtrados (advertencia)
            if stats['filtered'] > 0:
                self.stdout.write(
                    self.style.WARNING(f'[!]  Filtrados:        {stats["filtered"]} (contenido censurado)')
                )
            else:
                self.stdout.write(f'     Filtrados:        {stats["filtered"]}')

            # Errores
            if stats['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(f'[X]  Errores:          {stats["errors"]}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Errores:          {stats["errors"]}')
                )

            self.stdout.write(
                self.style.HTTP_INFO(f'\n{"="*60}\n')
            )

            # Mensaje final según resultados
            if stats['errors'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        'Sincronización completada con errores. '
                        'Revisa los logs para más detalles.'
                    )
                )
            elif stats['saved'] == 0:
                self.stdout.write(
                    self.style.WARNING(
                        'No se guardaron artículos nuevos. '
                        'Todos fueron filtrados o ya existían.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'¡Sincronización exitosa! Se guardaron {stats["saved"]} artículos.'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n[ERROR] Error critico durante la sincronizacion: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR('Revisa los logs para mas detalles.\n')
            )
            raise
