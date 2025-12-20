# SpaceNews Aggregator - Backend Challenge

API REST para agregar y gestionar noticias espaciales desde Spaceflight News API v4.

## Stack Tecnológico

- **Django 4.2.7**
- **Django REST Framework 3.14.0**
- **JWT Authentication (simplejwt)**
- **PostgreSQL / SQLite**
- **Python 3.9+**

## Características Principales

- Sincronización de noticias espaciales desde API externa
- Filtrado de contenido
- Análisis de sentimientos
- Sistema de favoritos por usuario
- Autenticación JWT
- Reportes y agregaciones ORM

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd Backend-Challenge-SpaceNews-Aggregator
```

### 2. Crear y activar entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
# Asegúrate de tener el venv activado
pip install -r requirements.txt
```

**Nota para usuarios de Windows/SQLite:**

Si obtienes un error con `psycopg2-binary`, puedes omitirlo ya que este proyecto usa SQLite por defecto:

```bash
# Instalar sin PostgreSQL
pip install Django==4.2.7 djangorestframework==3.14.0 djangorestframework-simplejwt==5.3.0 requests==2.31.0 python-decouple==3.8
```

El paquete `psycopg2-binary` solo es necesario si planeas usar PostgreSQL en producción.

### 4. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Iniciar servidor de desarrollo

```bash
# Opción 1: Usar script de conveniencia (Puerto 8500)
python run.py

# Opción 2: Usar archivo batch en Windows (Puerto 8500)
run.bat

# Opción 3: Comando manual
python manage.py runserver 8500
```

El servidor estará disponible en `http://localhost:8500`

## Estructura del Proyecto

```
spacenews/
├── config/                    # Configuración principal de Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── articles/              # App principal
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── services.py        # Service Layer (lógica de negocio)
│       ├── managers.py
│       ├── management/
│       │   └── commands/      # Management commands
│       └── tests/
├── manage.py
├── requirements.txt
└── .env.example
```

## Autenticación

El proyecto usa JWT para autenticación. Para obtener tokens:

```bash
# Obtener token
POST /api/token/
{
    "username": "your_username",
    "password": "your_password"
}

# Refrescar token
POST /api/token/refresh/
{
    "refresh": "your_refresh_token"
}
```

## API Endpoints

**Base URL:** `http://localhost:8500`

Los endpoints estarán disponibles en `/api/`

**Autenticación JWT:**
- `POST /api/token/` - Obtener access y refresh token
- `POST /api/token/refresh/` - Refrescar access token

**Admin:**
- `GET /admin/` - Panel de administración Django

## Desarrollo

Este proyecto sigue principios de Clean Architecture con Service Layer para separar la lógica de negocio.

## Testing

```bash
python manage.py test
```

## Licencia

Este proyecto es parte de una prueba técnica.
