#!/usr/bin/env python
"""
Script to create test ROP data for verification.
Run this on the InvenTree server to create sample suggestions.

Usage:
  cd /opt/inventree/src/backend/InvenTree
  source /opt/inventree/env/bin/activate
  python /path/to/create_test_data.py
"""

import os
import sys
import django

# Add InvenTree to Python path if not already there
inventree_path = '/opt/inventree/src/backend/InvenTree'
if inventree_path not in sys.path:
    sys.path.insert(0, inventree_path)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
django.setup()

from inventree_rop_engine.models import ROPPolicy, ROPSuggestion, DemandStatistics
from part.models import Part
from company.models import Company
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

def create_test_data():
    """Create test ROP policy and suggestion."""

    print("="*60)
    print("  Creating Test ROP Data")
    print("="*60)
    print()

    # Get the first part
    part = Part.objects.first()
    if not part:
        print('❌ No parts found in database.')
        print('   Please create a part in InvenTree first.')
        return False

    print(f'✓ Using part: {part.name} (ID: {part.pk})')
    if part.IPN:
        print(f'  IPN: {part.IPN}')
    print()

    # Create or get ROP policy
    policy, policy_created = ROPPolicy.objects.get_or_create(
        part=part,
        defaults={
            'enabled': True,
            'safety_stock': Decimal('10.00'),
            'service_level': 95,
            'target_stock_multiplier': Decimal('2.00'),
            'last_calculated_rop': Decimal('15.00'),
            'last_calculated_demand_rate': Decimal('2.50'),
            'last_calculation_date': timezone.now(),
        }
    )

    if policy_created:
        print('✓ ROP Policy created')
    else:
        print('✓ ROP Policy already exists')

    print(f'  - Safety Stock: {policy.safety_stock}')
    print(f'  - Service Level: {policy.service_level}%')
    print(f'  - Enabled: {policy.enabled}')
    print()

    # Create a test suggestion
    suggestion, suggestion_created = ROPSuggestion.objects.get_or_create(
        rop_policy=policy,
        status='PENDING',
        defaults={
            'current_stock': Decimal('5.00'),
            'projected_stock': Decimal('3.00'),
            'calculated_rop': Decimal('15.00'),
            'suggested_order_qty': Decimal('20.00'),
            'urgency_score': Decimal('85.50'),
            'days_until_stockout': 3,
            'stockout_date': timezone.now() + timedelta(days=3),
            'lead_time_days': 7,
        }
    )

    if suggestion_created:
        print('✓ ROP Suggestion created')
    else:
        print('✓ ROP Suggestion already exists')

    print(f'  - ID: {suggestion.id}')
    print(f'  - Urgency Score: {suggestion.urgency_score}')
    print(f'  - Current Stock: {suggestion.current_stock}')
    print(f'  - Suggested Order: {suggestion.suggested_order_qty}')
    print(f'  - Days Until Stockout: {suggestion.days_until_stockout}')
    print()

    # Create demand statistics
    stats, stats_created = DemandStatistics.objects.get_or_create(
        rop_policy=policy,
        calculation_date=timezone.now(),
        defaults={
            'mean_daily_demand': Decimal('2.50'),
            'std_dev_daily_demand': Decimal('0.75'),
            'total_removals': 225,
            'analysis_period_days': 90,
            'calculated_safety_stock': Decimal('8.50'),
        }
    )

    if stats_created:
        print('✓ Demand Statistics created')
    else:
        print('✓ Demand Statistics already exists')

    print(f'  - Mean Daily Demand: {stats.mean_daily_demand}')
    print(f'  - Std Dev: {stats.std_dev_daily_demand}')
    print(f'  - Analysis Period: {stats.analysis_period_days} days')
    print()

    print("="*60)
    print("  Test Data Created Successfully!")
    print("="*60)
    print()
    print("Next steps:")
    print("  1. Refresh your InvenTree dashboard (Ctrl+F5)")
    print("  2. Check the 'Urgent Reorder Suggestions' widget")
    print(f"  3. Navigate to part detail page for '{part.name}'")
    print("  4. Look for the 'ROP Analysis' panel")
    print()
    print("To verify via API:")
    print("  curl http://localhost/plugin/inventree-rop-engine/suggestions/")
    print()

    return True

if __name__ == '__main__':
    try:
        success = create_test_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
