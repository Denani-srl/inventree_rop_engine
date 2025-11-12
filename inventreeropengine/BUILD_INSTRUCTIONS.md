# Build Instructions for InvenTree ROP Engine

## Important: Build Frontend BEFORE Installing Plugin

The plugin installation will fail if the frontend has not been built first, because pip expects the static files to exist.

## Step-by-Step Build Process

### 1. Build the Frontend

```bash
cd inventreeropengine/frontend
npm install
npm run build
```

This will:
- Install all Node.js dependencies
- Compile the React/TypeScript code
- Output the built files to `../inventree_rop_engine/static/`

**Verify the build succeeded:**
```bash
ls -la ../inventree_rop_engine/static/
# You should see Dashboard.js, Panel.js, and Settings.js
```

### 2. Install the Plugin

#### Development Installation (recommended for testing)

```bash
cd ..  # Back to inventreeropengine/ directory
pip install -e .
```

#### Production Build and Install

```bash
cd ..  # Back to inventreeropengine/ directory
python -m build
pip install dist/inventree_rop_engine-*.whl
```

### 3. Configure InvenTree

Add to your InvenTree configuration:

**For development mode with hot-reload:**
```yaml
plugin_dev:
  slug: 'inventree-rop-engine'
  host: "http://localhost:5173"
```

Then run the frontend dev server:
```bash
cd frontend
npm run dev
```

**For production:**
Just ensure the plugin is enabled in InvenTree's plugin settings.

### 4. Collect Static Files in InvenTree

```bash
# In your InvenTree installation directory
invoke update
# or
python manage.py collectstatic --noinput
```

### 5. Run Database Migrations

```bash
python manage.py migrate inventree_rop_engine
```

### 6. Restart InvenTree Server

Restart your InvenTree server to load the plugin.

### 7. Enable the Plugin

1. Navigate to **Settings → Plugins** in InvenTree
2. Find **"ROP Suggestion Engine"** in the plugin list
3. Click **Enable**

## Troubleshooting

### Error: "cannot access 'inventree_rop_engine/static/'"

**Cause:** Frontend has not been built yet.

**Solution:** Run `npm run build` in the `frontend/` directory first.

### Error: "Module not found" or import errors

**Cause:** Missing dependencies.

**Solution:**
```bash
cd frontend
npm install
```

### Plugin not appearing in InvenTree

**Cause:** Static files not collected or plugin not enabled.

**Solution:**
1. Run `invoke update` in InvenTree
2. Check that the plugin is enabled in Settings
3. Clear browser cache

### Widget shows "null" or loading errors

**Cause:** API endpoints not accessible or frontend build issue.

**Solution:**
1. Check InvenTree logs for backend errors
2. Verify the frontend built correctly
3. Check browser console for JavaScript errors
4. Ensure migrations ran successfully

## Quick Reference

### Full Build & Install Workflow

```bash
# 1. Build frontend
cd inventreeropengine/frontend
npm install
npm run build

# 2. Install plugin
cd ..
pip install -e .

# 3. In InvenTree installation
invoke update
python manage.py migrate inventree_rop_engine

# 4. Restart InvenTree server
# Then enable in Settings → Plugins
```

### Rebuild After Code Changes

If you modify the frontend code:
```bash
cd inventreeropengine/frontend
npm run build
cd ../../<inventree-dir>
invoke update  # Recollect static files
```

If you modify the backend code and using `-e` install:
```bash
# Changes are automatically picked up
# Just restart InvenTree server
```

## Development Tips

- Use `npm run dev` in development for hot-reload
- Use `-e` (editable) install for backend development
- Check `frontend/dist/` to verify build output
- Monitor InvenTree logs for backend errors
- Use browser DevTools console for frontend errors
