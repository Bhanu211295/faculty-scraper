"""
Streamlit web app for faculty scraper.
Run locally with: streamlit run streamlit_app.py
Deploy to Streamlit Cloud automatically from GitHub.
"""

import streamlit as st
import threading
import time
from io import StringIO
import csv
from datetime import datetime

from fetcher import Fetcher
from extractor import get_extractor, FacultyRecord

st.set_page_config(
    page_title="Faculty Data Scraper",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom theme/styling
st.markdown("""
<style>
    .main {
        max-width: 700px;
        margin: auto;
    }
    .stButton > button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border-left: 4px solid #f5222d;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Faculty Data Scraper")
st.markdown("Extract faculty information from university websites — no coding required")

# Initialize session state
if "job_running" not in st.session_state:
    st.session_state.job_running = False
if "records" not in st.session_state:
    st.session_state.records = []
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None
if "status_msg" not in st.session_state:
    st.session_state.status_msg = ""
if "progress" not in st.session_state:
    st.session_state.progress = 0

# Sidebar with info
with st.sidebar:
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. Enter the university name
    2. Paste the faculty listing URL
    3. Choose an AI provider (free options available)
    4. Click "Start Scraping"
    5. Download results as CSV
    
    **Need an API key?**
    - [Gemini (free)](https://aistudio.google.com/apikey)
    - [Groq (free)](https://console.groq.com)
    - [Anthropic (free credits)](https://console.anthropic.com)
    """)

# Main form
if not st.session_state.job_running:
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        university = st.text_input(
            "University Name *",
            placeholder="e.g., DTU, IIT Delhi",
            help="A label to identify this university in your data"
        )
    with col2:
        provider = st.selectbox(
            "AI Provider",
            ["gemini", "groq", "anthropic"],
            help="Choose which AI service to use"
        )
    
    url = st.text_input(
        "Faculty Listing URL *",
        placeholder="https://dtu.ac.in/Web/Departments/Environment/faculty_v2/",
        help="The main faculty/staff page URL you want to scrape"
    )
    
    deep_mode = st.checkbox(
        "🔍 Use 'Deep Mode' (click each profile for details)",
        help="Enable this if the site builds profile links dynamically. Slower but more thorough."
    )
    
    st.markdown("---")
    
    if st.button("🚀 Start Scraping", type="primary"):
        if not university or not url:
            st.error("❌ Please enter both university name and URL")
        else:
            st.session_state.job_running = True
            st.session_state.records = []
            st.session_state.error_msg = None
            st.rerun()

else:
    # Job is running - show progress
    st.markdown("---")
    st.markdown("### 🔄 Scraping in Progress...")
    
    progress_container = st.empty()
    status_container = st.empty()
    record_count_container = st.empty()
    error_container = st.empty()
    
    def run_scrape(univ, url_to_scrape, prov, use_deep):
        try:
            status_container.info(f"🔍 Initializing scraper for {univ}...")
            
            fetcher = Fetcher(headless=True, respect_robots=False)
            extractor = get_extractor(prov)
            
            try:
                # Fetch the page
                status_container.info("📥 Fetching listing page...")
                progress_container.progress(20)
                page = fetcher.fetch(url_to_scrape)
                
                # Initialize click_links (will be populated if deep_mode is on)
                click_links = []
                
                # Deep mode: click to discover URLs
                if use_deep:
                    status_container.info("🖱️ Discovering profile URLs via clicks...")
                    progress_container.progress(40)
                    click_links = fetcher.discover_click_targets(url_to_scrape)
                    existing_hrefs = {l["href"] for l in page["links"]}
                    for l in click_links:
                        if l["href"] not in existing_hrefs:
                            page["links"].append(l)
                            existing_hrefs.add(l["href"])
                
                # Classify the page
                status_container.info("🤖 Analyzing page structure...")
                progress_container.progress(50)
                analysis = extractor.analyze_listing_page(page["url"], page["text"], page["links"])
                page_type = analysis.get("page_type")
                
                # Override if deep mode found links
                if use_deep and click_links and page_type != "detail_links":
                    page_type = "detail_links"
                    analysis = {"page_type": "detail_links", "profiles": click_links}
                
                records = []
                
                if page_type == "full_records":
                    # All records on one page
                    status_container.info("📋 Extracting records from page...")
                    progress_container.progress(70)
                    for r in analysis.get("records", []):
                        rec = FacultyRecord(source_university=univ, source_url=url_to_scrape)
                        for k in ["name", "designation", "department", "qualification", "specialization", "email", "phone", "photo_url", "bio"]:
                            setattr(rec, k, r.get(k))
                        records.append(rec)
                
                elif page_type == "detail_links":
                    # Need to visit each profile
                    profiles = analysis.get("profiles", [])
                    status_container.info(f"👤 Visiting {len(profiles)} profile pages...")
                    
                    for i, p in enumerate(profiles, 1):
                        purl = p.get("url")
                        if not purl:
                            continue
                        try:
                            progress = 70 + int((i / len(profiles)) * 25)
                            progress_container.progress(progress)
                            record_count_container.metric("Extracted Records", len(records))
                            
                            detail_page = fetcher.fetch(purl)
                            data = extractor.extract_detail_page(purl, detail_page["text"])
                            data["profile_url"] = purl
                            rec = FacultyRecord(source_university=univ, source_url=url_to_scrape)
                            for k in ["name", "designation", "department", "qualification", "specialization", "email", "phone", "photo_url", "bio", "profile_url"]:
                                setattr(rec, k, data.get(k))
                            rec.extraction_confidence = data.get("extraction_confidence")
                            records.append(rec)
                        except Exception as e:
                            pass  # skip this profile and move on
                
                else:
                    reason = analysis.get("reason", "Unknown")
                    raise Exception(f"Could not identify page type: {reason}")
                
                fetcher.close()
                
                if not records:
                    raise Exception("No records extracted from the page.")
                
                # Deduplicate
                seen = {}
                deduped = []
                for r in records:
                    key = (r.name, r.email)
                    if key not in seen:
                        seen[key] = True
                        deduped.append(r)
                
                st.session_state.records = deduped
                progress_container.progress(100)
                status_container.success(f"✅ Success! Extracted {len(deduped)} records.")
                
            except Exception as e:
                fetcher.close()
                raise e
        
        except Exception as e:
            st.session_state.error_msg = str(e)
            error_container.error(f"❌ Error: {str(e)}")
            status_container.empty()
            progress_container.empty()
    
    # Run the scrape
    run_scrape(university, url, provider, deep_mode)
    
    st.markdown("---")
    
    if st.session_state.error_msg:
        st.markdown(f"""
        <div class="error-box">
        <strong>Error during scraping:</strong><br>
        {st.session_state.error_msg}
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.records:
        st.markdown(f"""
        <div class="success-box">
        <strong>Success!</strong> Extracted <strong>{len(st.session_state.records)}</strong> faculty records.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📥 Download Your Data")
        
        # Convert records to CSV
        output = StringIO()
        fieldnames = [
            "source_university",
            "source_url",
            "name",
            "designation",
            "department",
            "qualification",
            "specialization",
            "email",
            "phone",
            "photo_url",
            "bio",
            "profile_url",
            "extraction_confidence",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([r.to_dict() for r in st.session_state.records])
        
        csv_data = output.getvalue()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"faculty_data_{timestamp}.csv",
            mime="text/csv",
            type="primary"
        )
        
        st.markdown("---")
        
        # Show preview
        with st.expander("👀 Preview Data", expanded=False):
            st.dataframe(
                [r.to_dict() for r in st.session_state.records[:10]],
                use_container_width=True,
                height=400
            )
    
    if st.button("🔄 Start Over"):
        st.session_state.job_running = False
        st.session_state.records = []
        st.session_state.error_msg = None
        st.rerun()
