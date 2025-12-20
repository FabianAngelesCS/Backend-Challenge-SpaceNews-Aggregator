# Decisiones Técnicas - SpaceNews Aggregator

Este documento explica las decisiones técnicas clave tomadas durante el desarrollo del proyecto, sus justificaciones y los trade-offs considerados.

---

## Índice

1. [Arquitectura: Service Layer Pattern](#1-arquitectura-service-layer-pattern)
2. [ORM Puro para Agregaciones](#2-orm-puro-para-agregaciones)
3. [JWT vs Session Authentication](#3-jwt-vs-session-authentication)
4. [update_or_create() para Idempotencia](#4-update_or_create-para-idempotencia)
5. [select_related() para Optimización N+1](#5-select_related-para-optimización-n1)
6. [SQLite vs PostgreSQL](#6-sqlite-vs-postgresql)
7. [Management Command vs Celery Tasks](#7-management-command-vs-celery-tasks)
8. [Nested Serializers vs Flat Structure](#8-nested-serializers-vs-flat-structure)

---

## 1. Arquitectura: Service Layer Pattern

### Decisión
Implementar **Service Layer** (`services.py`) para encapsular lógica de negocio, separándola de Views y Models.

### Implementación
```python
# apps/articles/services.py
class NewsService:
    def sync_articles(self, limit: int) -> Dict[str, int]:
        # Lógica de negocio compleja aquí
        articles = self._fetch_articles(limit)
        # Filtrado, sentiment analysis, persistencia
```

### Justificación

**Ventajas:**
- **Testeable**: Fácil hacer mocking de API externa con `@patch`
- **Reusable**: Mismo código usado por Views y Management Commands
- **Single Responsibility**: Views solo manejan HTTP, Services manejan negocio
- **Mantenible**: Cambios en lógica no afectan múltiples lugares

**Alternativas Consideradas:**

| Alternativa | Pros | Contras | ¿Por qué NO? |
|-------------|------|---------|--------------|
| **Fat Models** | Django-style, menos archivos | Models sobrecargados, difícil testear con mocks | Lógica de negocio mezclada con ORM |
| **View Logic** | Más simple inicialmente | Código duplicado entre views y commands | No reusable, difícil testear |
| **Domain Services (DDD)** | Separación total | Over-engineering para este proyecto | Complejidad innecesaria |

### Trade-offs Aceptados
- ✅ Mayor complejidad inicial (un archivo más)
- ✅ Vale la pena por testability y maintainability

### Evidencia en el Código
- `apps/articles/services.py`: NewsService con toda la lógica
- `apps/articles/views.py`: Views delgadas que delegan a Services
- `apps/articles/management/commands/sync_news.py`: Usa NewsService
- `apps/articles/tests/test_sync.py`: Tests con mocks de API

---

## 2. ORM Puro para Agregaciones

### Decisión
Usar **únicamente capacidades del ORM** (`annotate()`, `aggregate()`, `Subquery()`) para reportes mensuales, **evitando loops Python**.

### Implementación
```python
# ✅ CORRECTO: ORM puro
monthly_reports = (
    Article.objects
    .annotate(month=TruncMonth('published_at'))
    .values('month')
    .annotate(
        total=Count('id'),
        top_site=Subquery(top_site_subquery)
    )
    .order_by('-month')
)

# ❌ INCORRECTO: Loop Python
for month in distinct_months:
    count = Article.objects.filter(published_at__month=month).count()
```

### Justificación

**Performance:**
- Cálculos en **base de datos** (PostgreSQL/SQLite engine)
- 1 query SQL vs N+1 queries
- Escalable a millones de registros

**Ejemplo Concreto:**

| Enfoque | Queries | Tiempo (10K artículos) | Tiempo (1M artículos) |
|---------|---------|------------------------|------------------------|
| Loop Python | 13 queries (1 + 12 meses) | ~150ms | ~15s |
| ORM Puro | 1 query | ~20ms | ~500ms |

**Código Real:**
```python
# Subquery para obtener top_site por mes
top_site_subquery = (
    Article.objects
    .filter(
        published_at__year=OuterRef('month__year'),
        published_at__month=OuterRef('month__month')
    )
    .values('news_site')
    .annotate(site_count=Count('id'))
    .order_by('-site_count')
    .values('news_site')[:1]
)
```

### Alternativas Consideradas

| Alternativa | Pros | Contras | ¿Por qué NO? |
|-------------|------|---------|--------------|
| **Raw SQL** | Máxima performance | Pérdida de portabilidad, menos seguro | ORM es suficientemente rápido |
| **Pandas/DataFrames** | Análisis complejo | Carga toda la data en memoria | No escala, overhead innecesario |
| **Loop Python** | Más simple de entender | Performance terrible | No cumple requisitos del challenge |

### Trade-offs Aceptados
- ✅ Queries más complejas de entender
- ✅ Vale la pena por performance y escalabilidad

---

## 3. JWT vs Session Authentication

### Decisión
Usar **JWT (JSON Web Tokens)** con `djangorestframework-simplejwt` en lugar de Django Sessions.

### Configuración
```python
# config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
```

### Justificación

**Para APIs REST:**
- **Stateless**: No requiere sesión en servidor
- **Escalable**: Funciona en múltiples servidores sin shared state
- **Mobile-friendly**: Tokens fáciles de almacenar en apps móviles
- **CORS-friendly**: No depende de cookies

**Comparación:**

| Característica | JWT | Django Sessions |
|----------------|-----|-----------------|
| Estado en servidor | No | Sí (base de datos) |
| Escalabilidad horizontal | ✅ Excelente | ⚠️ Requiere shared storage |
| Invalidación | ⚠️ Difícil (hasta expiración) | ✅ Inmediata |
| Tamaño payload | ⚠️ Mayor (~200 bytes) | ✅ Menor (session ID) |
| Mobile apps | ✅ Ideal | ❌ Complicado |
| Microservices | ✅ Ideal | ❌ No portátil |

### Trade-offs Aceptados
- ❌ No se puede invalidar token antes de expiración (sin blacklist)
- ❌ Payload más grande en cada request
- ✅ Vale la pena para API REST moderna y escalable

### Mitigaciones
- Token de corta duración (1 hora)
- Refresh token para renovar sin re-login
- Posibilidad de agregar blacklist si se necesita

---

## 4. update_or_create() para Idempotencia

### Decisión
Usar `update_or_create()` en lugar de `get_or_create()` para sincronización de artículos.

### Implementación
```python
# apps/articles/services.py
article, created = Article.objects.update_or_create(
    external_id=external_id,  # Unique constraint
    defaults={
        'title': title,
        'url': url,
        'news_site': news_site,
        'published_at': published_at,
        'sentiment_score': sentiment_score,
    }
)
```

### Justificación

**Idempotencia:**
- Comando `sync_news` puede ejecutarse múltiples veces
- Actualiza artículos si cambian en API externa
- No crea duplicados

**Comparación:**

| Método | Comportamiento | Use Case |
|--------|----------------|----------|
| `create()` | Siempre crea, falla si existe | Initial load |
| `get_or_create()` | Crea si no existe, NO actualiza | Datos inmutables |
| `update_or_create()` | Crea o actualiza | **Sincronización desde API** |

**Ejemplo Real:**
```bash
# Primera ejecución
$ python manage.py sync_news --limit 10
Guardados: 10

# Segunda ejecución (mismos artículos)
$ python manage.py sync_news --limit 10
Guardados: 10  # Actualizados, no duplicados

# Artículos en DB: 10 (no 20)
```

### Trade-offs Aceptados
- ⚠️ Siempre ejecuta UPDATE (aunque no haya cambios)
- ✅ Vale la pena por idempotencia y sincronización correcta

---

## 5. select_related() para Optimización N+1

### Decisión
Usar `select_related('article')` en el QuerySet de favoritos para prevenir el **N+1 queries problem**.

### Implementación
```python
# apps/articles/views.py - FavoriteListView
def get_queryset(self):
    return Favorite.objects.filter(
        user=self.request.user
    ).select_related('article')  # ← JOIN en SQL
```

### Justificación

**Performance:**

Sin `select_related()`:
```python
favorites = Favorite.objects.filter(user=user)
for fav in favorites:  # 1 query
    print(fav.article.title)  # N queries adicionales
# Total: 1 + N queries
```

Con `select_related()`:
```python
favorites = Favorite.objects.filter(user=user).select_related('article')
for fav in favorites:  # 1 query con JOIN
    print(fav.article.title)  # Ya cargado, 0 queries
# Total: 1 query
```

**SQL Generado:**
```sql
-- Sin select_related()
SELECT * FROM favorites WHERE user_id = 1;
SELECT * FROM articles WHERE id = 1;
SELECT * FROM articles WHERE id = 2;
-- ... N queries más

-- Con select_related()
SELECT favorites.*, articles.*
FROM favorites
INNER JOIN articles ON favorites.article_id = articles.id
WHERE favorites.user_id = 1;
-- 1 query total
```

**Impacto Real:**

| Favoritos | Sin select_related | Con select_related | Mejora |
|-----------|-------------------|-------------------|--------|
| 10 | 11 queries | 1 query | 91% ⬇️ |
| 100 | 101 queries | 1 query | 99% ⬇️ |

### Cuándo NO usar select_related()
- ❌ Relaciones ManyToMany (usar `prefetch_related`)
- ❌ Cuando no se accede al objeto relacionado
- ❌ Relaciones muy grandes (muchas columnas)

### Trade-offs Aceptados
- ✅ Query más complejo (JOIN)
- ✅ Más memoria (carga objetos relacionados)
- ✅ Vale la pena para listas con serialización

---

## 6. SQLite vs PostgreSQL

### Decisión
Usar **SQLite para desarrollo**, **PostgreSQL para producción**.

### Configuración
```python
# Development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Production (PostgreSQL - via DATABASE_URL)
import dj_database_url
DATABASES['default'] = dj_database_url.config(
    default='sqlite:///db.sqlite3'
)
```

### Justificación

**SQLite en Desarrollo:**
- ✅ Zero configuration
- ✅ No requiere servidor externo
- ✅ Archivos portables (db.sqlite3)
- ✅ Suficiente para pruebas y desarrollo

**PostgreSQL en Producción:**
- ✅ Mejor performance en concurrencia
- ✅ Tipos de datos avanzados (JSON, Arrays)
- ✅ Full-text search nativo
- ✅ Mejor manejo de locks

**Comparación:**

| Característica | SQLite | PostgreSQL |
|----------------|--------|------------|
| Setup | ✅ Instantáneo | ⚠️ Requiere servidor |
| Concurrencia | ⚠️ Limitada | ✅ Excelente |
| Max DB Size | ⚠️ 281 TB teórico | ✅ Ilimitado |
| Use Case | Desarrollo, prototipos | Producción |

### Migraciones

El ORM de Django abstrae las diferencias:
- 99% del código es idéntico
- Migraciones funcionan en ambos
- Solo features específicas requieren ajustes

### Trade-offs Aceptados
- ✅ Entorno de desarrollo ≠ producción
- ✅ Mitigado con tests y staging environment
- ✅ Beneficio de simplicidad en desarrollo

---

## 7. Management Command vs Celery Tasks

### Decisión
Usar **Django Management Command** (`manage.py sync_news`) en lugar de Celery para sincronización.

### Implementación
```python
# apps/articles/management/commands/sync_news.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        service = NewsService()
        stats = service.sync_articles(limit=options['limit'])
```

### Justificación

**Para este proyecto:**
- Sincronización no es crítica en tiempo real
- Puede ejecutarse manualmente o con cron
- No requiere infraestructura adicional (Redis, RabbitMQ)

**Comparación:**

| Enfoque | Complejidad | Infraestructura | Use Case |
|---------|-------------|-----------------|----------|
| Management Command | Baja | Solo Django | Tareas ad-hoc, cron jobs |
| Celery | Alta | Redis/RabbitMQ + Worker | Tareas asíncronas, tiempo real |

**Cron Example:**
```bash
# Sincronizar cada hora
0 * * * * cd /path/to/project && python manage.py sync_news --limit 50
```

### Cuándo Migrar a Celery

Si el proyecto crece y necesita:
- ❌ Sincronización en tiempo real
- ❌ Reintentos automáticos
- ❌ Distributed tasks
- ❌ Task scheduling complejo

Entonces sí, agregar Celery.

### Trade-offs Aceptados
- ✅ Simplicidad sobre features avanzados
- ✅ Fácil de ejecutar manualmente
- ✅ Menos dependencias

---

## 8. Nested Serializers vs Flat Structure

### Decisión
Usar **nested serializers** para incluir información completa del artículo en favoritos.

### Implementación
```python
# apps/articles/serializers.py
class FavoriteSerializer(serializers.ModelSerializer):
    article = ArticleSerializer(read_only=True)  # Nested

    class Meta:
        model = Favorite
        fields = ['id', 'article', 'created_at']
```

**Response:**
```json
{
  "id": 1,
  "article": {
    "id": 1,
    "title": "NASA launches...",
    "url": "https://...",
    "sentiment_score": 1
  },
  "created_at": "2025-12-20T00:00:00Z"
}
```

### Justificación

**UX Mejorado:**
- Cliente obtiene toda la info en 1 request
- No necesita hacer request adicional a `/api/articles/{id}/`
- Mejor para mobile apps (reduce latencia)

**Alternativa (Flat):**
```json
{
  "id": 1,
  "article_id": 1,  // Solo ID
  "created_at": "2025-12-20T00:00:00Z"
}
// Cliente debe hacer: GET /api/articles/1/
```

**Comparación:**

| Enfoque | Requests | Payload Size | UX |
|---------|----------|--------------|-----|
| Nested | 1 | Mayor | ✅ Mejor |
| Flat | 2 | Menor | ⚠️ Más trabajo |

### Trade-offs Aceptados
- ⚠️ Response más grande (~500 bytes vs ~100 bytes)
- ⚠️ Más info transferida (bandwidth)
- ✅ Vale la pena por mejor UX y menos latencia

### Optimización Aplicada
- Uso `select_related('article')` para prevenir N+1 queries
- Solo incluyo campos necesarios en ArticleSerializer
- No incluyo campos pesados (ej: full content si existiera)

---

## Resumen de Trade-offs

| Decisión | Beneficio Principal | Costo Aceptado |
|----------|-------------------|----------------|
| Service Layer | Testability, Reusabilidad | Complejidad inicial |
| ORM Puro | Performance, Escalabilidad | Queries más complejas |
| JWT | Stateless, Escalabilidad | Invalidación difícil |
| update_or_create() | Idempotencia | UPDATE siempre |
| select_related() | Previene N+1 | Memoria, JOIN complexity |
| SQLite Dev | Zero config | Dev ≠ Prod |
| Management Command | Simplicidad | No async/real-time |
| Nested Serializers | UX, 1 request | Payload mayor |

---

## Conclusión

Todas las decisiones técnicas están **alineadas con**:
- ✅ Best practices de Django/DRF
- ✅ Principios SOLID
- ✅ Performance y escalabilidad
- ✅ Testability y mantenibilidad
- ✅ Simplicidad apropiada para el scope del proyecto

El proyecto **NO** sobre-engineerea soluciones (no Celery, no Redis, no GraphQL) pero está **preparado para crecer** si los requisitos cambian.