# Deploy Advanced Streamlit App to Railway.app

**Why Railway instead of Streamlit Cloud?**
- ✅ Full Playwright support (scrolling, pagination, clicking)
- ✅ Better network access to Indian universities
- ✅ No SSL certificate issues
- ✅ Free tier available
- ✅ Same Streamlit interface you already know

---

## Step-by-Step Deployment

### Step 1: Update GitHub with Advanced Files

Your GitHub repo needs these files:

**Update on GitHub:**
- `streamlit_app_advanced.py` ← Use this instead of `streamlit_app.py`
- `fetcher_advanced.py` ← New file
- `requirements.txt` ← Updated (includes Playwright)

**Keep these unchanged:**
- `extractor.py`
- `app.py`
- Other config files

### How to Update:

1. Go to: **https://github.com/Bhanu211295/faculty-scraper**

2. **Upload/Replace these files:**
   - Click **Add file** → **Upload files**
   - Upload `streamlit_app_advanced.py`, `fetcher_advanced.py`
   - Click **Commit changes**

3. **Update requirements.txt:**
   - Click on **requirements.txt**
   - Click **pencil icon** ✏️
   - Delete everything
   - Paste the new requirements (with Playwright included)
   - Click **Commit changes**

4. **Delete old file (optional):**
   - Click on `streamlit_app.py`
   - Click **three dots** (⋯) → **Delete**
   - Click **Commit changes**

---

### Step 2: Sign Up for Railway.app

1. Go to: **https://railway.app/**
2. Click **Start Project**
3. Sign in with **GitHub** (same account as your faculty-scraper repo)
4. Authorize Railway to access your GitHub

---

### Step 3: Create a New Project on Railway

1. On Railway dashboard, click **+ New Project**
2. Select **Deploy from GitHub repo**
3. Find and select **faculty-scraper** repo
4. Railway auto-detects it's Python/Streamlit
5. Click **Deploy**

Railway will start building (takes 2-3 minutes first time).

---

### Step 4: Add Environment Variables (API Key)

1. Once the build finishes, click on your project
2. Click on the **Deployment** (or **Settings**)
3. Look for **Variables** or **Env** section
4. Add a new variable:
   - **Name:** `GEMINI_API_KEY`
   - **Value:** `AQ.Ab8RN6L12WjwK2JttwccquKH9dAMu7SUI4iy3eZ-X90tzw7fAMA`
5. Click **Save**

Railway will auto-redeploy with the new variable.

---

### Step 5: Get Your Public URL

1. Go to your project on Railway
2. Click on the Streamlit service
3. Look for **Public URL** (should look like `https://your-app-xxxxx.railway.app`)
4. **That's your live app URL!**

---

## Testing Your App

1. Open your Railway app URL
2. Fill in:
   - **University:** `SASTRA`
   - **Faculty URL:** `https://www.sastra.edu/staffprofiles/schools/mech.php`
   - **Provider:** `gemini`
   - ✅ Check: Scrolling, Pagination, Profiles
3. Click **🚀 Start Scraping**

This should extract **all 56+ records** (not just 22)!

---

## Comparison: Streamlit Cloud vs Railway

| Feature | Streamlit Cloud | Railway.app |
|---------|---|---|
| **Cost** | Free | Free (with limits) |
| **Playwright** | ❌ No | ✅ Yes |
| **Scrolling** | ❌ No | ✅ Yes |
| **Pagination** | ❌ No | ✅ Yes |
| **Profile clicking** | ❌ No | ✅ Yes |
| **Indian university access** | ⚠️ Limited | ✅ Good |
| **Setup time** | 5 min | 10 min |
| **Browser support** | HTTP only | Full browser |

---

## File Structure on GitHub

After updates, your repo should have:

```
faculty-scraper/
├── streamlit_app_advanced.py    ← Use this
├── fetcher_advanced.py           ← New
├── extractor.py
├── requirements.txt              ← Updated
├── app.py
├── fetcher.py
├── scrape.py
├── scrape_advanced.py
└── ... (other files)
```

---

## Railway Free Tier Limits

Railway gives you free credits (about $5/month equivalent):
- 🔵 Enough for testing
- 🟡 Might run out if you scrape 100+ universities per month
- 🟢 Upgrade to paid if you need more

For heavy scraping, either:
1. Scrape in batches (spread across the month)
2. Use Railway's paid plan ($5-20/month)
3. Fall back to local command-line version

---

## Troubleshooting Railway Deployment

### "Build failed"
- Check that `requirements.txt` has `playwright>=1.45.0`
- Check that `streamlit_app_advanced.py` and `fetcher_advanced.py` are on GitHub

### "App crashes after deploy"
- Check Railway logs (click project → Deployment → Logs)
- Make sure `GEMINI_API_KEY` is set in Variables
- Restart the deployment (click Redeploy)

### "Playwright errors"
- Railway should auto-install browsers, but if not, the logs will show
- Check that you're using `streamlit_app_advanced.py` (not the old `streamlit_app.py`)

### "Slow performance / timeouts"
- Free tier has limited resources
- Try reducing scrolls/profiles limits in `fetcher_advanced.py`
- Consider upgrading to paid tier

---

## Next Steps

Once deployed and working:

1. **Scrape multiple universities:**
   - Create a master list of university URLs
   - Scrape each one, saving to CSV
   - Combine all CSVs into one master file

2. **Automate with scripts:**
   ```bash
   python scrape_advanced.py --university "University1" --url "..." --out uni1.csv --with-scrolling --with-pagination --with-profiles
   python scrape_advanced.py --university "University2" --url "..." --out uni2.csv --with-scrolling --with-pagination --with-profiles
   # Combine CSVs
   ```

3. **Backup:**
   - Download your CSVs regularly
   - Save to a safe location

---

## Comparison: When to Use Which Tool

| Task | Use This |
|------|----------|
| **Share with non-technical users** | Web app (Railway) |
| **Bulk scraping (many universities)** | Local `scrape_advanced.py` |
| **Quick test of a site** | Web app (Railway) |
| **Production/scheduled scraping** | Local script (cron job) |
| **Scraping Indian universities** | Local or Railway (both work) |

---

## Questions?

1. **"Which URL should I use?"**
   - Use the Railway public URL, not localhost

2. **"My API key stopped working"**
   - Regenerate a new key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   - Update in Railway Variables

3. **"Still only getting 22 records, not 56"**
   - Make sure ✅ Scrolling, ✅ Pagination, ✅ Profiles are checked
   - Check Railway logs for errors

4. **"How do I stop/pause the app?"**
   - Go to Railway → Project Settings → Pause Deployment
   - This saves credits

---

You're all set! Deploy to Railway and enjoy the advanced features! 🚀
