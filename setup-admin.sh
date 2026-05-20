#!/bin/bash

# Admin Panel Setup Script for Docker
# Run this script from the deploy/hetzner directory

echo "================================"
echo "Jones Shop Admin Panel Setup"
echo "================================"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HETZNER_DIR="$SCRIPT_DIR/deploy/hetzner"

# Check if docker-compose.yml exists
if [ ! -f "$HETZNER_DIR/docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found in $HETZNER_DIR"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Change to hetzner directory
cd "$HETZNER_DIR"

echo "[1/3] Ensuring Docker containers are running..."
docker compose up -d
if [ $? -ne 0 ]; then
    echo "Error: Failed to start Docker containers"
    exit 1
fi
echo "[1/3] ✓ Docker containers started"
echo ""

# Wait for database to be ready
echo "[2/3] Waiting for database to be ready..."
sleep 3

# Run migrations
docker compose exec -T api python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Warning: Migration command returned error"
fi
echo "[2/3] ✓ Database ready"
echo ""

# Create admin account
echo "[3/3] Creating default admin account..."
docker compose exec -T api python manage.py create_default_admin
if [ $? -ne 0 ]; then
    echo "Error: Failed to create admin account"
    exit 1
fi

echo ""
echo "================================"
echo "✓ Setup Complete!"
echo "================================"
echo ""

echo "Admin Panel URL:"
echo "  http://localhost:8000/admin/login/"
echo ""

echo "Credentials:"
echo "  Username: admin"
echo "  Password: t123"
echo ""

echo "Available Routes:"
echo "  Dashboard:  http://localhost:8000/admin/dashboard/"
echo "  Products:   http://localhost:8000/admin/products/"
echo "  Articles:   http://localhost:8000/admin/articles/"
echo ""

echo "Next Steps:"
echo "  1. Open your browser to http://localhost:8000/admin/login/"
echo "  2. Login with username: admin, password: t123"
echo "  3. Start managing your products and articles!"
