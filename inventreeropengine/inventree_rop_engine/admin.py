"""
Django Admin Configuration for ROP Suggestion Engine Models

Provides administrative interface for:
- ROP Policy management
- Demand statistics viewing
- Suggestion monitoring and management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ROPPolicy, DemandStatistics, ROPSuggestion


@admin.register(ROPPolicy)
class ROPPolicyAdmin(admin.ModelAdmin):
    """Admin interface for ROP Policy management."""
    
    list_display = (
        'part_link',
        'enabled',
        'safety_stock',
        'use_calculated_safety_stock',
        'service_level',
        'last_calculated_rop',
        'last_calculation_date',
    )
    
    list_filter = (
        'enabled',
        'use_calculated_safety_stock',
        'service_level',
    )
    
    search_fields = (
        'part__name',
        'part__IPN',
        'part__description',
    )
    
    readonly_fields = (
        'last_calculated_rop',
        'last_calculated_demand_rate',
        'last_calculation_date',
        'created_date',
        'modified_date',
    )
    
    fieldsets = (
        ('Part Information', {
            'fields': ('part',)
        }),
        ('Safety Stock Configuration', {
            'fields': (
                'safety_stock',
                'use_calculated_safety_stock',
                'service_level',
            )
        }),
        ('Demand Analysis', {
            'fields': (
                'custom_lookback_days',
            )
        }),
        ('Target Stock', {
            'fields': (
                'target_stock_multiplier',
            )
        }),
        ('Calculated Values (Read-Only)', {
            'fields': (
                'last_calculated_rop',
                'last_calculated_demand_rate',
                'last_calculation_date',
            ),
            'classes': ('collapse',)
        }),
        ('Control', {
            'fields': (
                'enabled',
                'notes',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_date',
                'modified_date',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def part_link(self, obj):
        """Display clickable link to part."""
        url = f'/part/{obj.part.pk}/'
        return format_html('<a href="{}">{}</a>', url, obj.part.name)
    part_link.short_description = 'Part'
    part_link.admin_order_field = 'part__name'


@admin.register(DemandStatistics)
class DemandStatisticsAdmin(admin.ModelAdmin):
    """Admin interface for viewing demand statistics."""
    
    list_display = (
        'part_name',
        'calculation_date',
        'mean_daily_demand',
        'std_dev_daily_demand',
        'total_removals',
        'analysis_period_days',
    )
    
    list_filter = (
        'calculation_date',
        'analysis_period_days',
    )
    
    search_fields = (
        'rop_policy__part__name',
        'rop_policy__part__IPN',
    )
    
    readonly_fields = (
        'rop_policy',
        'calculation_date',
        'mean_daily_demand',
        'std_dev_daily_demand',
        'total_removals',
        'analysis_period_days',
        'calculated_safety_stock',
    )
    
    def part_name(self, obj):
        """Display part name."""
        return obj.rop_policy.part.name
    part_name.short_description = 'Part'
    part_name.admin_order_field = 'rop_policy__part__name'
    
    def has_add_permission(self, request):
        """Disable manual addition (statistics are auto-generated)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make read-only (statistics are auto-generated)."""
        return False


@admin.register(ROPSuggestion)
class ROPSuggestionAdmin(admin.ModelAdmin):
    """Admin interface for monitoring and managing ROP suggestions."""
    
    list_display = (
        'part_name',
        'status_badge',
        'suggested_order_qty',
        'current_stock',
        'urgency_badge',
        'days_until_stockout',
        'suggested_supplier',
        'created_date',
    )
    
    list_filter = (
        'status',
        'created_date',
        'suggested_supplier',
    )
    
    search_fields = (
        'rop_policy__part__name',
        'rop_policy__part__IPN',
        'suggested_supplier__name',
    )
    
    readonly_fields = (
        'rop_policy',
        'suggested_order_qty',
        'current_stock',
        'projected_stock',
        'calculated_rop',
        'stockout_date',
        'days_until_stockout',
        'urgency_score',
        'suggested_supplier',
        'lead_time_days',
        'created_date',
        'actioned_date',
        'purchase_order',
    )
    
    fieldsets = (
        ('Part Information', {
            'fields': ('rop_policy',)
        }),
        ('Suggestion Details', {
            'fields': (
                'suggested_order_qty',
                'current_stock',
                'projected_stock',
                'calculated_rop',
            )
        }),
        ('Timing & Urgency', {
            'fields': (
                'stockout_date',
                'days_until_stockout',
                'urgency_score',
            )
        }),
        ('Supplier Information', {
            'fields': (
                'suggested_supplier',
                'lead_time_days',
            )
        }),
        ('Status & Action', {
            'fields': (
                'status',
                'purchase_order',
                'notes',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_date',
                'actioned_date',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_dismissed', 'mark_as_pending']
    
    def part_name(self, obj):
        """Display part name with link."""
        url = f'/part/{obj.rop_policy.part.pk}/'
        return format_html('<a href="{}">{}</a>', url, obj.rop_policy.part.name)
    part_name.short_description = 'Part'
    part_name.admin_order_field = 'rop_policy__part__name'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'PENDING': '#f0ad4e',
            'PO_CREATED': '#5cb85c',
            'DISMISSED': '#999',
            'EXPIRED': '#d9534f',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def urgency_badge(self, obj):
        """Display urgency score as colored badge."""
        score = float(obj.urgency_score)
        if score >= 80:
            color = '#d9534f'
        elif score >= 60:
            color = '#f0ad4e'
        elif score >= 40:
            color = '#f7dc6f'
        else:
            color = '#5cb85c'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            round(score)
        )
    urgency_badge.short_description = 'Urgency'
    urgency_badge.admin_order_field = 'urgency_score'
    
    def mark_as_dismissed(self, request, queryset):
        """Admin action to dismiss suggestions."""
        updated = queryset.update(status='DISMISSED')
        self.message_user(request, f'{updated} suggestion(s) marked as dismissed.')
    mark_as_dismissed.short_description = 'Mark selected as dismissed'
    
    def mark_as_pending(self, request, queryset):
        """Admin action to reactivate suggestions."""
        updated = queryset.update(status='PENDING')
        self.message_user(request, f'{updated} suggestion(s) marked as pending.')
    mark_as_pending.short_description = 'Mark selected as pending'
    
    def has_add_permission(self, request):
        """Disable manual addition (suggestions are auto-generated)."""
        return False
