# Quick Start - Build and Install ROP Engine Plugin

## Current Status
- ✅ Plugin code structure is ready
- ✅ React/TypeScript components are implemented
- ❌ Frontend NOT built yet (CRITICAL - must do this first!)
- ❌ Plugin NOT installed on server yet

## What You Need To Do NOW

### 1️⃣ Build Frontend (On Windows - This Machine)

Open PowerShell in this directory and run:

```powershell
cd inventreeropengine\frontend
npm install
npm run build
```

**Expected output:**
```
✓ built in XXXms
✓ compiled with warnings
```

**Verify build succeeded:**
```powershell
dir ..\inventree_rop_engine\static\
```

You should see:
- `Dashboard.js`
- `Panel.js`
- `Settings.js`
- `assets\` folder with CSS files

### 2️⃣ Commit and Push

```powershell
cd ..
git add inventree_rop_engine\static\
git status
git commit -m "Add built frontend static files"
git push
```

### 3️⃣ Install on Server (On Linux Server via SSH)

```bash
# Pull the changes with built files
cd /home/ohzak/inventree_rop_engine
git pull

# Switch to inventree user
sudo su - inventree

# Activate venv and navigate
cd /opt/inventree
source env/bin/activate

# Install plugin in editable mode
cd /home/ohzak/inventree_rop_engine/inventreeropengine
pip install -e .

# Run migrations
cd /opt/inventree
python manage.py migrate inventree_rop_engine

# Collect static files
python manage.py collectstatic --noinput

# Exit from inventree user
exit

# Restart InvenTree
sudo systemctl restart inventree
```

### 4️⃣ Enable Plugin in InvenTree Web UI

1. Open InvenTree in browser
2. Go to **Settings → Plugins**
3. Find "ROP Suggestion Engine"
4. Enable it
5. Configure settings (defaults are fine to start)

### 5️⃣ Test It Works

**Test API:**
```bash
curl http://localhost:8000/api/plugin/inventree-rop-engine/test/
```

Should return:
```json
{"status": "ok", "message": "ROP Engine plugin is working"}
```

**Check Dashboard:**
- Open InvenTree dashboard
- Look for "Urgent Reorder Suggestions" widget

**Check Part Page:**
- Go to any part detail page
- Look for "ROP Analysis" panel

---

## If You Get Errors

### "Could not find a version" or "is not a valid editable requirement"
→ Frontend not built yet - do Step 1 first!

### "No installed app with label 'inventree_rop_engine'"
→ Plugin not installed - do Step 3 first!

### Widgets not showing
→ Run `collectstatic` and restart InvenTree

### API returns 404
→ Plugin not enabled in Settings → Plugins

---

## Ready to Start?

**Run this command NOW to build the frontend:**

```powershell
cd C:\Users\Oscar\repo\inventree_rop_engine\inventreeropengine\frontend
npm install
npm run build
```
