# Running the Maps Lead Generator in Google Colab

This guide explains how to run your Crewai Maps Scrapper codebase in Google Colab.

## Quick Start

### Option 1: Upload to Colab (Easiest)

1. **Open Colab**: Go to [colab.research.google.com](https://colab.research.google.com)
2. **Upload Notebook**: Click `File` → `Upload notebook` → Select `colab_setup.ipynb` from this folder
3. **Run Cells in Order**: Execute each cell from top to bottom
4. **Upload Your Code**: When prompted, upload your project files (or skip if using GitHub)
5. **Configure & Run**: Fill in your search parameters and run the scraper

### Option 2: Clone from GitHub (Automated)

1. **Create a GitHub repository** with your code
2. **Open the notebook** in Colab
3. **Uncomment the GitHub clone line** in "Option B: Clone from GitHub" cell
4. **Replace the URL** with your repository link
5. **Run the cell** - your code will be automatically downloaded

### Option 3: Direct Upload from Colab

1. **Open colab_setup.ipynb** in Colab
2. **Run setup cells** (Steps 1-3)
3. **Use the file upload cell** - it will prompt you to select files
4. **Drag & drop your files** or select them from your computer

## Notebook Sections Explained

| Section | Purpose |
|---------|---------|
| **Step 1-2** | Install Python packages and Playwright browser |
| **Step 3** | Upload or clone your codebase |
| **Step 4-5** | Verify structure and create .env config |
| **Step 6** | Main execution section with interactive inputs |
| **Configure Search** | Set target area, business type, display options |
| **Start Discovery** | Find available locations matching your search |
| **Select Location** | Choose which location to scrape from the list |
| **Run Scraper** | Execute the actual scraping (takes several minutes) |
| **View Results** | Display results in a table format |
| **Download Results** | Save CSV file to your computer |
| **Troubleshooting** | Diagnose and view logs if something fails |

## File Structure Expected

Your uploaded files should match this structure:

```
scraper/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── pipeline.py
│   └── tools/
│       ├── __init__.py
│       ├── location_api.py
│       └── playwright_bot.py
├── requirements.txt
└── .env (optional, auto-created)
```

If you're uploading individual files, the notebook will help you create this structure.

## Important Notes

### Colab Limitations & Solutions

| Issue | Solution |
|-------|----------|
| **Browser crashes** | Reduce `max_scroll_attempts` in config cells |
| **Timeout errors** | Try scraping smaller areas first |
| **Google blocking** | Wait 15+ minutes before retrying same location |
| **Memory issues** | Run only one scrape per Colab session |
| **File uploads slow** | Use GitHub clone instead if repo is available |

### Configuration Tips

- **HEADLESS_MODE**: Always use `True` in Colab (required for browser automation)
- **TARGET_AREA**: Works best with city/country names (e.g., "Paris", "Brooklyn")
- **BUSINESS_TYPE**: Be specific (e.g., "Italian Restaurant" works better than "Restaurant")
- **MAX_DISPLAY**: Set to 20-50 for reasonable table display in the notebook

## Troubleshooting Steps

### 1. ImportError: Module not found
```
✓ Make sure all files are in /content/scraper/src/
✓ Verify __init__.py exists in each folder
✓ Re-run the "Create src folder structure" cell
```

### 2. Playwright browser won't start
```
✓ Run "Install Playwright Browsers" cell again
✓ Ensure you're in headless mode
✓ Try restarting the runtime (Runtime → Restart runtime)
```

### 3. No results found
```
✓ Check if Google is blocking the IP (try waiting 15 mins)
✓ Try a different location or business type
✓ Verify your internet connection is stable
✓ Check the logs in the Troubleshooting section
```

### 4. CAPTCHA or 403 errors
```
✓ Google has detected the scraper - this is normal after multiple requests
✓ Wait 15-30 minutes before trying again
✓ Try a different location/business type
✓ Consider using a VPN service (external to Colab)
```

## Tips for Best Results

1. **Start small**: Test with a major city first (e.g., "Luxembourg", "Paris")
2. **Use specific business types**: "Hair Salon" finds more results than "Salon"
3. **Run during off-peak hours**: Lower chance of Google blocking your requests
4. **Don't run multiple scrapes back-to-back**: Wait 10+ minutes between searches
5. **Monitor logs**: Check the "Check logs" cell if something seems wrong

## Advanced: Running Multiple Scrapes

To scrape multiple locations in one session:

1. Complete one full scrape
2. **Change parameters** in the "Configure Search Parameters" cell
3. **Re-run from "Start Location Discovery"** onwards
4. **Files will auto-save** with different names (location + business type)

Each CSV will be saved separately and ready to download.

## Performance Expectations

- **Setup**: 2-3 minutes (first time only)
- **Location discovery**: 10-20 seconds
- **Scraping**: 5-15 minutes (depends on number of results and scrolling)
- **Results processing**: 1-2 seconds

**Total typical time**: 10-20 minutes per scrape

## Getting Help

- **Review the logs**: Check the Troubleshooting section's log viewer
- **Check Colab console**: Look for error messages in the cell output
- **Try a simpler search**: Retry with a different location or business type
- **Restart Colab**: Runtime → Restart runtime (clears all state)

## Data Output

Your CSV files will contain:
- Business name
- Phone number
- Email address (if found)
- Website URL
- Physical address
- Review count
- Social media links
- Other business info

Files are saved to: `/content/scraper/csv/leads_*.csv`

Download them directly from the notebook using the download cell!
