# InvenTree ROP Suggestion Engine Plugin

## Overview

The **ROP (Reorder Point) Suggestion Engine** is a comprehensive InvenTree plugin that transforms inventory management from reactive threshold alerts to predictive, prescriptive procurement planning. It automatically calculates when to reorder parts based on:

- **Historical demand analysis** from stock removal events
- **Lead time considerations** from supplier data
- **Statistical safety stock** calculation based on demand variability
- **Projected stock levels** including inbound purchase orders
- **Integration with stock forecasting** for accurate stockout predictions

## Key Features

### 🎯 Prescriptive Ordering Suggestions
- Automatically calculates Reorder Points (ROP) using industry-standard formulas
- Generates Suggested Order Quantities (SOQ) to optimize inventory levels
- Prioritizes suggestions based on urgency and stockout risk

### 📊 Dashboard Widget
- Real-time view of urgent reorder suggestions
- Sortable by urgency, stockout date, and quantity
- One-click Purchase Order generation

### 📈 Part Detail Panel
- Comprehensive ROP analysis for individual parts
- Visual demand trend charts
- Historical statistics and policy configuration
- Instant recalculation capability

### ⚙️ Flexible Configuration
- Global settings for lookback periods and service levels
- Per-part policy overrides
- Manual or automatic safety stock calculation
- Customizable target stock multipliers

### 🔄 Background Automation
- Scheduled automatic ROP calculation
- Configurable calculation intervals
- Minimal UI performance impact

### 🔌 Ecosystem Integration
- Works seamlessly with `inventree-stock-forecasting` plugin
- Compatible with `inventree-supplier-panel` for automated PO transmission
- Integrates with core Purchase Order system

## Installation

### Prerequisites

- InvenTree version 0.13.0 or higher
- Python 3.9 or higher
- (Recommended) `inventree-stock-forecasting` plugin installed

### Method 1: Install from Source

1. Clone this repository or download the source code:
   ```bash
   git clone https://github.com/yourusername/inventree-rop-suggestion.git
   cd inventree-rop-suggestion
   ```

2. Install the plugin:
   ```bash
   pip install .
   ```

3. Restart your InvenTree server

4. Enable the plugin in InvenTree:
   - Navigate to **Settings → Plugins**
   - Find "ROP Suggestion Engine"
   - Toggle the switch to enable
   - Configure global settings as needed

### Method 2: Install via pip

```bash
pip install inventree-rop-suggestion
```

Then follow steps 3-4 above.

## Configuration

### Global Settings

Access plugin settings via **Settings → Plugins → ROP Suggestion Engine**:

| Setting | Description | Default |
|---------|-------------|---------|
| **Lookback Period (Days)** | Number of days to analyze for demand calculation | 90 |
| **Default Service Level (%)** | Target service level for safety stock (e.g., 95 = 95% protection) | 95 |
| **Enable Auto Calculation** | Automatically calculate ROP on schedule | True |
| **Calculation Interval (Hours)** | How often to recalculate ROP suggestions | 24 |
| **Minimum Demand Samples** | Minimum removal events required for ROP calculation | 5 |
| **Target Stock Multiplier** | Multiplier for maximum stock level (e.g., 2.0 = 2x ROP) | 2.0 |

### Per-Part Policy Configuration

For each part, you can configure individual ROP policies:

1. Navigate to the part's detail page
2. View the "ROP Analysis" panel
3. Click "Edit Policy Settings" (or use Django admin)

**Policy Options:**
- **Safety Stock**: Manual safety stock quantity (buffer inventory)
- **Use Calculated Safety Stock**: Enable automatic calculation based on demand variability
- **Service Level**: Target service level percentage (50-99%)
- **Custom Lookback Period**: Override global lookback period for this part
- **Target Stock Multiplier**: Custom multiplier for order-up-to level
- **Enabled**: Enable/disable ROP calculations for this part

## Usage

### Dashboard Widget

The dashboard widget displays urgent reorder suggestions:

