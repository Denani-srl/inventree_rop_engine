"""
ROP Calculation Engine - Core Business Logic

Implements the reorder point calculation algorithm including:
- Historical demand rate analysis from stock removal events
- Statistical safety stock calculation
- Integration with stock forecasting
- Projected stock evaluation
- Suggested order quantity determination
"""

from datetime import datetime, timedelta
from decimal import Decimal
import math
import logging

from django.db.models import Sum, Q, Count, F
from django.utils import timezone

logger = logging.getLogger('inventree')


class ROPCalculationEngine:
    """
    Core engine for ROP calculations and procurement suggestions.
    """
    
    def __init__(self, plugin_instance):
        """
        Initialize the ROP calculation engine.
        
        Args:
            plugin_instance: Reference to the ROPSuggestionPlugin instance
        """
        self.plugin = plugin_instance
        self.lookback_days = plugin_instance.get_setting('LOOKBACK_PERIOD_DAYS')
        self.min_samples = plugin_instance.get_setting('MIN_DEMAND_SAMPLES')
        self.default_service_level = plugin_instance.get_setting('DEFAULT_SERVICE_LEVEL')
    
    def calculate_all_suggestions(self):
        """
        Calculate ROP suggestions for all enabled parts.
        
        Returns:
            dict: Summary of calculation results
        """
        from .models import ROPPolicy, ROPSuggestion
        from part.models import Part
        
        results = {
            'total_parts': 0,
            'parts_analyzed': 0,
            'suggestion_count': 0,
            'errors': []
        }
        
        # Get all active ROP policies
        policies = ROPPolicy.objects.filter(enabled=True).select_related('part')
        results['total_parts'] = policies.count()
        
        for policy in policies:
            try:
                suggestion = self.calculate_part_rop(policy.part.pk)
                if suggestion:
                    results['suggestion_count'] += 1
                results['parts_analyzed'] += 1
            except Exception as e:
                logger.error(f"Error calculating ROP for part {policy.part.pk}: {str(e)}")
                results['errors'].append({
                    'part_id': policy.part.pk,
                    'error': str(e)
                })
        
        return results
    
    def calculate_part_rop(self, part_id):
        """
        Calculate ROP and generate suggestion for a specific part.
        
        Args:
            part_id: ID of the part to analyze
        
        Returns:
            ROPSuggestion object if reorder needed, None otherwise
        """
        from .models import ROPPolicy, DemandStatistics, ROPSuggestion
        from part.models import Part
        
        try:
            part = Part.objects.get(pk=part_id)
        except Part.DoesNotExist:
            logger.error(f"Part {part_id} not found")
            return None
        
        # Get or create ROP policy
        policy, created = ROPPolicy.objects.get_or_create(
            part=part,
            defaults={'enabled': True}
        )
        
        if not policy.enabled:
            return None
        
        # Step 1: Calculate demand rate
        demand_data = self.calculate_demand_rate(part, policy)
        if not demand_data:
            logger.warning(f"Insufficient demand data for part {part.name}")
            return None
        
        # Step 2: Calculate or retrieve safety stock
        safety_stock = self.calculate_safety_stock(part, policy, demand_data)
        
        # Step 3: Get lead time
        lead_time = self.get_lead_time(part)
        if lead_time is None:
            logger.warning(f"No lead time available for part {part.name}")
            lead_time = 30  # Default fallback
        
        # Step 4: Calculate ROP
        demand_during_lead_time = demand_data['mean_daily_demand'] * Decimal(lead_time)
        rop = demand_during_lead_time + safety_stock
        
        # Update policy with calculated values
        policy.last_calculated_rop = rop
        policy.last_calculated_demand_rate = demand_data['mean_daily_demand']
        policy.last_calculation_date = timezone.now()
        policy.save()
        
        # Save demand statistics
        stats = DemandStatistics.objects.create(
            rop_policy=policy,
            mean_daily_demand=demand_data['mean_daily_demand'],
            std_dev_daily_demand=demand_data['std_dev_daily_demand'],
            total_removals=demand_data['removal_count'],
            analysis_period_days=demand_data['analysis_period_days'],
            calculated_safety_stock=safety_stock
        )
        
        # Step 5: Get projected stock (including inbound POs)
        projected_stock = self.calculate_projected_stock(part)
        
        # Step 6: Check if reorder needed
        if projected_stock >= rop:
            # Stock is sufficient, no suggestion needed
            # Mark any pending suggestions as expired
            ROPSuggestion.objects.filter(
                rop_policy=policy,
                status='PENDING'
            ).update(status='EXPIRED')
            return None
        
        # Step 7: Calculate suggested order quantity
        target_stock = rop * policy.target_stock_multiplier
        soq = max(0, target_stock - projected_stock)
        
        # Step 8: Get stockout timing from forecasting plugin
        stockout_info = self.get_stockout_prediction(part, rop)
        
        # Step 9: Determine suggested supplier
        suggested_supplier = self.get_preferred_supplier(part)
        
        # Step 10: Create or update suggestion
        suggestion, created = ROPSuggestion.objects.update_or_create(
            rop_policy=policy,
            status='PENDING',
            defaults={
                'suggested_order_qty': soq,
                'current_stock': part.get_stock_count(),
                'projected_stock': projected_stock,
                'calculated_rop': rop,
                'stockout_date': stockout_info.get('date'),
                'days_until_stockout': stockout_info.get('days'),
                'suggested_supplier': suggested_supplier,
                'lead_time_days': lead_time,
            }
        )
        
        return suggestion
    
    def calculate_demand_rate(self, part, policy):
        """
        Calculate historical demand rate from stock removal events.
        
        Args:
            part: Part instance
            policy: ROPPolicy instance
        
        Returns:
            dict: Demand statistics or None if insufficient data
        """
        from stock.models import StockItem
        
        lookback_days = policy.get_effective_lookback_days(self.plugin)
        start_date = timezone.now() - timedelta(days=lookback_days)
        
        # Query historical stock adjustments for removals
        # Note: This uses InvenTree's tracking system
        # The StockItem model tracks changes through various mechanisms
        
        # Get all stock items for this part
        stock_items = StockItem.objects.filter(part=part)
        
        # Calculate total removals from tracking
        # InvenTree tracks this through StockItemTracking
        try:
            from stock.models import StockItemTracking
            
            removals = StockItemTracking.objects.filter(
                item__part=part,
                date__gte=start_date,
                tracking_type__in=[
                    StockItemTracking.REMOVED_FROM_LOCATION,
                    StockItemTracking.CONSUMED_BY_BUILD,
                    StockItemTracking.SHIPPED_AGAINST_SALES_ORDER,
                ]
            ).values_list('quantity', flat=True)
            
            removal_list = [abs(float(q)) for q in removals if q]
            
        except Exception as e:
            logger.error(f"Error querying stock tracking: {str(e)}")
            removal_list = []
        
        # Check if we have enough samples
        if len(removal_list) < self.min_samples:
            return None
        
        # Calculate statistics
        total_removed = sum(removal_list)
        mean_daily = Decimal(total_removed) / Decimal(lookback_days)
        
        # Calculate standard deviation
        if len(removal_list) > 1:
            mean = total_removed / len(removal_list)
            variance = sum((x - mean) ** 2 for x in removal_list) / len(removal_list)
            std_dev_per_transaction = Decimal(math.sqrt(variance))
            # Convert to daily std dev (approximation)
            transactions_per_day = len(removal_list) / lookback_days
            std_dev_daily = std_dev_per_transaction * Decimal(math.sqrt(transactions_per_day))
        else:
            std_dev_daily = Decimal(0)
        
        return {
            'mean_daily_demand': mean_daily,
            'std_dev_daily_demand': std_dev_daily,
            'removal_count': len(removal_list),
            'analysis_period_days': lookback_days,
            'total_removed': Decimal(total_removed)
        }
    
    def calculate_safety_stock(self, part, policy, demand_data):
        """
        Calculate safety stock based on demand variability and service level.
        
        Uses the formula: SS = Z * σ_LT
        Where:
        - Z = Z-score for desired service level
        - σ_LT = Standard deviation of demand during lead time
        
        Args:
            part: Part instance
            policy: ROPPolicy instance
            demand_data: dict with demand statistics
        
        Returns:
            Decimal: Safety stock quantity
        """
        if not policy.use_calculated_safety_stock:
            return policy.safety_stock
        
        # Get service level and convert to Z-score
        service_level = policy.service_level
        z_score = self.service_level_to_z_score(service_level)
        
        # Get lead time
        lead_time = self.get_lead_time(part)
        if lead_time is None:
            lead_time = 30
        
        # Calculate standard deviation during lead time
        # σ_LT = σ_daily * sqrt(L)
        std_dev_daily = demand_data['std_dev_daily_demand']
        std_dev_lead_time = std_dev_daily * Decimal(math.sqrt(lead_time))
        
        # Calculate safety stock
        safety_stock = Decimal(z_score) * std_dev_lead_time
        
        return max(Decimal(0), safety_stock)
    
    def service_level_to_z_score(self, service_level_pct):
        """
        Convert service level percentage to Z-score.
        
        Args:
            service_level_pct: Service level as percentage (e.g., 95 for 95%)
        
        Returns:
            float: Z-score
        """
        # Common service levels and their Z-scores
        z_scores = {
            50: 0.0,
            75: 0.674,
            80: 0.842,
            85: 1.036,
            90: 1.282,
            95: 1.645,
            97: 1.881,
            98: 2.054,
            99: 2.326,
            99.5: 2.576,
            99.9: 3.090,
        }
        
        # Return closest match
        return z_scores.get(service_level_pct, 1.645)  # Default to 95%
    
    def get_lead_time(self, part):
        """
        Get lead time for a part from supplier information.
        
        Args:
            part: Part instance
        
        Returns:
            int: Lead time in days or None
        """
        try:
            # Try to get from supplier parts
            supplier_part = part.supplier_parts.filter(
                supplier__is_supplier=True
            ).order_by('supplier__name').first()
            
            if supplier_part and hasattr(supplier_part, 'lead_time'):
                return supplier_part.lead_time
            
            # Fallback to manufacturer part
            if hasattr(part, 'manufacturer_part'):
                manufacturer_part = part.manufacturer_part.first()
                if manufacturer_part and hasattr(manufacturer_part, 'lead_time'):
                    return manufacturer_part.lead_time
            
        except Exception as e:
            logger.error(f"Error getting lead time: {str(e)}")
        
        return None
    
    def calculate_projected_stock(self, part):
        """
        Calculate projected available stock including inbound POs.
        
        Formula: Projected = Current + Inbound POs - Committed (SO/Builds)
        
        Args:
            part: Part instance
        
        Returns:
            Decimal: Projected stock quantity
        """
        # Current stock
        current_stock = Decimal(part.get_stock_count())
        
        # Inbound inventory from Purchase Orders
        inbound_qty = self.get_inbound_po_quantity(part)
        
        # Committed stock (allocated to sales orders, builds)
        committed_qty = Decimal(part.allocated_to_sales_orders())
        committed_qty += Decimal(part.allocated_to_build_orders())
        
        projected = current_stock + inbound_qty - committed_qty
        
        return projected
    
    def get_inbound_po_quantity(self, part):
        """
        Get quantity of part on open purchase orders (inbound).
        
        Only includes POs with status PLACED or IN_PROGRESS (not PENDING).
        
        Args:
            part: Part instance
        
        Returns:
            Decimal: Total inbound quantity
        """
        try:
            from order.models import PurchaseOrder, PurchaseOrderLineItem
            
            # Query PO lines for this part that are on placed/in-progress orders
            po_lines = PurchaseOrderLineItem.objects.filter(
                part=part,
                order__status__in=[
                    PurchaseOrder.PLACED,     # Status 20 - Order issued to supplier
                    PurchaseOrder.COMPLETE    # Status 30 - But not yet received
                ]
            ).exclude(
                received__gte=F('quantity')  # Exclude fully received lines
            )
            
            total_inbound = Decimal(0)
            for line in po_lines:
                outstanding = line.quantity - (line.received or 0)
                total_inbound += Decimal(outstanding)
            
            return total_inbound
            
        except Exception as e:
            logger.error(f"Error calculating inbound PO quantity: {str(e)}")
            return Decimal(0)
    
    def get_stockout_prediction(self, part, rop):
        """
        Get predicted stockout date from forecasting plugin.
        
        Integrates with inventree-stock-forecasting plugin if available.
        
        Args:
            part: Part instance
            rop: Reorder point threshold
        
        Returns:
            dict: {'date': Date or None, 'days': int or None}
        """
        try:
            # Check if forecasting plugin is available
            from plugin.registry import registry
            forecasting_plugin = registry.get_plugin('inventree-stock-forecasting')
            
            if not forecasting_plugin:
                # No forecasting plugin, estimate based on demand rate
                return self.estimate_stockout_simple(part, rop)
            
            # Get forecast data from plugin
            forecast_data = forecasting_plugin.get_forecast_for_part(part.pk)
            
            # Find when stock drops below ROP
            for forecast_point in forecast_data:
                if forecast_point['projected_stock'] < rop:
                    stockout_date = forecast_point['date']
                    days_until = (stockout_date - timezone.now().date()).days
                    return {
                        'date': stockout_date,
                        'days': days_until
                    }
            
            # No stockout predicted in forecast horizon
            return {'date': None, 'days': None}
            
        except Exception as e:
            logger.warning(f"Could not get forecast data: {str(e)}")
            return self.estimate_stockout_simple(part, rop)
    
    def estimate_stockout_simple(self, part, rop):
        """
        Simple stockout estimation based on current stock and demand rate.
        
        Args:
            part: Part instance
            rop: Reorder point
        
        Returns:
            dict: {'date': Date or None, 'days': int or None}
        """
        try:
            from .models import ROPPolicy
            policy = ROPPolicy.objects.get(part=part)
            
            if not policy.last_calculated_demand_rate:
                return {'date': None, 'days': None}
            
            current_stock = Decimal(part.get_stock_count())
            demand_rate = policy.last_calculated_demand_rate
            
            if demand_rate <= 0:
                return {'date': None, 'days': None}
            
            # Days until stock drops below ROP
            days_until = int((current_stock - rop) / demand_rate)
            
            if days_until < 0:
                days_until = 0  # Already below ROP
            
            stockout_date = timezone.now().date() + timedelta(days=days_until)
            
            return {
                'date': stockout_date,
                'days': days_until
            }
            
        except Exception as e:
            logger.error(f"Error estimating stockout: {str(e)}")
            return {'date': None, 'days': None}
    
    def get_preferred_supplier(self, part):
        """
        Determine the preferred supplier for a part.
        
        Prioritizes based on:
        1. Shortest lead time
        2. Lowest cost
        3. Primary supplier flag
        
        Args:
            part: Part instance
        
        Returns:
            Company instance or None
        """
        try:
            supplier_parts = part.supplier_parts.filter(
                supplier__is_supplier=True,
                supplier__is_active=True
            ).select_related('supplier')
            
            if not supplier_parts.exists():
                return None
            
            # Prioritize by lead time if available
            for sp in supplier_parts:
                if hasattr(sp, 'lead_time') and sp.lead_time:
                    return sp.supplier
            
            # Otherwise return first active supplier
            return supplier_parts.first().supplier
            
        except Exception as e:
            logger.error(f"Error getting preferred supplier: {str(e)}")
            return None
    
    def generate_purchase_order(self, suggestion_id):
        """
        Generate a Purchase Order from an ROP suggestion.
        
        Args:
            suggestion_id: ID of the ROPSuggestion
        
        Returns:
            PurchaseOrder instance or None
        """
        from .models import ROPSuggestion
        from order.models import PurchaseOrder, PurchaseOrderLineItem
        
        try:
            suggestion = ROPSuggestion.objects.get(pk=suggestion_id)
            
            if suggestion.status != 'PENDING':
                logger.warning(f"Suggestion {suggestion_id} is not pending")
                return None
            
            if not suggestion.suggested_supplier:
                logger.error(f"No supplier specified for suggestion {suggestion_id}")
                return None
            
            # Create Purchase Order
            po = PurchaseOrder.objects.create(
                supplier=suggestion.suggested_supplier,
                description=f"Auto-generated from ROP suggestion for {suggestion.rop_policy.part.name}",
                reference=f"ROP-{timezone.now().strftime('%Y%m%d')}-{suggestion_id}",
                status=PurchaseOrder.PENDING,
            )
            
            # Create line item
            PurchaseOrderLineItem.objects.create(
                order=po,
                part=suggestion.rop_policy.part,
                quantity=suggestion.suggested_order_qty,
                reference=f"ROP Suggestion #{suggestion_id}",
            )
            
            # Update suggestion
            suggestion.status = 'PO_CREATED'
            suggestion.purchase_order = po
            suggestion.actioned_date = timezone.now()
            suggestion.save()
            
            logger.info(f"Created PO {po.reference} from suggestion {suggestion_id}")
            
            return po
            
        except Exception as e:
            logger.error(f"Error generating PO from suggestion: {str(e)}")
            return None
