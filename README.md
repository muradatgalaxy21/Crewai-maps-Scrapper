# Maps Lead Generator — Run in Google Colab 🚀

Scrape Google Maps business leads directly from your browser using **Google Colab** — no installation required!

This is a complete, ready-to-run setup for the **Crewai Maps Scraper** project. Everything you need is included.

---

## ⚡ Quick Start (2 Minutes)

1. **Download** the files:
   - `colab_setup.ipynb` (the notebook)
   - `crewai-scraper-colab.zip` (your project code)

2. **Go to Google Colab**: https://colab.research.google.com

3. **Upload the notebook**:
   - Click `File` → `Upload notebook`
   - Select `colab_setup.ipynb`

4. **Run it**:
   - Start from the top and run each cell in order
   - When prompted, upload the ZIP file
   - Fill in your search parameters (location, business type)
   - Click "Run Scraper"
   - Download your CSV results!

That's it! ✅

---

## 📦 What's Included

| File | Purpose |
|------|---------|
| `colab_setup.ipynb` | Main notebook — run this in Colab |
| `crewai-scraper-colab.zip` | Your complete project code |
| `README.md` | This file |
| `COLAB_GUIDE.md` | Detailed guide & troubleshooting |

---

## 📋 Detailed Setup

### Step 1: Prepare Your Files

You should have:
- ✅ `colab_setup.ipynb`
- ✅ `crewai-scraper-colab.zip`

If you only have `colab_setup.ipynb`, you can create the ZIP file yourself:

```bash
python prepare_for_colab.py
```

This generates `crewai-scraper-colab.zip` automatically.

### Step 2: Open Google Colab

Go to: **https://colab.research.google.com**

### Step 3: Upload the Notebook

**Option A: Upload File**
- Click `File` → `Upload notebook`
- Select `colab_setup.ipynb`
- Wait for it to load

