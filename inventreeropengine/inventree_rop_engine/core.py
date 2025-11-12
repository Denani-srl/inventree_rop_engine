"""Prescriptive reorder point calculation and procurement suggestion engine"""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, ScheduleMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin

from . import PLUGIN_VERSION


class inventreeropengine(AppMixin, ScheduleMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin, InvenTreePlugin):

    """inventreeropengine - custom InvenTree plugin."""

    # Plugin metadata
    TITLE = "ROP Suggestion Engine"
    NAME = "ROPSuggestionPlugin"
    SLUG = "inventree-rop-engine"
    DESCRIPTION = "Prescriptive reorder point calculation and procurement suggestion engine"
    VERSION = PLUGIN_VERSION

    # Additional project information
    AUTHOR = "Denani srl"

    LICENSE = "MIT"

    # Supported InvenTree versions
    MIN_VERSION = '0.18.0'

    # Render custom UI elements to the plugin settings page
    ADMIN_SOURCE = "Settings.js:renderPluginSettings"
    
    # Scheduled tasks (from ScheduleMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/schedule/
    SCHEDULED_TASKS = {
        # Define your scheduled tasks here...
    }
    
    # Plugin settings (from SettingsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/settings/
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
    
    
    
    
    
    # Custom URL endpoints (from UrlsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/urls/
    def setup_urls(self):
        """Configure custom URL endpoints for this plugin."""
        from django.urls import path
        from . import api_views

        return [
            path('suggestions/', api_views.ROPSuggestionsView.as_view(), name='rop-suggestions'),
            path('part/<int:pk>/details/', api_views.PartROPDetailsView.as_view(), name='part-rop-details'),
            path('part/<int:pk>/calculate/', api_views.CalculatePartROPView.as_view(), name='calculate-part-rop'),
            path('generate-po/', api_views.GeneratePOFromSuggestionView.as_view(), name='generate-po'),
        ]
    

    # User interface elements (from UserInterfaceMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/ui/
    
    # Custom UI panels
    def get_ui_panels(self, request, context: dict, **kwargs):
        """Return a list of custom panels to be rendered in the InvenTree user interface."""

        panels = []

        # Only display this panel for the 'part' target
        if context.get('target_model') == 'part':
            part_id = context.get('target_id')
            api_url = f'/api/plugin/{self.slug}/part/{part_id}/details/'

            panels.append({
                'key': 'rop-analysis-panel',
                'title': 'ROP Analysis',
                'description': 'Reorder Point analysis and procurement suggestions',
                'icon': 'ti:chart-line:outline',
                'source': self.plugin_static_file('Panel.js:renderROPAnalysisPanel'),
                'context': {
                    'settings': self.get_settings_dict(),
                    'part_id': part_id,
                    'api_url': api_url,
                }
            })

        return panels
    

    # Custom dashboard items
    def get_ui_dashboard_items(self, request, context: dict, **kwargs):
        """Return a list of custom dashboard items to be rendered in the InvenTree user interface."""

        items = []

        api_url = f'/api/plugin/{self.slug}/suggestions/'

        items.append({
            'key': 'rop-urgent-suggestions',
            'title': 'Urgent Reorder Suggestions',
            'description': 'Parts requiring immediate procurement action',
            'icon': 'ti:alert-triangle:outline',
            'source': self.plugin_static_file('Dashboard.js:renderROPDashboardItem'),
            'width': 6,
            'height': 4,
            'context': {
                'settings': self.get_settings_dict(),
                'api_url': api_url,
            }
        })

        return items
