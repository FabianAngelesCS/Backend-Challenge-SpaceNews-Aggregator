# SpaceNews Aggregator

Backend API REST para agregación y gestión de noticias espaciales con autenticación JWT, análisis de sentimiento y reportes estadísticos.

## 🚀 Características

- **Sincronización de Noticias**: Consume Spaceflight News API v4 con búsqueda de contenido NASA
- **Filtrado Inteligente**: Censura automática de contenido con keywords específicas (SpaceX/Musk)
- **Análisis de Sentimiento**: Clasificación de artículos basada en keywords (Mars/Moon)
- **Sistema de Favoritos**: Gestión de favoritos por usuario con autenticación JWT
- **Reportes Mensuales**: Estadísticas agregadas usando ORM puro (sin loops Python)
- **Tests Completos**: Suite de 13 tests con mocking de APIs externas
- **Seguridad**: Aislamiento estricto de datos entre usuarios

## 📋 Stack Tecnológico

- **Django 4.2.7** - Framework web principal
- **Django REST Framework 3.14.0** - API REST
- **Simple JWT 5.3.0** - Autenticación JWT
- **SQLite** - Base de datos (desarrollo)
- **PostgreSQL** - Base de datos (producción - opcional)
- **Requests 2.31.0** - Cliente HTTP para API externa
- **Python 3.10+** - Lenguaje de programación

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd Backend-Challenge-SpaceNews-Aggregator
```

### 2. Crear y activar entorno virtual

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

**Nota:** El proyecto usa SQLite para desarrollo, por lo que NO necesitas instalar `psycopg2-binary`. El archivo `requirements.txt` incluye `setuptools` para compatibilidad con Python 3.12+.

### 4. Configurar variables de entorno

**Windows (PowerShell/CMD):**
```bash
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

El proyecto usa SQLite por defecto, no necesitas modificar nada en el `.env` para desarrollo. Para producción con PostgreSQL, configura las variables correspondientes en `.env`.

### 5. Ejecutar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser

# Credenciales sugeridas para pruebas:
# Username: admin
# Email: admin@spacenews.com
# Password: admin123
```

### 7. Sincronizar artículos iniciales
```bash
python manage.py sync_news --limit 50
```

### 8. Iniciar servidor
```bash
python manage.py runserver
```

El servidor estará disponible en: `http://127.0.0.1:8000`

## 🔑 Credenciales de Prueba

Después de crear el superusuario, tendrás acceso a:

**Admin Panel:** `http://127.0.0.1:8000/admin/`
- Username: `admin`
- Password: `admin123`

**API REST con JWT:**
- Usa las mismas credenciales para obtener tokens

## 📡 API Endpoints

### Autenticación (JWT)

#### Obtener Token de Acceso
```bash
POST /api/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Respuesta:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Refrescar Token
```bash
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Reportes (Público)

#### Reportes Mensuales
```bash
GET /api/reports/monthly/
```

**Respuesta:**
```json
[
  {
    "month": "2025-12",
    "total": 49,
    "top_site": "NASA"
  },
  {
    "month": "2025-11",
    "total": 23,
    "top_site": "SpaceNews"
  }
]
```

**Características:**
- Endpoint público (no requiere autenticación)
- Cálculos realizados 100% con ORM (sin loops Python)
- Usa `TruncMonth` y `Subquery` para optimización
- Ordenado por mes descendente

### Favoritos (Requiere Autenticación)

#### Marcar Artículo como Favorito
```bash
POST /api/articles/{id}/favorite/
Authorization: Bearer {access_token}
```

**Respuesta (201 Created - primera vez):**
```json
{
  "message": "Artículo agregado a favoritos",
  "article_id": 1,
  "article_title": "Wind-Sculpted Landscapes: Investigating the Martian..."
}
```

**Respuesta (200 OK - ya existe):**
```json
{
  "message": "El artículo ya está en tus favoritos",
  "article_id": 1
}
```

**Errores:**
- `401 Unauthorized` - Sin token o token inválido
- `404 Not Found` - Artículo no existe

#### Listar Favoritos del Usuario
```bash
GET /api/favorites/
Authorization: Bearer {access_token}
```

**Respuesta:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "article": {
        "id": 2,
        "external_id": 34933,
        "title": "NASA safety panel recommends review of Artemis plans",
        "url": "https://spacenews.com/nasa-safety-panel-recommends-review...",
        "news_site": "SpaceNews",
        "sentiment_score": 0,
        "published_at": "2025-12-19T23:53:46Z"
      },
      "created_at": "2025-12-20T02:59:53.124156Z"
    }
  ]
}
```

**Seguridad:**
- Cada usuario solo ve SUS PROPIOS favoritos
- Filtrado en QuerySet: `filter(user=request.user)`
- Optimizado con `select_related('article')`

### Ejemplos Prácticos con curl

**1. Obtener Token JWT:**
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"admin\", \"password\": \"admin123\"}"
```

