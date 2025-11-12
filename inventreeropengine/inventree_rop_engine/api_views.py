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
            # TODO: Database tables not created yet - returning empty data
            # Once migrations are working, uncomment the query below

            # For now, return empty results so the widget can load
            return Response({
                'count': 0,
                'results': [],
                'timestamp': timezone.now().isoformat(),
                'message': 'Database tables not yet created. Enable the plugin and restart InvenTree to create tables.'
            })

            # Original code (commented out until tables exist):
            # suggestions = ROPSuggestion.objects.filter(...)

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
            # TODO: Database tables not created yet - returning placeholder data
            return Response({
                'part_id': pk,
                'has_policy': False,
                'message': 'Database tables not yet created. ROP analysis will be available once migrations run successfully.',
            })

            # Original code (commented out until tables exist):
            # part = get_object_or_404(Part, pk=pk)
            # policy = ROPPolicy.objects.get(part=part)
            # ...

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
