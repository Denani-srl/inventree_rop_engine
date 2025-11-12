# InvenTree ROP (Reorder Point) Engine Plugin

Prescriptive reorder point calculation and procurement suggestion engine for InvenTree.

## Features

- **Automated ROP Calculation**: Analyzes historical demand patterns and calculates optimal reorder points
- **Safety Stock Management**: Configurable service levels and safety stock policies
- **Procurement Suggestions**: Generates actionable purchase recommendations with urgency scoring
- **Dashboard Widget**: Displays urgent reorder suggestions directly on the InvenTree dashboard
- **Part Analysis Panel**: Detailed ROP analysis on individual part pages
- **REST API**: Full API access for programmatic integration

## Screenshots

### Dashboard Widget
The dashboard widget shows parts requiring immediate procurement attention:
- Urgency scores with color coding
- Current stock vs recommended order quantities
- Days until stockout projections
- Quick access to generate purchase orders

### Part Analysis Panel
Detailed ROP metrics displayed on each part page:
- Current stock level vs reorder point
- Safety stock and maximum stock levels
- Demand rate analysis
- Lead time considerations
- Suggested order quantities

## Installation

### 🚨 CRITICAL: Build Frontend First!

**⚠️ YOU MUST BUILD THE FRONTEND BEFORE INSTALLING THE PLUGIN ⚠️**

The plugin **WILL NOT WORK** without building the frontend first. Pip installation may succeed, but the plugin will be completely non-functional without the static JavaScript files.

**Quick Build (Windows):**
```powershell
cd inventreeropengine\frontend
npm install
npm run build
```

Or use the automated build script:
```powershell
.\build.ps1
```

### Prerequisites
- InvenTree 0.18.0 or later
- Node.js 18+ and npm (for building the frontend)
- Python 3.9+

### Step 1: Build the Frontend (REQUIRED)

```bash
cd inventreeropengine/frontend
npm install
npm run build
```

This compiles the React/TypeScript frontend and outputs the built files to `inventree_rop_engine/static/`.

**Verify the build succeeded:**
```bash
ls -la ../inventree_rop_engine/static/
# You should see Dashboard.js, Panel.js, and Settings.js
```

### Step 2: Install the Plugin

From the plugin root directory:

```bash
pip install -e .
```

Or for production:

```bash
python -m build
pip install dist/inventree-rop-engine-*.whl
```

### Step 3: Collect Static Files

In your InvenTree installation:

```bash
invoke update
# or
python manage.py collectstatic --noinput
```

### Step 4: Run Migrations

```bash
python manage.py migrate inventree_rop_engine
```

### Step 5: Enable the Plugin

1. Navigate to Settings → Plugins in InvenTree
2. Find "ROP Suggestion Engine" in the plugin list
3. Enable the plugin

## Configuration

The plugin provides several configurable settings:

### Lookback Period (Days)
- **Default**: 90 days
- **Description**: Number of days of historical data to analyze for demand rate calculation
- Higher values provide more stable demand estimates but may not capture recent trends

### Default Service Level (%)
- **Default**: 95%
- **Description**: Target service level for safety stock calculation
- 95% means stock will be available 95% of the time during lead time

### Minimum Demand Samples
- **Default**: 5
- **Description**: Minimum number of stock removal events required before calculating ROP
- Ensures statistical significance of demand rate calculations

### Target Stock Multiplier
- **Default**: 2.0
- **Description**: Multiplier for maximum stock level calculation (e.g., 2.0 = 2x ROP)
- Controls the upper bound for inventory levels

## API Endpoints

All endpoints are prefixed with `/api/plugin/inventree-rop-engine/`

### Get All Suggestions
```
GET /api/plugin/inventree-rop-engine/suggestions/
```
Returns list of parts with active reorder suggestions, sorted by urgency.

**Query Parameters:**
- `min_urgency`: Filter by minimum urgency score (0-100)
- `limit`: Number of results to return

### Get Part ROP Details
```
GET /api/plugin/inventree-rop-engine/part/<id>/details/
```
Returns detailed ROP analysis for a specific part.

### Calculate Part ROP
```
POST /api/plugin/inventree-rop-engine/part/<id>/calculate/
```
Triggers recalculation of ROP for a specific part.

### Generate Purchase Order
```
POST /api/plugin/inventree-rop-engine/generate-po/
```
Creates a purchase order from a suggestion.

**Request Body:**
```json
{
    "suggestion_id": 123
}
```

## How It Works

### 1. Demand Rate Calculation
The engine analyzes stock removal events over the configured lookback period to calculate average daily demand rate.

### 2. Safety Stock Calculation
Based on demand variability and the configured service level, the plugin calculates appropriate safety stock levels using statistical methods.

### 3. Reorder Point Formula
```
ROP = (Demand Rate × Lead Time) + Safety Stock
```

### 4. Urgency Scoring
Parts are scored 0-100 based on:
- Current stock level vs ROP
- Days until projected stockout
- Demand rate volatility
- Lead time considerations

## Development

### Running Frontend in Development Mode

For hot-reload during development:

```bash
cd frontend
npm run dev
```

Configure InvenTree to use the development server by adding to your config:

```yaml
plugin_dev:
  slug: 'inventree-rop-engine'
  host: "http://localhost:5173"
```

### Project Structure

```
inventreeropengine/
├── frontend/                 # React/TypeScript frontend
│   ├── src/
│   │   ├── Dashboard.tsx    # Dashboard widget component
│   │   ├── Panel.tsx        # Part analysis panel component
│   │   └── Settings.tsx     # Plugin settings component
│   └── package.json
├── inventree_rop_engine/     # Python backend
│   ├── models.py            # Database models
│   ├── rop_engine.py        # ROP calculation logic
│   ├── api_views.py         # REST API views
│   ├── admin.py             # Django admin configuration
│   └── core.py              # Plugin configuration
└── pyproject.toml
```

## Database Models

### ROPPolicy
Stores per-part ROP configuration and overrides.

### DemandStats
Cached demand rate calculations and statistics.

### ROPSuggestion
Generated procurement suggestions with timestamps and status tracking.

## Troubleshooting

### Widget Not Appearing
1. Ensure the plugin is enabled in InvenTree settings
2. Verify static files were collected: `invoke update`
3. Clear browser cache
4. Check browser console for JavaScript errors

### No ROP Data Showing
1. Ensure parts have sufficient stock history (minimum samples configured)
2. Check that parts have suppliers and lead times configured
3. Verify the lookback period captures relevant data

### API Errors
1. Check InvenTree logs for backend errors
2. Verify database migrations ran successfully
3. Ensure plugin permissions are correctly configured

## License

MIT License - see LICENSE file for details

## Support

For issues, feature requests, or contributions, please visit the GitHub repository.

## Acknowledgments

Built using the InvenTree Plugin Creator tool and modern React/TypeScript stack.