**2. Consultar Reportes Mensuales (público):**
```bash
curl http://127.0.0.1:8000/api/reports/monthly/
```

**3. Listar Favoritos (requiere token):**
```bash
curl http://127.0.0.1:8000/api/favorites/ \
  -H "Authorization: Bearer {tu_token_access}"
```

**4. Marcar Artículo como Favorito:**
```bash
curl -X POST http://127.0.0.1:8000/api/articles/1/favorite/ \
  -H "Authorization: Bearer {tu_token_access}"
```

**5. Verificar Duplicados:**
```bash
# Ejecutar el comando del paso 4 nuevamente
# Respuesta: {"message": "El artículo ya está en tus favoritos", "article_id": 1}
```

## 🛠️ Management Commands

### Sincronizar Noticias

Comando para sincronizar artículos desde Spaceflight News API v4.

```bash
# Sincronizar 100 artículos (default)
python manage.py sync_news

# Sincronizar cantidad específica
python manage.py sync_news --limit 50

# Ver ayuda
python manage.py sync_news --help
```

**Funcionalidad:**
1. Consulta la API: `https://api.spaceflightnewsapi.net/v4/articles/`
2. Busca artículos con keyword: `NASA`
3. **Filtra** artículos que contengan:
   - "spacex" (case-insensitive)
   - "musk" (case-insensitive)
4. **Calcula sentiment score:**
   - `1` si el título contiene "mars" o "moon"
   - `0` en cualquier otro caso
5. **Guarda/actualiza** usando `update_or_create()` (previene duplicados)

**Output de ejemplo:**
```
============================================================
SINCRONIZADOR DE NOTICIAS ESPACIALES
============================================================
Iniciando sincronización con límite de 50 artículos...

============================================================
RESULTADOS DE LA SINCRONIZACIÓN
============================================================
Total procesados:  50
[OK] Guardados:        49
[!]  Filtrados:        1 (contenido censurado)
[OK] Errores:          0

============================================================
¡Sincronización exitosa! Se guardaron 49 artículos.
```

## ⚠️ Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'pkg_resources'`

**Problema:** Al ejecutar `python manage.py migrate` obtienes este error.

**Causa:** Python 3.12+ no incluye `setuptools` por defecto en entornos virtuales.

**Solución:**
```bash
pip install setuptools
```

Este paquete ya está incluido en `requirements.txt`, pero si instalaste las dependencias antes de agregarlo, ejecútalo manualmente.

### Error con `psycopg2-binary` en Windows

**Problema:** Error de instalación de `psycopg2-binary`.

**Causa:** Este paquete solo es necesario para PostgreSQL en producción, no para desarrollo.

**Solución:** El proyecto ya NO incluye `psycopg2-binary` en `requirements.txt` para desarrollo. Si usas PostgreSQL en producción, instálalo manualmente:
```bash
pip install psycopg2-binary
```

### El servidor no inicia

**Problema:** `python manage.py runserver` falla.

**Verificaciones:**
1. Asegúrate de tener el entorno virtual activado
2. Verifica que las migraciones se ejecutaron: `python manage.py migrate`
3. Revisa que el archivo `.env` existe (cópialo desde `.env.example`)

### Los tests fallan

**Problema:** `python manage.py test` muestra errores.

**Verificaciones:**
1. Asegúrate de tener todas las dependencias: `pip install -r requirements.txt`
2. Ejecuta las migraciones: `python manage.py migrate`
3. Verifica que no haya cambios sin aplicar en los modelos

## 🧪 Testing

El proyecto incluye una suite completa de 13 tests que cubre:
- Tests de integración con mocking de API externa
- Tests de seguridad y aislamiento de usuarios
- Tests de lógica de negocio

### Ejecutar Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Tests específicos
python manage.py test apps.articles.tests.test_sync
python manage.py test apps.articles.tests.test_favorites

# Con mayor verbosidad
python manage.py test -v 2
```

### Cobertura de Tests

**Tests de Sincronización (test_sync.py):**
- `test_sync_filters_spacex_articles` - Mock de API externa, filtrado de censura
- `test_sync_calculates_sentiment_score` - Análisis de sentimiento
- `test_sync_handles_duplicates` - Prevención de duplicados
- `test_should_filter_spacex` - Detección de keyword
- `test_should_filter_musk` - Detección de keyword
- `test_calculate_sentiment_mars` - Sentiment = 1 para Mars
- `test_calculate_sentiment_moon` - Sentiment = 1 para Moon
- `test_calculate_sentiment_neutral` - Sentiment = 0 para otros

**Tests de Favoritos (test_favorites.py):**
- `test_user_can_only_see_own_favorites` - **CRÍTICO**: Aislamiento de usuarios
- `test_unauthenticated_cannot_access_favorites` - 401 sin auth
- `test_create_favorite_requires_authentication` - 401 al crear
- `test_create_favorite_with_invalid_article` - 404 no encontrado
- `test_duplicate_favorite_returns_200` - Manejo de duplicados

**Resultado esperado:**
```
Ran 13 tests in 3.681s