1. Navigate to your InvenTree dashboard
2. The "Urgent Reorder Suggestions" widget shows parts requiring immediate attention
3. Each row displays:
   - **Urgency Score** (0-100, color-coded)
   - **Part Name** and IPN
   - **Suggested Order Quantity**
   - **Current Stock**
   - **Days Until Stockout**
   - **Supplier** and Lead Time
   - **Quick Order Button**

4. Click any row to view detailed part analysis
5. Click "Order" button to generate a Purchase Order instantly

### Part Detail Panel

On any part's detail page, the "ROP Analysis" panel provides:

#### Policy Configuration Section
- Current ROP policy settings
- Calculated ROP threshold
- Demand rate (units/day)
- Last calculation timestamp

#### Demand Statistics
- Mean daily demand
- Standard deviation
- Analysis period and sample count
- Calculated safety stock

#### Current Stock Status
- Current quantity in stock
- Stock status vs ROP threshold
- On-order quantities

#### Reorder Recommendation (if applicable)
- Suggested Order Quantity
- Urgency score and color-coding
- Projected stockout date
- Days until stockout

#### Actions
- **Recalculate ROP**: Trigger immediate recalculation
- **Generate PO**: Create Purchase Order from suggestion
- **Edit Policy**: Modify ROP policy settings

### Manual ROP Calculation

To manually trigger ROP calculation for a specific part:

1. Navigate to the part's detail page
2. In the "ROP Analysis" panel, click "Recalculate ROP"
3. The system will:
   - Analyze historical demand
   - Calculate safety stock (if configured)
   - Determine ROP threshold
   - Check projected stock levels
   - Generate suggestion if needed

### Purchase Order Generation

#### From Dashboard Widget:
1. Click "Order" button next to any suggestion
2. Confirm the action
3. System creates a draft Purchase Order automatically
4. You'll be redirected to the new PO for review

#### From Part Panel:
1. Click "Generate Purchase Order" in the suggestion card
2. Confirm the action
3. Review the created PO

**Auto-Generated PO Includes:**
- Pre-populated quantity (SOQ)
- Selected supplier (based on lead time/cost)
- Reference linking back to ROP suggestion
- Status: PENDING (ready for review)

## How It Works

### ROP Calculation Formula

The plugin uses the industry-standard ROP formula:

```
ROP = (Demand During Lead Time) + (Safety Stock)

Where:
- Demand During Lead Time (LTD) = D × L
- D = Average Daily Demand Rate (from historical removals)
- L = Lead Time (from supplier data)
- Safety Stock (SS) = Z × σ_LT
- Z = Z-score for desired service level
- σ_LT = Standard deviation of demand during lead time
```

### Suggested Order Quantity (SOQ)

```
SOQ = Target Stock Level - Projected Available Stock

Where:
- Target Stock = ROP × Target Stock Multiplier
- Projected Stock = Current Stock + Inbound POs - Committed Stock
```

### Demand Rate Calculation

The plugin analyzes historical `StockItemTracking` records to calculate demand:

1. Filters for "Remove Stock" events over the lookback period
2. Calculates total removed quantity
3. Computes mean daily demand rate
4. Calculates standard deviation for safety stock

### Inbound Inventory Integration

**Critical Feature**: The plugin accounts for inventory already on order:

```
Projected Stock = Current + Inbound POs - Committed (SO/Builds)
```

This prevents false-positive reorder alerts when stock is already inbound.

### Urgency Scoring

Suggestions are prioritized using an urgency score (0-100) based on:

- **Time Urgency** (0-50 points): Days until stockout
  - ≤0 days: 50 points
  - ≤7 days: 40 points
  - ≤14 days: 30 points
  - ≤30 days: 20 points
  
- **Severity** (0-30 points): Depth of projected shortage
  - Already at zero: 30 points
  - Proportional to shortage percentage
  
- **Lead Time Risk** (0-20 points): Relationship between stockout date and lead time
  - Stockout before delivery: 20 points (critical)
  - Stockout within 1.5× lead time: 15 points

## Integration with Other Plugins

### inventree-stock-forecasting
**Required for advanced predictions**

