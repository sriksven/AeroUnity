# Streamlit Web UI Deployment Guide

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Locally

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Streamlit Cloud Deployment

### 1. Prerequisites

- GitHub repository (already have: https://github.com/sriksven/AeroUnity)
- Streamlit Cloud account (free): https://streamlit.io/cloud

### 2. Deployment Steps

1. **Sign up for Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub

2. **Create New App**
   - Click "New app"
   - Repository: `sriksven/AeroUnity`
   - Branch: `main`
   - Main file path: `app.py`

3. **Deploy**
   - Click "Deploy!"
   - Streamlit will automatically install dependencies from `requirements.txt`
   - App will be live at: `https://aerounity.streamlit.app` (or similar)

### 3. Configuration

The app uses `.streamlit/config.toml` for:
- Custom theme (purple gradient matching AeroUnity branding)
- Server settings
- Port configuration

## Features

### Aircraft Mission Planning
- Configure waypoints, wind, battery, obstacles
- Real-time mission planning with OR-Tools
- Results display with metrics
- Route visualization

### Spacecraft Mission Planning
- Configure orbit parameters (altitude, inclination)
- Select orbit types (sun-sync, polar, LEO)
- Schedule observations over 7 days
- Science value optimization

### Interactive Controls
- Sliders for all parameters
- Advanced settings expandable sections
- Real-time validation
- Results download (JSON)

## App Structure

```
app.py                  # Main Streamlit application
.streamlit/
  └── config.toml      # Streamlit configuration
requirements.txt       # Python dependencies
```

## Customization

### Theme Colors

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"  # Purple gradient
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

### Add More Features

The app is modular - you can add:
- Real-time plot generation
- CSV/JSON export buttons
- Mission comparison tools
- Historical mission gallery

## Troubleshooting

### Import Errors

If you get import errors, ensure all dependencies are in `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### Memory Issues

Streamlit Cloud has memory limits. For large computations:
- Use `@st.cache_data` decorator
- Limit visualization sizes
- Optimize data structures

### Deployment Fails

Check:
- `requirements.txt` is up to date
- `app.py` has no syntax errors
- All imports are available on PyPI

## Live Demo

Once deployed, share the URL:
- **Live App:** https://aerounity.streamlit.app
- **GitHub:** https://github.com/sriksven/AeroUnity
- **Devpost:** [Your Devpost link]

## Next Steps

1. Test locally: `streamlit run app.py`
2. Push to GitHub: `git push origin main`
3. Deploy on Streamlit Cloud
4. Add URL to README and Devpost

---

**Note:** The current app uses simplified planning logic for demo purposes. For full validation results, run:

```bash
python run_complete_validation.py
```

This generates all plots and detailed metrics in the `outputs/` directory.
