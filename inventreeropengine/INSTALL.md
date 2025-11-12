# Installation Instructions for ROP Engine Plugin

## ⚠️ CRITICAL: Build Frontend First!

The plugin **WILL NOT WORK** without building the frontend first. The static JavaScript files are required for the dashboard widgets and panels to function.

## Step 1: Build Frontend (Windows - Current Machine)

```powershell
# Navigate to frontend directory
cd C:\Users\Oscar\repo\inventree_rop_engine\inventreeropengine\frontend

# Install dependencies
npm install

# Build the frontend
npm run build

# Verify build succeeded - you should see Dashboard.js, Panel.js, Settings.js
dir ..\inventree_rop_engine\static\
```

## Step 2: Commit and Push Built Files

```powershell
cd C:\Users\Oscar\repo\inventree_rop_engine\inventreeropengine

git add inventree_rop_engine/static/
git commit -m "Add built frontend static files"
git push
```

## Step 3: Pull Changes on Server (Linux/WSL)

```bash
cd /home/ohzak/inventree_rop_engine
git pull
```

## Step 4: Install Plugin on InvenTree Server

```bash
# Switch to inventree user and activate virtual environment
sudo su - inventree

# Navigate to InvenTree directory and activate environment
cd /opt/inventree
source env/bin/activate

# Navigate to plugin directory and install in editable mode
cd /home/ohzak/inventree_rop_engine/inventreeropengine
pip install -e .

# Verify installation
pip list | grep inventree-rop-engine
```

## Step 5: Run Database Migrations

```bash
# Still as inventree user with venv activated
cd /opt/inventree
python manage.py migrate inventree_rop_engine
```

## Step 6: Collect Static Files

```bash
# Still as inventree user with venv activated
cd /opt/inventree
python manage.py collectstatic --noinput
```

## Step 7: Restart InvenTree

```bash
# Exit from inventree user
exit

# Restart InvenTree service (as your regular user)
sudo systemctl restart inventree
# Or if using invoke:
# cd /opt/inventree && invoke restart
```

## Step 8: Enable Plugin in InvenTree

1. Open InvenTree web interface
2. Navigate to **Settings → Plugins**
3. Find "ROP Suggestion Engine" in the list
4. Click to enable the plugin
5. Configure settings if needed:
   - Lookback Period (Days): 90
   - Default Service Level (%): 95
   - Minimum Demand Samples: 5
   - Target Stock Multiplier: 2.0

## Step 9: Verify Installation

### Test API Endpoint
```bash
curl http://localhost:8000/api/plugin/inventree-rop-engine/test/
```

Expected response:
```json
{
    "status": "ok",
    "message": "ROP Engine plugin is working",
    "plugin": "inventree-rop-engine",
    "version": "0.1.0"
}
```

### Check Dashboard Widget
1. Go to InvenTree dashboard
2. You should see "Urgent Reorder Suggestions" widget

### Check Part Panel
1. Navigate to any part detail page
2. You should see "ROP Analysis" panel

## Troubleshooting

### Frontend Not Built
**Error**: `Could not find a version that satisfies the requirement` or static files missing

**Solution**: You MUST build the frontend first (see Step 1)

### Plugin Not Found After Install
**Error**: `No installed app with label 'inventree_rop_engine'`

**Solution**: Make sure you ran `pip install -e .` from the correct directory

### Widgets Not Appearing
**Solution**:
1. Run `python manage.py collectstatic --noinput`
2. Restart InvenTree service
3. Clear browser cache
4. Check browser console for errors

### API Returns 404
**Solution**:
1. Verify plugin is enabled in InvenTree settings
2. Check plugin is installed: `pip list | grep inventree-rop-engine`
3. Verify migrations ran: `python manage.py showmigrations inventree_rop_engine`

## Development Mode

For development with hot-reload:

```bash
cd frontend
npm run dev
```

Add to InvenTree config:
```yaml
plugin_dev:
  slug: 'inventree-rop-engine'
  host: "http://localhost:5173"
```