The ROP engine consumes time-series projections from the stock forecasting plugin to:
- Determine precise stockout dates
- Account for future demand from Sales Orders and Build Orders
- Improve accuracy of projection calculations

**Setup**: Install and enable `inventree-stock-forecasting` before or alongside this plugin.

### inventree-supplier-panel
**Recommended for automation**

After generating a PO from ROP suggestions, use the supplier panel to:
- Automatically transmit POs to Mouser, Digikey, etc.
- Streamline the procurement workflow
- Eliminate manual data entry

### inventree-report-lsp-plugin
**Recommended for reporting**

Create custom procurement reports:
- Order Suggestion Logs
- ROP Analysis Summaries
- Demand Trend Reports
- Procurement Pipeline Status

## Database Models

The plugin creates three custom Django models:

### ROPPolicy
Stores ROP configuration per part:
- Safety stock settings
- Service level targets
- Custom lookback periods
- Target stock multipliers
- Cached ROP calculations

### DemandStatistics
Historical demand analysis records:
- Mean and standard deviation of demand
- Total removal events
- Analysis period
- Calculated safety stock

### ROPSuggestion
Generated reorder suggestions:
- Suggested order quantities
- Projected stock levels
- Urgency scores
- Stockout predictions
- Status tracking (PENDING, PO_CREATED, DISMISSED, EXPIRED)
- Linked Purchase Orders

## API Endpoints

The plugin exposes REST API endpoints:

### GET `/api/plugin/rop-suggestion/suggestions/`
List all pending ROP suggestions

**Query Parameters:**
- `limit`: Maximum results (default: 20)
- `min_urgency`: Minimum urgency score filter (default: 0)

### GET `/api/plugin/rop-suggestion/part/<pk>/details/`
Get detailed ROP analysis for a specific part

### POST `/api/plugin/rop-suggestion/part/<pk>/calculate/`
Trigger immediate ROP calculation for a part

### POST `/api/plugin/rop-suggestion/generate-po/`
Generate Purchase Order from suggestion

**Request Body:**
```json
{
  "suggestion_id": 123
}
```

## Performance Considerations

### Background Calculation
Heavy ROP calculations run as scheduled background tasks to avoid UI blocking:
- Default interval: Every 24 hours
- Configurable via settings
- Results cached in database

### Manual Recalculation
Individual part calculations execute on-demand when requested via UI

### Database Queries
Optimized queries with:
- Select_related() for foreign keys
- Prefetch_related() for many-to-many
- Indexed fields for fast lookups

## Troubleshooting

### No Suggestions Appearing
**Check:**
1. Is the plugin enabled?
2. Are parts configured with ROP policies?
3. Is there sufficient historical demand data (≥ minimum samples)?
4. Are lead times configured in supplier data?

### Incorrect Demand Calculation
**Verify:**
1. Stock removal tracking is enabled
2. Lookback period is appropriate for part usage patterns
3. Removal events are being logged correctly

### Inaccurate Stockout Predictions
**Ensure:**
1. `inventree-stock-forecasting` plugin is installed and enabled
2. Sales Orders and Build Orders are up-to-date
3. Purchase Order statuses are current

### Permission Errors
**Required Permissions:**
- `order.view_purchaseorder` - View ROP suggestions
- `order.add_purchaseorder` - Generate Purchase Orders
- `order.change_purchaseorder` - Modify ROP calculations

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
```
inventree_rop_engine/
├── __init__.py          # Plugin class with mixins
├── models.py            # Django models (ROPPolicy, DemandStatistics, ROPSuggestion)
├── rop_engine.py        # Core calculation logic
├── api_views.py         # REST API endpoints
└── ui/                  # Frontend JavaScript
    ├── rop_dashboard.js # Dashboard widget
    └── rop_part_panel.js # Part detail panel
```

### Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the InvenTree plugin documentation
- Join the InvenTree community forums

## Acknowledgments

Based on the architectural analysis document "Developing a Prescriptive Reorder Point System for InvenTree" which outlines the integration strategy and functional requirements.

---

**Version:** 1.0.0  
**Author:** Custom Development  
**InvenTree Compatibility:** ≥0.13.0
