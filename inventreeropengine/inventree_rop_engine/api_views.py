"""
REST API Views for ROP Suggestion Engine

Exposes endpoints for:
- Listing all ROP suggestions
- Getting detailed ROP analysis for a part
- Triggering ROP calculations
- Generating Purchase Orders from suggestions
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from part.models import Part
from .models import ROPPolicy, ROPSuggestion, DemandStatistics
from .rop_engine import ROPCalculationEngine

import logging

logger = logging.getLogger('inventree')


class ROPSuggestionsView(APIView):
    """
    API endpoint to retrieve all pending ROP suggestions.
    
    Used by the dashboard widget to display urgent reorder needs.
    
    GET /api/plugin/rop-suggestion/suggestions/
    Returns: List of pending suggestions, ordered by urgency
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all pending ROP suggestions."""
        try:
            # Check user permissions
            if not request.user.has_perm('order.view_purchaseorder'):
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get filter parameters
            max_results = int(request.query_params.get('limit', 20))
            min_urgency = float(request.query_params.get('min_urgency', 0))
            
            # Query pending suggestions
            suggestions = ROPSuggestion.objects.filter(
                status='PENDING',
                urgency_score__gte=min_urgency
            ).select_related(
                'rop_policy__part',
                'suggested_supplier'
            ).order_by('-urgency_score', 'stockout_date')[:max_results]
            
            # Serialize data
            data = []
            for suggestion in suggestions:
                part = suggestion.rop_policy.part
                data.append({
                    'id': suggestion.id,
                    'part_id': part.pk,
                    'part_name': part.name,
                    'part_IPN': part.IPN,
                    'part_description': part.description,
                    'suggested_order_qty': float(suggestion.suggested_order_qty),
                    'current_stock': float(suggestion.current_stock),
                    'projected_stock': float(suggestion.projected_stock),
                    'calculated_rop': float(suggestion.calculated_rop),
                    'urgency_score': float(suggestion.urgency_score),
                    'days_until_stockout': suggestion.days_until_stockout,
                    'stockout_date': suggestion.stockout_date.isoformat() if suggestion.stockout_date else None,
                    'supplier_name': suggestion.suggested_supplier.name if suggestion.suggested_supplier else None,
                    'supplier_id': suggestion.suggested_supplier.pk if suggestion.suggested_supplier else None,
                    'lead_time_days': suggestion.lead_time_days,
                    'created_date': suggestion.created_date.isoformat(),
                    'part_url': f'/part/{part.pk}/',
                })
            
            return Response({
                'count': len(data),
                'results': data,
                'timestamp': timezone.now().isoformat(),
            })
        
        except Exception as e:
            logger.error(f"Error retrieving ROP suggestions: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PartROPDetailsView(APIView):
    """
    API endpoint to retrieve detailed ROP analysis for a specific part.
    
    Used by the custom part panel to display:
    - ROP calculation breakdown
    - Demand statistics
    - Historical trends
    - Current suggestion (if any)
    
    GET /api/plugin/rop-suggestion/part/<pk>/details/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get ROP details for a specific part."""
        try:
            part = get_object_or_404(Part, pk=pk)
            
            # Get or create ROP policy
            try:
                policy = ROPPolicy.objects.get(part=part)
            except ROPPolicy.DoesNotExist:
                return Response({
                    'part_id': pk,
                    'has_policy': False,
                    'message': 'No ROP policy configured for this part',
                })
            
            # Get latest demand statistics
            latest_stats = policy.demand_statistics.first()
            
            # Get current suggestion
            current_suggestion = policy.suggestions.filter(
                status='PENDING'
            ).first()
            
            # Build response
            response_data = {
                'part_id': pk,
                'part_name': part.name,
                'has_policy': True,
                'policy': {
                    'enabled': policy.enabled,
                    'safety_stock': float(policy.safety_stock),
                    'use_calculated_safety_stock': policy.use_calculated_safety_stock,
                    'service_level': policy.service_level,
                    'target_stock_multiplier': float(policy.target_stock_multiplier),
                    'last_calculated_rop': float(policy.last_calculated_rop) if policy.last_calculated_rop else None,
                    'last_calculated_demand_rate': float(policy.last_calculated_demand_rate) if policy.last_calculated_demand_rate else None,
                    'last_calculation_date': policy.last_calculation_date.isoformat() if policy.last_calculation_date else None,
                },
                'current_stock': float(part.get_stock_count()),
                'on_order': float(part.quantity_being_built()) if hasattr(part, 'quantity_being_built') else 0,
            }
            
            # Add demand statistics
            if latest_stats:
                response_data['demand_statistics'] = {
                    'mean_daily_demand': float(latest_stats.mean_daily_demand),
                    'std_dev_daily_demand': float(latest_stats.std_dev_daily_demand),
                    'total_removals': latest_stats.total_removals,
                    'analysis_period_days': latest_stats.analysis_period_days,
                    'calculated_safety_stock': float(latest_stats.calculated_safety_stock) if latest_stats.calculated_safety_stock else None,
                    'calculation_date': latest_stats.calculation_date.isoformat(),
                }
                
                # Add historical stats for charting
                historical_stats = policy.demand_statistics.all()[:30]  # Last 30 calculations
                response_data['historical_demand'] = [
                    {
                        'date': stat.calculation_date.date().isoformat(),
                        'mean_demand': float(stat.mean_daily_demand),
                        'std_dev': float(stat.std_dev_daily_demand),
                    }
                    for stat in historical_stats
                ]
            
            # Add current suggestion
            if current_suggestion:
                response_data['suggestion'] = {
                    'id': current_suggestion.id,
                    'suggested_order_qty': float(current_suggestion.suggested_order_qty),
                    'projected_stock': float(current_suggestion.projected_stock),
                    'calculated_rop': float(current_suggestion.calculated_rop),
                    'urgency_score': float(current_suggestion.urgency_score),
                    'days_until_stockout': current_suggestion.days_until_stockout,
                    'stockout_date': current_suggestion.stockout_date.isoformat() if current_suggestion.stockout_date else None,
                    'created_date': current_suggestion.created_date.isoformat(),
                }
            
            return Response(response_data)
        
        except Exception as e:
            logger.error(f"Error retrieving part ROP details: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CalculatePartROPView(APIView):
    """
    API endpoint to trigger ROP calculation for a specific part.
    
    POST /api/plugin/rop-suggestion/part/<pk>/calculate/
    Triggers immediate ROP calculation and returns results
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Calculate ROP for a specific part."""
        try:
            # Check user permissions
            if not request.user.has_perm('order.change_purchaseorder'):
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            part = get_object_or_404(Part, pk=pk)
            
            # Get plugin instance
            from plugin.registry import registry
            plugin = registry.get_plugin('rop-suggestion')
            
            if not plugin:
                return Response(
                    {'error': 'ROP plugin not loaded'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create engine and calculate
            engine = ROPCalculationEngine(plugin)
            suggestion = engine.calculate_part_rop(pk)
            
            if suggestion:
                return Response({
                    'success': True,
                    'message': 'ROP calculated successfully',
                    'suggestion_id': suggestion.id,
                    'suggested_order_qty': float(suggestion.suggested_order_qty),
                    'urgency_score': float(suggestion.urgency_score),
                })
            else:
                return Response({
                    'success': True,
                    'message': 'ROP calculated - no reorder needed',
                    'suggestion_id': None,
                })
        
        except Exception as e:
            logger.error(f"Error calculating part ROP: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeneratePOFromSuggestionView(APIView):
    """
    API endpoint to generate a Purchase Order from an ROP suggestion.
    
    POST /api/plugin/rop-suggestion/generate-po/
    Body: {'suggestion_id': <id>}
    
    Creates a draft PO in the InvenTree system.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate PO from suggestion."""
        try:
            # Check user permissions
            if not request.user.has_perm('order.add_purchaseorder'):
                return Response(
                    {'error': 'Insufficient permissions to create purchase orders'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            suggestion_id = request.data.get('suggestion_id')
            if not suggestion_id:
                return Response(
                    {'error': 'suggestion_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get plugin instance
            from plugin.registry import registry
            plugin = registry.get_plugin('rop-suggestion')
            
            if not plugin:
                return Response(
                    {'error': 'ROP plugin not loaded'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create engine and generate PO
            engine = ROPCalculationEngine(plugin)
            po = engine.generate_purchase_order(suggestion_id)
            
            if po:
                return Response({
                    'success': True,
                    'message': 'Purchase Order created successfully',
                    'po_id': po.pk,
                    'po_reference': po.reference,
                    'po_url': f'/order/purchase-order/{po.pk}/',
                })
            else:
                return Response(
                    {'error': 'Failed to generate Purchase Order'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(f"Error generating PO from suggestion: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Import timezone at the top if not already imported
from django.utils import timezone
