#!/bin/bash
echo "🌊 استثمار مصيف بلطيم — Setup"
echo "================================"

# Install packages
echo "📦 Installing requirements..."
pip3 install -r requirements.txt -q

# Migrations
echo "🗃️  Running migrations..."
python3 manage.py migrate --run-syncdb -v 0

# Seed data
echo "🏖️  Seeding properties..."
python3 manage.py seed_properties

# Create superuser
echo ""
echo "👤 Create admin user:"
python3 manage.py createsuperuser

echo ""
echo "✅ Setup complete!"
echo "   Run: python3 manage.py runserver"
echo "   Open: http://localhost:8000"
