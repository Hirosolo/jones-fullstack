# Pezure Django Backend

A robust Django REST API backend for the Pezure e-commerce platform, providing comprehensive backend services for print-on-demand product management, user authentication, and order processing.

## Overview

This Django application serves as the backend API for Pezure, handling all server-side operations including product catalog management, user authentication, order processing, and content management through a RESTful API architecture.

## Technology Stack

- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Cache**: DragonFly DB / Redis
- **Task Queue**: Celery with RabbitMQ
- **Authentication**: JWT-based authentication
- **Media Storage**: Cloud storage integration
- **Environment**: Python 3.9+

## Project Structure

```
pezure-django/
├── articles/              # Blog and content management
├── myshop/               # Product catalog and e-commerce logic
├── profiles/             # User management and authentication
├── utils/                # Shared utilities and helpers
├── pezureTrendingMall/   # Main Django project configuration
├── media/                # Media files storage
├── static/               # Static files
├── templates/            # HTML templates
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── .env.example         # Environment variables template
```

## Core Applications

### myshop
- Product catalog management
- Category and subcategory handling
- Shopping cart functionality
- Order processing
- Payment integration
- Inventory management

### profiles
- User registration and authentication
- Profile management
- JWT token handling
- User permissions and roles

### articles
- Content management system
- Blog functionality
- SEO content management
- Dynamic page content

### utils
- Shared utilities
- Common decorators
- Helper functions
- API utilities

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- PostgreSQL database
- Redis/DragonFly DB
- Virtual environment tool

### Local Development Setup

1. **Clone and navigate to backend directory**
```bash
cd pezure-django
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

## Environment Configuration

Create a `.env` file with the following variables:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pezure_db

# URLs
SITE_URL=http://localhost:3000
DJANGO_BASE_URL=http://localhost:8000

# Cache
CACHE_URL=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Media Storage
MEDIA_URL=/media/
MEDIA_ROOT=media/

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Token refresh
- `POST /api/auth/logout/` - User logout

### Products
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Product details
- `GET /api/categories/` - Product categories
- `GET /api/categories/{slug}/` - Category products

### User Profile
- `GET /api/profile/` - User profile
- `PUT /api/profile/` - Update profile
- `GET /api/orders/` - User orders
- `POST /api/orders/` - Create order

### Content
- `GET /api/articles/` - Blog articles
- `GET /api/articles/{slug}/` - Article details

## Database Models

### Key Models
- **Product**: Product information, pricing, inventory
- **Category**: Product categorization
- **User**: Extended user model with profile information
- **Order**: Order management and tracking
- **Article**: Content management for blog/pages

## Development Commands

### Database Operations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py flush  # Reset database
```

### Data Management
```bash
python manage.py loaddata fixtures/initial_data.json
python manage.py dumpdata app.model > fixtures/data.json
```

### Testing
```bash
python manage.py test
python manage.py test myshop.tests
```

### Static Files
```bash
python manage.py collectstatic
```

## Deployment

### Production Settings
1. Set `DEBUG=False` in environment
2. Configure proper `ALLOWED_HOSTS`
3. Set up production database
4. Configure static file serving
5. Set up proper logging

### WSGI Deployment
```bash
gunicorn pezureTrendingMall.wsgi:application --bind 0.0.0.0:8000
```

## API Documentation

Access the browsable API documentation at:
- Development: `http://localhost:8000/api/`
- Admin Interface: `http://localhost:8000/admin/`

## Security Features

- CSRF protection
- JWT authentication
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting capabilities

## Performance Optimization

- Database query optimization
- Caching with Redis/DragonFly
- Pagination for large datasets
- Optimized database indexes
- Background task processing with Celery

## Troubleshooting

### Common Issues
1. **Database connection errors**: Check DATABASE_URL configuration
2. **Migration issues**: Run `python manage.py showmigrations`
3. **Static files not loading**: Run `python manage.py collectstatic`
4. **Permission errors**: Check file permissions and user roles

### Logging
Logs are configured in `settings.py` and can be found in the console output during development.