OK
```

## 🏗️ Arquitectura

### Service Layer Pattern

El proyecto implementa **Service Layer** para separar lógica de negocio:

```
Views (Presentación)
    ↓
Serializers (Validación/Serialización)
    ↓
Services (Lógica de Negocio)
    ↓
Models (Acceso a Datos)
```

**Ventajas:**
- Lógica de negocio reusable y testeable
- Views limpias y enfocadas en HTTP
- Fácil migración a otras interfaces (GraphQL, CLI, etc.)

### Estructura del Proyecto

```
Backend-Challenge-SpaceNews-Aggregator/
├── config/                          # Configuración de Django
│   ├── settings.py                  # Settings principal
│   ├── urls.py                      # URLs raíz
│   ├── wsgi.py                      # WSGI entry point
│   └── asgi.py                      # ASGI entry point
│
├── apps/
│   └── articles/                    # App principal
│       ├── models.py                # Article, Favorite
│       ├── views.py                 # MonthlyReportView, FavoriteListView, favorite_article
│       ├── serializers.py           # ArticleSerializer, FavoriteSerializer
│       ├── services.py              # NewsService (Service Layer)
│       ├── urls.py                  # URLs de la app
│       ├── admin.py                 # Django Admin config
│       ├── managers.py              # Custom QuerySet managers
│       │
│       ├── management/
│       │   └── commands/
│       │       └── sync_news.py     # Comando de sincronización
│       │
│       └── tests/
│           ├── test_sync.py         # Tests de sincronización
│           └── test_favorites.py    # Tests de favoritos
│
├── manage.py                        # Django CLI
├── requirements.txt                 # Dependencias
├── .env.example                     # Template de variables
├── .gitignore                       # Git ignore
└── README.md                        # Este archivo
```

## 🔐 Seguridad

### Autenticación JWT

- Tokens con expiración (1 hora para access, 1 día para refresh)
- Algoritmo HS256
- Refresh token rotation opcional

### Aislamiento de Usuarios

**CRÍTICO:** Los favoritos están aislados por usuario:

```python
# En FavoriteListView.get_queryset()
return Favorite.objects.filter(
    user=self.request.user  # ← Filtrado crítico
).select_related('article')
```

**Tests de seguridad confirman:**
- Usuario A no puede ver favoritos de Usuario B
- Sin autenticación = 401 Unauthorized
- Artículo inexistente = 404 Not Found

## 📊 Decisiones Técnicas

### 1. Service Layer vs Fat Models

**Decisión:** Service Layer en `services.py`

**Razones:**
- Lógica de negocio compleja (API externa, filtrado, sentiment)
- Fácilmente testeable con mocks
- Reusable desde management commands y views
- Modelos enfocados solo en datos

### 2. ORM Puro para Reportes

**Decisión:** Usar `annotate()`, `aggregate()`, `Subquery()` sin loops Python

**Razones:**
- Performance: cálculos en base de datos
- Escalabilidad: funciona con millones de registros
- Django best practices

**Ejemplo:**
```python
# ❌ MAL: Loop Python
for month in months:
    count = Article.objects.filter(published_at__month=month).count()

# ✅ BIEN: ORM puro
Article.objects.annotate(
    month=TruncMonth('published_at')
).values('month').annotate(total=Count('id'))
```

### 3. select_related() para Optimización

**Decisión:** Usar `select_related('article')` en favoritos

**Razones:**
- Previene N+1 queries
- 1 query SQL en lugar de N+1
- Mejor performance en listas

### 4. update_or_create() para Idempotencia

**Decisión:** Usar `update_or_create()` en sincronización

**Razones:**
- Previene duplicados automáticamente
- Actualiza artículos existentes
- Comando sync_news idempotente (ejecutable múltiples veces)

## 🚀 Deployment

### Variables de Entorno Requeridas

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@localhost:5432/spacenews
```

### Pasos para Producción

1. **Configurar PostgreSQL:**
```bash
# Instalar psycopg2-binary
pip install psycopg2-binary

# Actualizar .env con DATABASE_URL
```

2. **Configurar archivos estáticos:**
```bash
python manage.py collectstatic
```

3. **Ejecutar migraciones:**
```bash
python manage.py migrate
```

4. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

5. **Usar servidor WSGI (Gunicorn):**
```bash
pip install gunicorn
gunicorn config.wsgi:application
```

## 📝 Licencia

Este proyecto es parte de una prueba técnica de backend.

## 👨‍💻 Autor

Desarrollado como solución al SpaceNews Aggregator Backend Challenge.