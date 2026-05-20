# Admin Panel Setup Guide - Docker

## Quick Setup

Run this command from the `deploy/hetzner` directory to create the default admin account:

```bash
docker compose exec -T api python manage.py create_default_admin
```

## Admin Credentials
- **URL**: http://localhost:8000/admin/login/
- **Username**: `admin`
- **Password**: `t123`

## What This Does
✓ Creates a superuser account with full admin access
✓ Sets up the Django admin panel at `/admin/`
✓ Enables full CRUD for products and articles

## Features Available
- **Dashboard**: `/admin/dashboard/` - View statistics
- **Products**: `/admin/products/` - Manage all products (Create, Read, Update, Delete)
- **Articles**: `/admin/articles/` - Manage all articles (Create, Read, Update, Delete)

## Testing the Admin Panel

### 1. Start Backend in Docker
```bash
cd deploy/hetzner
docker compose up -d
```

### 2. Create Admin Account
```bash
docker compose exec -T api python manage.py create_default_admin
```

### 3. Access Admin Panel
- Open browser: http://localhost:8000/admin/login/
- Login with `admin` / `t123`
- Start managing products and articles!

## Testing API Endpoints (Optional)

If you want to test the REST API with the admin account:

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"t123"}'

# Response:
# {"access":"<token>","refresh":"<token>"}

# Use token to access API
curl -X GET http://localhost:8000/api/products/ \
  -H "Authorization: Bearer <token>"
```

## Troubleshooting

### Command not found
- Make sure you're in the `deploy/hetzner` directory
- Check that `utils` app is in `INSTALLED_APPS` in settings.py

### "No such file" error
- Verify Docker containers are running: `docker compose ps`
- If not running: `docker compose up -d`

### Database issues
- Run migrations first: `docker compose exec -T api python manage.py migrate`
- Then create admin account

## Notes
- Only 1 admin account exists (no staff accounts)
- Admin has full superuser permissions
- All CRUD operations require admin login
- Backend uses Django session authentication
