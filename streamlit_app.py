"""
Streamlit web app for faculty scraper - FIXED VERSION
"""

import streamlit as st
from io import StringIO
import csv
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from extractor import get_extractor, FacultyRecord

st.set_page_config(
    page_title="Faculty Data Scraper",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main {
        max-width: 700px;
        margin: auto;
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
if "success" not in st.session_state:
    st.session_state.success = False

# Sidebar info
with st.sidebar:
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. Enter university name
    2. Paste faculty listing URL
    3. Pick an AI provider
    4. Click "Start Scraping"
    5. Download CSV
    
    **Free API Keys:**
    - [Gemini](https://aistudio.google.com/apikey)
    - [Groq](https://console.groq.com)
    """)

# Form section
if not st.session_state.job_running:
    st.markdown("---")
    
    with st.form("scrape_form"):
        university = st.text_input(
            "University Name *",
            placeholder="e.g., DTU, IIT Delhi",
            help="Label for this university"
        )
        
        url = st.text_input(
            "Faculty Listing URL *",
            placeholder="https://dtu.ac.in/Web/Departments/Environment/faculty_v2/",
            help="Main faculty/staff page URL"
        )
        
        provider = st.selectbox(
            "AI Provider",
            ["gemini", "groq", "anthropic"],
            help="Which AI service to use"
        )
        
        submitted = st.form_submit_button("🚀 Start Scraping", type="primary", use_container_width=True)
        
        if submitted:
            if not university or not url:
                st.error("❌ Please enter both university name and URL")
            else:
                st.session_state.job_running = True
                st.session_state.university = university
                st.session_state.url = url
                st.session_state.provider = provider
                st.session_state.records = []
                st.session_state.error_msg = None
                st.session_state.success = False
                st.rerun()

else:
    # Job running - show progress and results
    st.markdown("---")
    st.markdown("### 🔄 Scraping in Progress...")
    
    progress_container = st.empty()
    status_container = st.empty()
    record_count_container = st.empty()
    error_container = st.empty()
    
    try:
        progress_container.progress(10)
        status_container.info("🔍 Initializing scraper...")
        
        extractor = get_extractor(st.session_state.provider)
        
        # Fetch page
        progress_container.progress(20)
        status_container.info("📥 Fetching listing page...")
        try:
            resp = requests.get(st.session_state.url, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Extract text and links
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("http://", "https://")):
                    links.append({"text": a.get_text(strip=True), "href": href})
            
            page = {"url": st.session_state.url, "text": text, "links": links}
        except Exception as e:
            raise Exception(f"Failed to fetch page: {e}")
        
        # Analyze page
        progress_container.progress(50)
        status_container.info("🤖 Analyzing page structure...")
        analysis = extractor.analyze_listing_page(page["url"], page["text"], page["links"])
        page_type = analysis.get("page_type")
        
        records = []
        
        if page_type == "full_records":
            # Extract records directly from page
            progress_container.progress(70)
            status_container.info("📋 Extracting records from page...")
            for r in analysis.get("records", []):
                rec = FacultyRecord(
                    source_university=st.session_state.university,
                    source_url=st.session_state.url
                )
                for k in ["name", "designation", "department", "qualification", "specialization", "email", "phone", "photo_url", "bio"]:
                    setattr(rec, k, r.get(k))
                records.append(rec)
        
        elif page_type == "detail_links":
            # Visit individual profiles
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
                    
                    # Fetch detail page with requests
                    resp = requests.get(purl, timeout=10)
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    for tag in soup(["script", "style", "noscript"]):
                        tag.decompose()
                    detail_text = soup.get_text(separator="\n", strip=True)
                    
                    data = extractor.extract_detail_page(purl, detail_text)
                    data["profile_url"] = purl
                    
                    rec = FacultyRecord(
                        source_university=st.session_state.university,
                        source_url=st.session_state.url
                    )
                    for k in ["name", "designation", "department", "qualification", "specialization", "email", "phone", "photo_url", "bio", "profile_url"]:
                        setattr(rec, k, data.get(k))
                    rec.extraction_confidence = data.get("extraction_confidence")
                    records.append(rec)
                
                except Exception as e:
                    pass  # Skip this profile and move on
        
        else:
            raise Exception(f"Could not identify page type: {analysis.get('reason', 'Unknown')}")
        
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
        st.session_state.success = True
        progress_container.progress(100)
        status_container.success(f"✅ Success! Extracted {len(deduped)} records.")
    
    except Exception as e:
        st.session_state.error_msg = str(e)
        error_container.error(f"❌ Error: {str(e)}")
        status_container.empty()
        progress_container.empty()
    
    st.markdown("---")
    
    # Show results or error
    if st.session_state.success and st.session_state.records:
        st.success(f"✅ Extracted {len(st.session_state.records)} faculty records!")
        
        st.markdown("### 📥 Download Your Data")
        
        # Convert to CSV
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
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Preview
        with st.expander("👀 Preview Data"):
            st.dataframe(
                [r.to_dict() for r in st.session_state.records[:10]],
                use_container_width=True,
                height=400
            )
    
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.job_running = False
        st.session_state.records = []
        st.session_state.error_msg = None
        st.session_state.success = False
        st.rerun()