**Option B: Open from GitHub** (if you've uploaded to GitHub)
- Click `File` → `Open notebook`
- Go to GitHub tab
- Paste your repo URL

### Step 4: Run the Setup

Start from the top and run each cell in order:

```
Step 1: Install Dependencies
   ↓
Step 2: Install Playwright Browsers
   ↓
Step 3: Upload/Clone Your Codebase
   ↓
Step 4: Verify Structure
   ↓
Step 5: Create .env File
   ↓
Step 6: Run the Scraper
```

**Don't skip any cells!** Each one is necessary.

### Step 5: Upload Your Code

When you reach **"Step 3: Upload or Clone Your Codebase"**, you'll see three options:

**Choose ONE:**

- **Option A**: Click the upload cell and select `crewai-scraper-colab.zip`
  - Simplest method
  - Takes 30 seconds
  - Recommended ✅

- **Option B**: Use GitHub
  - Uncomment the git clone line
  - Replace with your repo URL
  - Click run
  - Best if your code is on GitHub

- **Option C**: Upload files individually
  - Click the upload cell
  - Select individual Python files
  - Notebook creates folders automatically
  - More tedious but works fine

### Step 6: Configure Your Search

Fill in the form with:
- **Target Area**: City or country name (e.g., "Paris", "New York", "Luxembourg")
- **Business Type**: What you're looking for (e.g., "Hair Salon", "Restaurant", "Coffee Shop")
- **Max Results to Display**: How many rows to show (5-100)
- **Headless Mode**: Keep this ON (required for Colab)

Example:
```
Area: "Paris"
Business: "Italian Restaurant"
Max Display: 30
```

### Step 7: Run the Scraper

Click the "Run Scraper" cell and wait. It will:
1. Find locations matching your area ✓
2. Display available locations (pick one)
3. Search Google Maps for that business type ✓
4. Extract business details (name, phone, email, website) ✓
5. Save results to CSV ✓

**Expected time**: 5-15 minutes (depends on number of results)

### Step 8: Download Results

Your CSV file is automatically saved and ready to download!

Click the download cell to get: `leads_[location]_[business].csv`

---

## 📊 What You'll Get

Your CSV includes:

| Column | Description |
|--------|-------------|
| Business Name | The business name |
| Phone | Phone number |
| Email | Email address (if found) |
| Website | Business website |
| Address | Physical address |
| Reviews | Number of reviews |
| Social Links | Social media links (if found) |

**Example output:**
```
Business Name,Phone,Email,Website,Address,Reviews,...
Joe's Hair Salon,+33 1 23 45 67 89,contact@joes.fr,joes-salon.fr,123 Rue de Paris,45 reviews,...
Betty's Cuts,+33 1 98 76 54 32,info@bettys.fr,bettyscuts.fr,456 Ave Lyon,32 reviews,...
...
```

---

## 🎯 Tips for Best Results

### Location Tips
- Use **city names** or **country names**
- Examples that work well:
  - ✅ "Paris"
  - ✅ "New York"
  - ✅ "Luxembourg"
  - ❌ "random place" (too vague)

### Business Type Tips
- Be **specific** — more specific = better results
- Good examples:
  - ✅ "Italian Restaurant"
  - ✅ "Hair Salon"
  - ✅ "Coffee Shop"
  - ❌ "Business" (too vague)
  - ❌ "Store" (too general)

### Avoid Getting Blocked
- Don't scrape the **same location** repeatedly
- Wait **15+ minutes** between different scrapes
- Try **different business types** in the same location
- If Google blocks you, wait 30 minutes and try again

### Max Results
- Small areas: 5-50 results (fast)
- Medium areas: 50-200 results (moderate)
- Large areas: 200+ results (slow, takes 15+ minutes)

---

## ⚠️ Troubleshooting

### "Module not found" Error

**Solution**: Make sure you uploaded the ZIP file in Step 3.

If you manually uploaded files, check that the structure is:
```
/content/scraper/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── tools/
│   └── orchestration/
└── requirements.txt
```

Run the "Verify structure" cell to check.

### Browser Won't Start

**Solution**: 
1. Run "Install Playwright Browsers" cell again
2. Click `Runtime` → `Restart runtime`
3. Start over from Step 1

### No Results Found

**Possible causes:**
- Location doesn't exist (try a different name)
- Business type doesn't exist there
- Google is blocking requests (wait 15 minutes)
- Area is too small (try a larger location)

**Solution**:
1. Try a different location (e.g., "Paris" instead of small suburb)
2. Try a different business type
3. Check the logs in the "Troubleshooting" section
4. Wait 15+ minutes and try again

### CAPTCHA or 403 Error

Google detected the scraper. This is normal!

**Solution**:
- Wait 30 minutes before trying again
- Try a different location/business type
- Don't hammer the same search repeatedly

The scraper will fail but continue — just wait and retry.

### Timeout or Connection Errors

Colab internet connection is unstable.

**Solution**:
1. Try again (often works on retry)
2. Reduce `MAX_SCROLL_ATTEMPTS` in the configuration
3. Try a smaller area with fewer expected results
4. Restart runtime and try again

### CSV File Not Created

Scraping failed or no results found.

**Solution**:
1. Check the cell output for error messages
2. Look at the logs in "Check logs" section
3. Try with a different location
4. Verify your area and business type are correct

---

## ❓ FAQ

**Q: Do I need to install anything on my computer?**  
A: No! Everything runs in Google Colab. You just need a Google account and the files.

**Q: Will my data be safe?**  
A: Yes. Colab runs on Google's servers. Your CSV is only saved in Colab until you download it.

**Q: Can I scrape multiple areas in one session?**  
A: Yes! Change the parameters and run the scraper again. Each CSV gets a different filename.

**Q: How long does it take?**  
A: Usually 10-20 minutes total (setup + scraping). First-time setup is slower.

**Q: Will Google block me?**  
A: Only if you scrape too much, too fast. Wait 15+ minutes between requests on the same location.

**Q: Can I run this 24/7?**  
A: Colab sessions timeout after 12 hours of inactivity or 24 hours max. You'd need to restart.

**Q: What if I want to modify the code?**  
A: The notebook loads all source files. You can edit them in Colab or modify the ZIP before uploading.

**Q: Is this legal?**  
A: Scraping public data from Google Maps is legal in most jurisdictions. Check your local laws. Use results responsibly.

**Q: Can I share this with others?**  
A: Yes! Give them the `colab_setup.ipynb` and `crewai-scraper-colab.zip` files. They can follow this README.

---

## 📚 More Information

For detailed information, see:
- **COLAB_GUIDE.md** — Full guide with advanced options
- **prepare_for_colab.py** — Script to create/update the ZIP
- **src/config.py** — Configuration options you can adjust

---

## 🔧 Advanced: Adjust Configuration

To change scraper behavior, edit the configuration in the notebook:

```python
# In "Configure Search Parameters" cell:
MAX_SCROLL_ATTEMPTS = 15  # More = slower but more results
HEADLESS_MODE = True      # Keep True for Colab
```

Or edit `.env` file:
```
MAX_SCROLL_ATTEMPTS=20
MAX_TOTAL_SCROLLS=500
```

---

## ✅ What You Should See

After successful scraping:

```
🔍 SCRAPER CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location:    Paris, France
Business:    Hair Salon
Output:      /content/scraper/csv/leads_paris_hair_salon.csv
Headless:    True
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starting scraper...

[Browser opens, scrolls through results...]

✓ Scraping complete! Found 47 results.

📊 RESULTS TABLE (showing first 20 of 47 records)

[Table with business data]

✓ COMPLETE: 47 leads saved to /content/scraper/csv/leads_paris_hair_salon.csv
```

Then click the download button to get your CSV! 📥

---

## 🚀 Next Steps After Scraping

1. **Download the CSV** using the download cell
2. **Open in Excel/Sheets** to view and organize
3. **Filter & sort** by reviews, phone number, etc.
4. **Export to CRM** or email software
5. **Contact the leads** 📧

---

## 📞 Need Help?

1. **Check COLAB_GUIDE.md** — Has detailed troubleshooting
2. **Review cell outputs** — Error messages are usually helpful
3. **Check logs** — Click "Check logs" cell to see detailed errors
4. **Try different search terms** — Sometimes simple fixes work

---

## 📝 License & Attribution

This is the **Crewai Maps Scraper** adapted for Google Colab.

Uses:
- **Playwright** — Browser automation
- **Geopy/Nominatim** — Location discovery
- **Pydantic** — Configuration
- **Rich** — Pretty terminal output

All open source and free to use!

---

**Happy scraping! 🎉**

Questions? Check COLAB_GUIDE.md for more detailed information.
