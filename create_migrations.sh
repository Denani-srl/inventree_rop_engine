#!/bin/bash
# Script to create and apply migrations for the ROP plugin
# This needs to be run on the InvenTree server

set -e

echo "=========================================="
echo "  ROP Plugin Migration Script"
echo "=========================================="
echo ""

# Navigate to InvenTree directory
cd /opt/inventree/src/backend/InvenTree

# Activate virtual environment
source /opt/inventree/env/bin/activate

# Set Django settings module
export DJANGO_SETTINGS_MODULE=InvenTree.settings

# Add plugin to INSTALLED_APPS temporarily
python << 'PYEOF'
import os
import django
import sys

# Ensure settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')

# Import settings
from django.conf import settings

# Add our plugin to INSTALLED_APPS
if 'inventree_rop_engine' not in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = tuple(list(settings.INSTALLED_APPS) + ['inventree_rop_engine'])
    print("✓ Added inventree_rop_engine to INSTALLED_APPS")
else:
    print("✓ inventree_rop_engine already in INSTALLED_APPS")

# Setup Django
django.setup()
print("✓ Django setup complete")

# Import management commands
from django.core.management import call_command

# Create migrations
print("\n📝 Creating migrations...")
try:
    call_command('makemigrations', 'inventree_rop_engine', interactive=False, verbosity=2)
    print("✓ Migrations created successfully")
except Exception as e:
    print(f"✗ Error creating migrations: {e}")
    sys.exit(1)

# Apply migrations
print("\n🔧 Applying migrations...")
try:
    call_command('migrate', 'inventree_rop_engine', interactive=False, verbosity=2)
    print("✓ Migrations applied successfully")
except Exception as e:
    print(f"✗ Error applying migrations: {e}")
    sys.exit(1)

# Verify tables were created
print("\n✅ Verifying database tables...")
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE '%rop%' ORDER BY tablename")
    tables = cursor.fetchall()
    if tables:
        print("✓ Tables created:")
        for table in tables:
            print(f"  • {table[0]}")
    else:
        print("✗ No tables found")
        sys.exit(1)

print("\n" + "="*42)
print("  ✓ Migration completed successfully!")
print("="*42)
print("\nNext steps:")
print("  1. Restart InvenTree: sudo systemctl restart inventree")
print("  2. Uncomment model imports in api_views.py")
print("  3. Reinstall plugin: pip install -e .")
print("")

PYEOF

echo ""
echo "Script completed. Please restart InvenTree."
