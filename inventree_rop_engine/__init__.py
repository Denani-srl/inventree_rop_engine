"""
InvenTree ROP (Reorder Point) Suggestion Engine Plugin

This plugin provides prescriptive reorder point calculations and procurement suggestions
based on demand rate analysis, lead times, and safety stock policies.

Compatible with InvenTree 1.1.2+
"""

from django.urls import path
from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import (
    AppMixin,
    SettingsMixin,
    UrlsMixin,
    UserInterfaceMixin,
)


class ROPSuggestionPlugin(InvenTreePlugin, AppMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin):
    """
    ROP Suggestion Engine - Prescriptive inventory replenishment plugin.
    
    Calculates reorder points based on:
    - Historical demand rates from stock removal events
    - Lead times
    - Safety stock policies
    - Projected stock levels from forecasting
    """
    
    NAME = "ROPSuggestionPlugin"
    SLUG = "rop-suggestion"
    TITLE = "ROP Suggestion Engine"
    DESCRIPTION = "Prescriptive reorder point calculation and procurement suggestions"
    VERSION = "1.0.0"
    AUTHOR = "Custom Development"
    
    # Mixin configuration
    NAVIGATION_TAB_NAME = "ROP Engine"
    NAVIGATION_TAB_ICON = "fas fa-chart-line"
    
    # ========================================================================
    # SettingsMixin - Global configuration parameters
    # ========================================================================
    
    SETTINGS = {
        'LOOKBACK_PERIOD_DAYS': {
            'name': _('Lookback Period (Days)'),
            'description': _('Number of days to analyze for demand rate calculation'),
            'default': 90,
            'validator': int,
        },
        'DEFAULT_SERVICE_LEVEL': {
            'name': _('Default Service Level (%)'),
            'description': _('Target service level for safety stock calculation (e.g., 95 for 95%)'),
            'default': 95,
            'validator': int,
        },
        'MIN_DEMAND_SAMPLES': {
            'name': _('Minimum Demand Samples'),
            'description': _('Minimum number of removal events required for ROP calculation'),
            'default': 5,
            'validator': int,
        },
        'TARGET_STOCK_MULTIPLIER': {
            'name': _('Target Stock Multiplier'),
            'description': _('Multiplier for maximum stock level (e.g., 2.0 = 2x ROP)'),
            'default': 2.0,
            'validator': float,
        },
    }
    
    # ========================================================================
    # UrlsMixin - Custom API endpoints
    # ========================================================================
    
    def setup_urls(self):
        """Define custom URL routes for the ROP API."""
        from . import api_views
        
        return [
            path('suggestions/', api_views.ROPSuggestionsView.as_view(), name='rop-suggestions'),
            path('part/<int:pk>/details/', api_views.PartROPDetailsView.as_view(), name='part-rop-details'),
            path('part/<int:pk>/calculate/', api_views.CalculatePartROPView.as_view(), name='calculate-part-rop'),
            path('generate-po/', api_views.GeneratePOFromSuggestionView.as_view(), name='generate-po'),
        ]
    
    # ========================================================================
    # UserInterfaceMixin - Dashboard widget and custom panels
    # ========================================================================
    
    def get_ui_panels(self, instance, request, context):
        """
        Add custom panels to part detail pages.
        Shows ROP analysis and stock projection visualization.
        """
        from part.models import Part
        
        panels = []
        
        # Only add panel to Part detail pages
        if isinstance(instance, Part):
            # Build API URL manually for compatibility
            api_url = f'/api/plugin/{self.slug}/part/{instance.pk}/details/'
            
            panels.append({
                'key': 'rop-analysis-panel',
                'title': 'ROP Analysis',
                'description': 'Reorder Point analysis and procurement suggestions',
                'source': self.plugin_static_file('rop_part_panel.js'),
                'context': {
                    'part_id': instance.pk,
                    'api_url': api_url,
                }
            })
        
        return panels
    
    def get_ui_features(self, feature_type, context, request):
        """
        Return custom UI features based on the requested feature type.

        Args:
            feature_type: The type of UI feature being requested (e.g., 'dashboard', 'panel')
            context: Query parameters and additional context data
            request: The HTTP request object

        Returns:
            List of UI feature configurations for the requested feature type
        """
        # Handle dashboard features
        if feature_type == 'dashboard':
            # Build API URL manually for compatibility
            api_url = f'/api/plugin/{self.slug}/suggestions/'

            return [
                {
                    'key': 'rop-urgent-suggestions',
                    'title': 'Urgent Reorder Suggestions',
                    'description': 'Parts requiring immediate procurement action',
                    'source': self.plugin_static_file('rop_dashboard.js') ,
                    'width': 6,
                    'height': 4,
                    'context': {
                        'api_url': api_url,
                    }
                }
            ]

        # Return empty list for other feature types
        return []
