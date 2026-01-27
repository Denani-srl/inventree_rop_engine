"""
Custom Django models for ROP Suggestion Engine.

These models store:
- ROP policy configurations per part
- Calculated demand statistics
- Generated suggestions with timestamps
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class ROPPolicy(models.Model):
    """
    Stores ROP policy configuration for individual parts.
    
    Allows manual override of safety stock and custom parameters
    per part, decoupling from core InvenTree part model.
    """
    
    class Meta:
        app_label = 'inventree_rop_engine'
        verbose_name = _('ROP Policy')
        verbose_name_plural = _('ROP Policies')
        unique_together = ('part',)
    
    # Link to InvenTree Part (using integer FK to avoid import issues)
    part = models.OneToOneField(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='rop_policy',
        verbose_name=_('Part'),
        help_text=_('The part this ROP policy applies to')
    )
    
    # Safety Stock Configuration
    safety_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Safety Stock'),
        help_text=_('Manual safety stock quantity (buffer inventory)')
    )
    
    use_calculated_safety_stock = models.BooleanField(
        default=False,
        verbose_name=_('Use Calculated Safety Stock'),
        help_text=_('Calculate safety stock based on demand variability and service level')
    )
    
    service_level = models.IntegerField(
        default=95,
        validators=[MinValueValidator(50), MaxValueValidator(99)],
        verbose_name=_('Service Level (%)'),
        help_text=_('Target service level for calculated safety stock (e.g., 95 = 95% protection)')
    )
    
    # Demand Calculation Parameters
    custom_lookback_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(7)],
        verbose_name=_('Custom Lookback Period (Days)'),
        help_text=_('Override global lookback period for this part')
    )
    
    # Target Stock Level
    target_stock_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.0,
        validators=[MinValueValidator(1.0)],
        verbose_name=_('Target Stock Multiplier'),
        help_text=_('Multiplier for target stock level (e.g., 2.0 = order up to 2x ROP)')
    )
    
    # Cached Calculations (for performance)
    last_calculated_rop = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Last Calculated ROP'),
        help_text=_('Most recent ROP calculation result')
    )
    
    last_calculated_demand_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Last Demand Rate'),
        help_text=_('Average daily demand rate from last calculation')
    )
    
    last_calculation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last Calculation Date'),
        help_text=_('When ROP was last calculated for this part')
    )
    
    # Control Flags
    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
        help_text=_('Enable ROP calculations for this part')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes about this ROP policy')
    )
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ROP Policy for {self.part.name}"
    
    def get_effective_lookback_days(self, plugin_instance):
        """Get the effective lookback period (custom or global)."""
        if self.custom_lookback_days:
            return self.custom_lookback_days
        return plugin_instance.get_setting('LOOKBACK_PERIOD_DAYS')
    
    def get_effective_safety_stock(self, calculated_ss=None):
        """
        Get the effective safety stock value.
        
        Args:
            calculated_ss: The statistically calculated safety stock (if available)
        
        Returns:
            Decimal: The safety stock value to use
        """
        if self.use_calculated_safety_stock and calculated_ss is not None:
            return calculated_ss
        return self.safety_stock


class DemandStatistics(models.Model):
    """
    Stores historical demand statistics for parts.
    
    Used for statistical safety stock calculation and trend analysis.
    """
    
    class Meta:
        app_label = 'inventree_rop_engine'
        verbose_name = _('Demand Statistics')
        verbose_name_plural = _('Demand Statistics')
        ordering = ['-calculation_date']
    
    rop_policy = models.ForeignKey(
        ROPPolicy,
        on_delete=models.CASCADE,
        related_name='demand_statistics',
        verbose_name=_('ROP Policy')
    )
    
    calculation_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Calculation Date')
    )
    
    # Statistical measures
    mean_daily_demand = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name=_('Mean Daily Demand')
    )
    
    std_dev_daily_demand = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name=_('Standard Deviation of Daily Demand')
    )
    
    total_removals = models.IntegerField(
        verbose_name=_('Total Removal Events'),
        help_text=_('Number of removal transactions in the analysis period')
    )
    
    analysis_period_days = models.IntegerField(
        verbose_name=_('Analysis Period (Days)')
    )
    
    # Calculated safety stock
    calculated_safety_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Calculated Safety Stock')
    )
    
    def __str__(self):
        return f"Demand Stats for {self.rop_policy.part.name} ({self.calculation_date.date()})"


class ROPSuggestion(models.Model):
    """
    Stores generated reorder suggestions.
    
    Tracks the history of suggestions and their execution status.
    """
    
    class Meta:
        app_label = 'inventree_rop_engine'
        verbose_name = _('ROP Suggestion')
        verbose_name_plural = _('ROP Suggestions')
        ordering = ['-urgency_score', 'stockout_date']
    
    STATUS_CHOICES = [
        ('PENDING', _('Pending Action')),
        ('PO_CREATED', _('Purchase Order Created')),
        ('DISMISSED', _('Dismissed')),
        ('EXPIRED', _('Expired')),
    ]
    
    rop_policy = models.ForeignKey(
        ROPPolicy,
        on_delete=models.CASCADE,
        related_name='suggestions',
        verbose_name=_('ROP Policy')
    )
    
    # Suggestion details
    suggested_order_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Suggested Order Quantity (SOQ)')
    )
    
    current_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Current Stock at Suggestion')
    )
    
    projected_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Projected Stock Level')
    )
    
    calculated_rop = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Calculated ROP')
    )
    
    # Timing information
    stockout_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Projected Stockout Date'),
        help_text=_('Date when stock is projected to drop below ROP')
    )
    
    days_until_stockout = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Days Until Stockout')
    )
    
    urgency_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('Urgency Score'),
        help_text=_('Higher score = more urgent (0-100)')
    )
    
    # Supplier information
    suggested_supplier = models.ForeignKey(
        'company.Company',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Suggested Supplier')
    )
    
    lead_time_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Lead Time (Days)')
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_('Status')
    )
    
    created_date = models.DateTimeField(auto_now_add=True)
    actioned_date = models.DateTimeField(null=True, blank=True)
    
    # Link to created PO if actioned
    purchase_order = models.ForeignKey(
        'order.PurchaseOrder',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rop_suggestions',
        verbose_name=_('Purchase Order')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    def __str__(self):
        return f"Suggestion: Order {self.suggested_order_qty} of {self.rop_policy.part.name}"
    
    def calculate_urgency_score(self):
        """
        Calculate urgency score based on:
        - Days until stockout
        - Severity of projected shortage
        - Lead time considerations
        """
        if not self.days_until_stockout:
            return 100.0  # Already below ROP
        
        # Base score from time urgency (0-50 points)
        if self.days_until_stockout <= 0:
            time_score = 50.0
        elif self.days_until_stockout <= 7:
            time_score = 40.0
        elif self.days_until_stockout <= 14:
            time_score = 30.0
        elif self.days_until_stockout <= 30:
            time_score = 20.0
        else:
            time_score = max(0, 20 - (self.days_until_stockout - 30) / 10)
        
        # Severity score from projected shortage (0-30 points)
        if self.projected_stock <= 0:
            severity_score = 30.0
        else:
            calc_rop = float(self.calculated_rop)
            if calc_rop == 0:
                shortage_ratio = 0
            else:
                shortage_ratio = (calc_rop - float(self.projected_stock)) / calc_rop
            severity_score = min(30.0, shortage_ratio * 30)
        
        # Lead time score (0-20 points)
        if self.lead_time_days and self.days_until_stockout:
            if self.days_until_stockout < self.lead_time_days:
                lead_time_score = 20.0  # Critical: stockout before delivery
            elif self.days_until_stockout < self.lead_time_days * 1.5:
                lead_time_score = 15.0
            else:
                lead_time_score = 10.0
        else:
            lead_time_score = 10.0
        
        total_score = min(100.0, time_score + severity_score + lead_time_score)
        return round(total_score, 2)
    
    def save(self, *args, **kwargs):
        """Override save to automatically calculate urgency score."""
        self.urgency_score = self.calculate_urgency_score()
        super().save(*args, **kwargs)
