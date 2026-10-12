from typing import List, Optional
import io
import zipfile
import pandas as pd
from unique_content_engine import generate_unique_description
import streamlit as st
import asyncio
import os
import json
import time
import uuid
import re
from test_fill_event import fill_and_create_event, batch_fill_and_create_events, DEFAULT_ID
from test_waiver_creation import create_and_publish_waiver, batch_create_and_publish_waivers, generate_waiver_body_content
from description_generator import generate_event_description, DEFAULT_OPENROUTER_KEY, PHONE_NUMBER_1, PHONE_NUMBER_2, MAX_CHAR_LIMIT
from capiaa_bot import process_uploaded_files, upload_bulk_pdfs
from hsset_uploader import batch_upload_pdfs as hsset_batch_upload
from triomphe_uploader import batch_upload_files as triomphe_batch_upload
from usp_uploader import batch_upload_files as usp_batch_upload
from hireandwire_bot import batch_create_profiles as hireandwire_batch_create
from firstory_bot import batch_create_firstory_playlists, DEFAULT_EMAIL as FIRSTORY_DEFAULT_EMAIL, DEFAULT_PASSWORD as FIRSTORY_DEFAULT_PASSWORD
from proboards_bot import generate_proboards_content, extract_phone_tag, DEFAULT_GROQ_KEY
from pdf_content_exporter import create_single_article_pdf, create_combined_pdf, create_articles_zip
from eden_uploader import upload_pdf_to_eden, batch_upload_pdfs, DEFAULT_JOB_URL
from tenth_uploader import upload_pdf_to_tenth, batch_upload_pdfs as batch_upload_tenth_pdfs, DEFAULT_JOB_URL as TENTH_DEFAULT_JOB_URL
from usal_matricula_uploader import upload_pdf_to_usal, batch_upload_pdfs as batch_upload_usal_pdfs
from ufl_affiliate_uploader import upload_pdf_to_ufl, batch_upload_pdfs as batch_upload_ufl_pdfs

def convert_wpforms_urls(raw_input_text: str) -> List[str]:
    """
    Parses raw text, JSON objects, or URLs and converts any WPForms tmp upload URL
    to the encoded public downloadable link format (%2F formatted).
    Supports any domain (tahoe.ca.gov, capiaa.ca.gov, etc.).
    """
    if not raw_input_text:
        return []
        
    clean_text = raw_input_text.replace(r"\/", "/")
    url_pattern = r'https?://[^\s"\'<>{}|\\^`]+'
    found_urls = re.findall(url_pattern, clean_text)
    
    converted_links = []
    seen = set()

    for url in found_urls:
        url = url.rstrip('"\';,}]\\')

        if "/wp-content/uploads/" in url and "/wpforms/tmp/" in url:
            parts = url.split("/wp-content/uploads/")
            base_domain = parts[0]
            rest_path = "wp-content/uploads/" + parts[1]

            if "/wpforms/tmp/" in rest_path:
                tmp_parts = rest_path.split("/wpforms/tmp/")
                prefix = tmp_parts[0] + "/wpforms/tmp/"
                filename = tmp_parts[1]
                
                encoded_prefix = prefix.replace("/", "%2F")
                encoded_url = f"{base_domain}/{encoded_prefix}{filename}"
                
                if encoded_url not in seen:
                    seen.add(encoded_url)
                    converted_links.append(encoded_url)
            else:
                if url not in seen:
                    seen.add(url)
                    converted_links.append(url)
        else:
            if url not in seen:
                seen.add(url)
                converted_links.append(url)

    return converted_links

# Page configuration
st.set_page_config(
    page_title="SmartWaiver & CAPIAA Automation Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #64748B; margin-bottom: 2rem; }
    .badge-success { background-color: #DEF7EC; color: #03543F; font-size: 0.85rem; font-weight: 600; padding: 0.25rem 0.6rem; border-radius: 0.375rem; }
    .badge-info { background-color: #E1EFFE; color: #1E40AF; font-size: 0.85rem; font-weight: 600; padding: 0.25rem 0.6rem; border-radius: 0.375rem; }
    .stTextArea textarea { font-family: 'Consolas', 'Courier New', monospace; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "created_waivers" not in st.session_state:
    st.session_state.created_waivers = []
if "created_events" not in st.session_state:
    st.session_state.created_events = []
if "uploaded_capiaa" not in st.session_state:
    st.session_state.uploaded_capiaa = []
if "converted_urls" not in st.session_state:
    st.session_state.converted_urls = []
if "hsset_uploaded" not in st.session_state:
    st.session_state.hsset_uploaded = []
if "triomphe_uploaded" not in st.session_state:
    st.session_state.triomphe_uploaded = []
if "usp_uploaded" not in st.session_state:
    st.session_state.usp_uploaded = []
if "hireandwire_created" not in st.session_state:
    st.session_state.hireandwire_created = []
if "firstory_created" not in st.session_state:
    st.session_state.firstory_created = []
if "excel_content_df" not in st.session_state:
    st.session_state.excel_content_df = None
if "usal_links" not in st.session_state:
    if os.path.exists("usal_uploaded_links.txt"):
        try:
            with open("usal_uploaded_links.txt", "r", encoding="utf-8") as f:
                st.session_state.usal_links = [line.strip() for line in f if line.strip()]
        except Exception:
            st.session_state.usal_links = []
    else:
        st.session_state.usal_links = []
if "ufl_submissions" not in st.session_state:
    if os.path.exists("ufl_uploaded_submissions.txt"):
        try:
            with open("ufl_uploaded_submissions.txt", "r", encoding="utf-8") as f:
                st.session_state.ufl_submissions = [line.strip() for line in f if line.strip()]
        except Exception:
            st.session_state.ufl_submissions = []
    else:
        st.session_state.ufl_submissions = []

st.markdown('<div class="main-header">⚡ SmartWaiver & CAPIAA Automation Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Waiver Template Creation, Event Management, CAPIAA PDF Uploader & WPForms Link Converter</div>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.markdown("### 🔑 SmartWaiver Account")
    user_id_val = st.text_input(
        "SmartWaiver Username / ID:",
        value=DEFAULT_ID,
        key="sw_username_input",
        help="Target SmartWaiver account username"
    )
    user_pass_val = st.text_input(
        "SmartWaiver Password:",
        value="Rohit@123321",
        type="password",
        key="sw_password_input",
        help="Target SmartWaiver account password"
    )

    st.divider()
    openrouter_key = st.text_input(
        "OpenRouter API Key (Optional):",
        value=DEFAULT_OPENROUTER_KEY,
        type="password",
        help="Used to generate rich waiver content & descriptions"
    )
    
    st.divider()
    st.markdown("### 📞 Phone Number Enforcement")
    st.info(f"**Primary Phone:** `{PHONE_NUMBER_1}`\n\n**Secondary Phone:** `{PHONE_NUMBER_2}`")
    st.caption("Phone numbers are automatically interleaved every 15-20 words!")

# Mode Selection Tabs
mode = st.tabs([
    "📝 1. Create Waivers (Template Links)", 
    "🎯 2. Create Events (Actions Copy Links)",
    "📄 3. CAPIAA PDF Uploader (Certificate Links)",
    "🔄 4. WPForms Link Converter (%2F Generator)",
    "🐾 5. HSSET Job Application PDF Uploader",
    "🎵 6. Triomphe de l'Art Competition Uploader",
    "🧬 7. USP Abstracts PDF/ZIP Uploader",
    "💼 8. Hire & Wire Profile Generator",
    "🎙️ 9. Firstory Playlist Creator",
    "📊 10. StackBlitz Excel Content Bot",
    "🏨 11. Eden Hospitality PDF Uploader",
    "🏛️ 12. Tenth Revolution PDF Uploader",
    "🎓 13. USAL Digitalstack Matricula PDF Uploader",
    "🐊 14. UFL Invasion Science Affiliate PDF Uploader"
])

# TAB 1: CREATE WAIVERS
with mode[0]:
    col1, col2 = st.columns([1, 1], gap="large")

    col2_waiver_placeholder = col2.empty()
    waiver_history_placeholder = st.empty()

    def render_waivers_output():
        with col2_waiver_placeholder.container():
            st.subheader("📋 Public Waiver Links (Copy & Paste)")
            if st.session_state.created_waivers:
                urls_only = [
                    w.get("published_link") for w in st.session_state.created_waivers 
                    if w.get("published_link") and "waiver.smartwaiver.com/w/" in w.get("published_link")
                ]
                urls_plain_text = "\n".join(urls_only)

                st.markdown('<span class="badge-success">EXACT LIVE PUBLISHED WAIVER LINKS</span>', unsafe_allow_html=True)
                st.markdown("###")

                dynamic_key = f"{len(st.session_state.created_waivers)}_{time.time_ns()}"

                st.text_area(
                    label="Direct Copy Box (Public Waiver Links):",
                    value=urls_plain_text,
                    height=280,
                    help="Select all and copy directly!",
                    key=f"waiver_copy_area_{dynamic_key}"
                )

                st.download_button(
                    label="📥 Download Waiver URLs as .txt file",
                    data=urls_plain_text,
                    file_name="waiver_links.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"dl_waivers_{dynamic_key}"
                )
            else:
                st.info("Public Waiver links (`https://waiver.smartwaiver.com/w/.../web/`) will appear here as plain text for copy-pasting as soon as waivers are published.")

    def render_waivers_history():
        with waiver_history_placeholder.container():
            if st.session_state.created_waivers:
                st.divider()
                st.subheader("📜 Session Published Waivers History")
                waiver_table = []
                for item in st.session_state.created_waivers:
                    waiver_table.append({
                        "Waiver Title": item["waiver_title"],
                        "Public Published Link": item.get("published_link") or "N/A"
                    })
                st.dataframe(waiver_table, use_container_width=True)

    # Initial Render
    render_waivers_output()
    render_waivers_history()

    with col1:
        st.subheader("✍️ Bulk Waiver Titles Input")
        
        bulk_titles_raw = st.text_area(
            "Paste Bulk Waiver Titles (One per line):",
            value="",
            placeholder="What happens if someone cancels your payment Help Desk\nHow do I cancel my subscription to TotalAdblock SUPPORT USA",
            height=200,
            key="waiver_input_area"
        )

        if st.button("🚀 Auto-Create & Publish All Waivers", type="primary", use_container_width=True, key="btn_create_waivers"):
            titles_list = [t.strip() for t in bulk_titles_raw.splitlines() if t.strip()]
            
            if not titles_list:
                st.error("Please enter at least one Waiver Title!")
            else:
                st.session_state.created_waivers = []
                render_waivers_output()
                render_waivers_history()
                
                st.info(f"Processing {len(titles_list)} waiver template(s) in 1 continuous browser session...")
                progress_bar = st.progress(0)
                status_text = st.empty()

                items_payload = []
                for title in titles_list:
                    body = generate_waiver_body_content(title, api_key=openrouter_key)
                    items_payload.append({"title": title, "body": body})

                async def process_batch_waivers():
                    processed_count = 0
                    async for res in batch_create_and_publish_waivers(items_payload, username=user_id_val, password=user_pass_val):
                        processed_count += 1
                        status_text.text(f"Completed ({processed_count}/{len(titles_list)}): {res['waiver_title']}")
                        if res["success"]:
                            st.session_state.created_waivers.append(res)
                            render_waivers_output()
                            render_waivers_history()
                        progress_bar.progress(processed_count / len(titles_list))

                asyncio.run(process_batch_waivers())
                st.success(f"Successfully published {len(titles_list)} waiver template(s) in 1 continuous browser session!")

# TAB 2: CREATE EVENTS (ACTIONS COLUMN LINKS)
with mode[1]:
    col1, col2 = st.columns([1, 1], gap="large")

    col2_event_placeholder = col2.empty()
    event_history_placeholder = st.empty()

    def render_events_output():
        with col2_event_placeholder.container():
            st.subheader("📋 Public Event Links (Copy & Paste)")
            if st.session_state.created_events:
                urls_only = [
                    e.get("actions_link") for e in st.session_state.created_events 
                    if e.get("actions_link") and "waiver.smartwaiver.com/e/" in e.get("actions_link")
                ]
                urls_plain_text = "\n".join(urls_only)

                st.markdown('<span class="badge-success">EXACT EVENT PUBLIC LINKS (MATCHING CONSOLE LINK FIELD)</span>', unsafe_allow_html=True)
                st.markdown("###")

                dynamic_key = f"{len(st.session_state.created_events)}_{time.time_ns()}"

                st.text_area(
                    label="Direct Copy Box (Public Event Links):",
                    value=urls_plain_text,
                    height=280,
                    help="Select all and copy directly!",
                    key=f"event_copy_area_{dynamic_key}"
                )

                st.download_button(
                    label="📥 Download Event URLs as .txt file",
                    data=urls_plain_text,
                    file_name="event_links.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"dl_events_{dynamic_key}"
                )
            else:
                st.info("Public Event links (`https://waiver.smartwaiver.com/e/.../web/`) will appear here as plain text for copy-pasting as soon as events are created.")

    def render_events_history():
        with event_history_placeholder.container():
            if st.session_state.created_events:
                st.divider()
                st.subheader("📜 Session Created Events History")
                event_table = []
                for item in st.session_state.created_events:
                    event_table.append({
                        "Event Name": item["event_name"],
                        "Public Event Link": item.get("actions_link") or "N/A",
                        "Console Detail Link": item.get("console_link") or "N/A",
                        "Desc Length": len(item.get("event_description", ""))
                    })
                st.dataframe(event_table, use_container_width=True)

    # Initial Render
    render_events_output()
    render_events_history()

    with col1:
        st.subheader("✍️ Bulk Event Titles Input")
        
        bulk_event_titles_raw = st.text_area(
            "Paste Bulk Event Titles (One per line):",
            value="",
            placeholder="Complete-Guide How to stop Adblock payments SUPPORT USA\nHow do I cancel my subscription to TotalAdblock SUPPORT USA",
            height=180,
            key="event_input_area"
        )

        override_custom_desc = st.checkbox("Provide custom manual description (Optional)", value=False, key="cb_custom_desc")
        custom_desc_text = ""
        if override_custom_desc:
            custom_desc_text = st.text_area(
                "Custom Description (Max 1000 chars):",
                value="",
                placeholder="Custom description text...",
                max_chars=1000,
                height=100,
                key="ta_custom_desc"
            )

        if st.button("🚀 Auto-Create All Events & Get Actions Copy Links", type="primary", use_container_width=True, key="btn_create_events"):
            titles_list = [t.strip() for t in bulk_event_titles_raw.splitlines() if t.strip()]
            
            if not titles_list:
                st.error("Please enter at least one Event Title!")
            else:
                st.session_state.created_events = []
                render_events_output()
                render_events_history()

                st.info(f"Processing {len(titles_list)} event(s) in 1 continuous browser session...")
                progress_bar = st.progress(0)
                status_text = st.empty()

                items_payload = []
                for title in titles_list:
                    if override_custom_desc and custom_desc_text.strip():
                        desc = custom_desc_text.strip()[:MAX_CHAR_LIMIT]
                    else:
                        desc = generate_event_description(title, api_key=openrouter_key)
                    items_payload.append({"name": title, "description": desc})

                async def process_batch_events():
                    processed_count = 0
                    async for res in batch_fill_and_create_events(items_payload, username=user_id_val, password=user_pass_val):
                        processed_count += 1
                        status_text.text(f"Completed ({processed_count}/{len(titles_list)}): {res['event_name']}")
                        st.session_state.created_events.append(res)
                        render_events_output()
                        render_events_history()
                        progress_bar.progress(processed_count / len(titles_list))

                asyncio.run(process_batch_events())
                st.success(f"Successfully created {len(titles_list)} event(s) in 1 continuous browser session!")

# TAB 3: CAPIAA PDF UPLOADER
with mode[2]:
    col1, col2 = st.columns([1, 1], gap="large")

    col2_capiaa_placeholder = col2.empty()
    capiaa_history_placeholder = st.empty()

    def render_capiaa_output():
        with col2_capiaa_placeholder.container():
            st.subheader("📋 Public CAPIAA Encoded Links (Copy & Paste)")
            if st.session_state.uploaded_capiaa:
                urls_only = [
                    item.get("encoded_url") for item in st.session_state.uploaded_capiaa
                    if item.get("encoded_url")
                ]
                urls_plain_text = "\n".join(urls_only)

                st.markdown('<span class="badge-success">EXACT CAPIAA ENCODED DOWNLOAD LINKS (%2F FORMATTED)</span>', unsafe_allow_html=True)
                st.markdown("###")

                dynamic_key = f"{len(st.session_state.uploaded_capiaa)}_{time.time_ns()}"

                st.text_area(
                    label="Direct Copy Box (CAPIAA Encoded Links):",
                    value=urls_plain_text,
                    height=280,
                    help="Select all and copy directly!",
                    key=f"capiaa_copy_area_{dynamic_key}"
                )

                st.download_button(
                    label="📥 Download CAPIAA URLs as .txt file",
                    data=urls_plain_text,
                    file_name="capiaa_encoded_links.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"dl_capiaa_{dynamic_key}"
                )
            else:
                st.info("Public CAPIAA encoded links (`https://capiaa.ca.gov/wp-content%2F...`) will appear here as plain text for copy-pasting as soon as PDF files are uploaded.")

    def render_capiaa_history():
        with capiaa_history_placeholder.container():
            if st.session_state.uploaded_capiaa:
                st.divider()
                st.subheader("📜 Session Uploaded CAPIAA Files History")
                capiaa_table = []
                for item in st.session_state.uploaded_capiaa:
                    capiaa_table.append({
                        "File Name": item["file_name"],
                        "Status": "✅ Success" if item.get("success") else "❌ Failed",
                        "Encoded URL": item.get("encoded_url") or "N/A",
                        "Error": item.get("error") or "None"
                    })
                st.dataframe(capiaa_table, use_container_width=True)

    # Initial Render
    render_capiaa_output()
    render_capiaa_history()

    with col1:
        st.subheader("📤 Bulk Upload PDF & ZIP Files")
        st.warning("🌐 **VPN / Location Notice:** `capiaa.ca.gov` requires a **US Location**. If you get a `403 Forbidden` error, please turn on your VPN (US region) or enter a US Proxy below.")
        
        uploaded_files = st.file_uploader(
            "Select PDF file(s) or ZIP archive containing PDFs:",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            help="Upload single/multiple PDFs or ZIP archives containing PDFs.",
            key="capiaa_file_uploader"
        )

        proxy_url_val = st.text_input(
            "US Proxy Server (Optional if VPN is active):",
            value="",
            placeholder="http://123.45.67.89:8080 or http://user:pass@ip:port",
            help="Optional HTTP/HTTPS proxy to bypass 403 Forbidden Geo-Blocking.",
            key="capiaa_proxy_url"
        )

        run_headless = st.checkbox("Run browser in background (Headless Mode)", value=False, key="cb_capiaa_headless")

        if st.button("🚀 Upload PDFs to CAPIAA & Get Public Links", type="primary", use_container_width=True, key="btn_upload_capiaa"):
            if not uploaded_files:
                st.error("Please upload at least one PDF or ZIP file!")
            else:
                extracted_pdf_paths = process_uploaded_files(uploaded_files)
                
                if not extracted_pdf_paths:
                    st.error("No valid PDF files found in the upload!")
                else:
                    st.session_state.uploaded_capiaa = []
                    render_capiaa_output()
                    render_capiaa_history()

                    st.info(f"Processing {len(extracted_pdf_paths)} PDF file(s) on CAPIAA server...")
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    async def run_capiaa_uploads():
                        results = await upload_bulk_pdfs(extracted_pdf_paths, headless=run_headless, proxy_url=proxy_url_val)
                        for idx, res in enumerate(results):
                            status_text.text(f"Uploaded ({idx + 1}/{len(extracted_pdf_paths)}): {res['file_name']}")
                            st.session_state.uploaded_capiaa.append(res)
                            render_capiaa_output()
                            render_capiaa_history()
                            progress_bar.progress((idx + 1) / len(extracted_pdf_paths))

                    asyncio.run(run_capiaa_uploads())
                    st.success(f"Successfully processed {len(extracted_pdf_paths)} PDF file(s) on CAPIAA!")

# TAB 4: WPFORMS LINK CONVERTER (%2F GENERATOR)
with mode[3]:
    col1, col2 = st.columns([1, 1], gap="large")

    col2_converter_placeholder = col2.empty()

    def render_converter_output():
        with col2_converter_placeholder.container():
            st.subheader("📋 Public Encoded Download Links (%2F Format)")
            if st.session_state.converted_urls:
                urls_plain_text = "\n".join(st.session_state.converted_urls)

                st.markdown(f'<span class="badge-success">EXACT %2F ENCODED PUBLIC DOWNLOAD LINKS ({len(st.session_state.converted_urls)} CONVERTED)</span>', unsafe_allow_html=True)
                st.markdown("###")

                dynamic_key = f"{len(st.session_state.converted_urls)}_{time.time_ns()}"

                st.text_area(
                    label="Direct Copy Box (Converted %2F Download Links):",
                    value=urls_plain_text,
                    height=320,
                    help="Select all and copy directly!",
                    key=f"conv_copy_area_{dynamic_key}"
                )

                st.download_button(
                    label="📥 Download Converted URLs as .txt file",
                    data=urls_plain_text,
                    file_name="wpforms_converted_links.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"dl_conv_{dynamic_key}"
                )
            else:
                st.info("Converted public downloadable links (`https://domain.ca.gov/wp-content%2F...`) will appear here as plain text for instant copy-pasting.")

    # Initial Render
    render_converter_output()

    with col1:
        st.subheader("📥 Bulk Input: Paste URLs or DevTools Response JSON")
        
        raw_converter_input = st.text_area(
            "Paste Raw URLs, Escaped URLs, or Chrome DevTools Network Response JSON (One per line or raw block):",
            value="",
            placeholder="https://tahoe.ca.gov/wp-content/uploads/sites/257/wpforms/tmp/5a1571124a73801fc72aca7e9a7475ff.pdf\n"
                        "OR DevTools JSON Response:\n"
                        '{"success":true,"data":{"url":"https:\\/\\/tahoe.ca.gov\\/wp-content\\/uploads\\/sites\\/257\\/wpforms\\/tmp\\/cd68b16cd028d91002745f8454c10729.pdf"}}',
            height=280,
            key="converter_input_area"
        )

        if st.button("⚡ Convert All URLs to Public %2F Encoded Links", type="primary", use_container_width=True, key="btn_convert_urls"):
            if not raw_converter_input.strip():
                st.error("Please paste at least one URL or DevTools Network JSON response!")
            else:
                converted = convert_wpforms_urls(raw_converter_input)
                if not converted:
                    st.error("No valid WPForms URLs found in your input text!")
                else:
                    st.session_state.converted_urls = converted
                    render_converter_output()
                    st.success(f"Successfully converted {len(converted)} WPForms URL(s) to public %2F encoded format!")

# ─────────────────────────────────────────────────────────────
# TAB 5: HSSET JOB APPLICATION PDF UPLOADER
# ─────────────────────────────────────────────────────────────
with mode[4]:
    st.markdown("""
    <style>
    .hsset-badge { background: linear-gradient(135deg, #1a73e8, #0d47a1); color:#fff;
        padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:700; letter-spacing:.05em; }
    .hsset-url-box { background:#0f172a; border:1px solid #334155; border-radius:8px;
        padding:14px 18px; font-family:'Courier New',monospace; font-size:0.82rem;
        color:#38bdf8; word-break:break-all; margin-bottom:6px; }
    .hsset-success { color:#22c55e; font-weight:700; }
    .hsset-fail    { color:#ef4444; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    hsset_output_placeholder = col2.empty()

    def render_hsset_output():
        with hsset_output_placeholder.container():
            st.subheader("🔗 Public Upload Links")
            st.caption("Direct-access PDF links (no login required)")
            if st.session_state.hsset_uploaded:
                success_items = [r for r in st.session_state.hsset_uploaded if r["success"]]
                fail_items    = [r for r in st.session_state.hsset_uploaded if not r["success"]]

                if success_items:
                    urls_text = "\n".join(r["public_url"] for r in success_items)
                    st.markdown('<span class="hsset-badge">✅ LIVE PUBLIC PDF LINKS</span>', unsafe_allow_html=True)
                    st.markdown("")

                    dyn_key = f"hsset_{len(success_items)}_{int(time.time())}"
                    st.text_area(
                        "Copy-paste box (one URL per line):",
                        value=urls_text,
                        height=260,
                        key=f"hsset_copy_{dyn_key}",
                        help="Select all → Ctrl+C to copy"
                    )
                    st.download_button(
                        "📥 Download URLs as .txt",
                        data=urls_text,
                        file_name="hsset_upload_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"hsset_dl_{dyn_key}"
                    )

                if fail_items:
                    st.markdown("**❌ Failed uploads:**")
                    for r in fail_items:
                        st.markdown(f'<span class="hsset-fail">✗ {r["file_name"]}</span>: {r["error"]}',
                                    unsafe_allow_html=True)
            else:
                st.info(
                    "Upload links will appear here.\n\n"
                    "Format: `https://humanesocietyofsoutheasttexas.org/wp-content/uploads/"
                    "wp_dndcf7_uploads/wpcf7-files/<UUID>/<filename>`"
                )

    def render_hsset_history():
        if st.session_state.hsset_uploaded:
            st.divider()
            st.subheader("📋 Upload History (This Session)")
            table_data = []
            for r in st.session_state.hsset_uploaded:
                table_data.append({
                    "File": r["file_name"],
                    "Status": "✅ Success" if r["success"] else "❌ Failed",
                    "Public URL": r.get("public_url") or r.get("error", "N/A")
                })
            st.dataframe(table_data, use_container_width=True)

    render_hsset_output()

    with col1:
        st.subheader("🐾 HSSET PDF Uploader")
        st.caption(
            "Uploads PDFs to [humanesocietyofsoutheasttexas.org/job-application/]("
            "https://humanesocietyofsoutheasttexas.org/job-application/) "
            "and returns the direct public link. **No form submission.**"
        )
        st.markdown("")

        uploaded_files = st.file_uploader(
            "Upload PDF or ZIP file(s):",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="hsset_file_uploader",
            help="Select one or more PDF or ZIP files to upload"
        )

        col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 1])
        with col_opt1:
            hsset_start_num = st.number_input("▶️ Start from File #:", min_value=1, value=1, step=1, key="hsset_start_num", help="Set to e.g. 369 to resume from file 369")
        with col_opt2:
            hsset_auto_skip = st.checkbox("⏩ Auto-skip uploaded", value=True, key="hsset_auto_skip", help="Skip files already in session history")
        with col_opt3:
            hsset_clear_prev = st.checkbox("🗑️ Clear previous", value=False, key="hsset_clear_prev", help="Check to erase old links before starting")

        if st.button(
            "🚀 Upload & Get Public Links",
            type="primary",
            use_container_width=True,
            key="btn_hsset_upload",
            disabled=(not uploaded_files)
        ):
            import tempfile

            if hsset_clear_prev:
                st.session_state.hsset_uploaded = []
                render_hsset_output()

            existing_filenames = set(
                r["file_name"] for r in st.session_state.hsset_uploaded if r.get("success")
            )

            progress = st.progress(0)
            status   = st.empty()

            # Save uploaded streamlit files to temp paths
            tmp_paths = []
            tmp_dir   = tempfile.mkdtemp()
            for uf in uploaded_files:
                if hsset_auto_skip and uf.name in existing_filenames:
                    continue
                tmp_path = os.path.join(tmp_dir, uf.name)
                with open(tmp_path, "wb") as f:
                    f.write(uf.read())
                tmp_paths.append(tmp_path)

            total = len(uploaded_files)
            if not tmp_paths:
                st.info("All selected files are already uploaded in session history!")
            else:
                status.info(f"Uploading {len(tmp_paths)} file(s) (starting from #{hsset_start_num})...")

                ok, bad = 0, 0
                start_val = int(hsset_start_num)
                for i, res in enumerate(hsset_batch_upload(tmp_paths, start_index=start_val), start_val):
                    st.session_state.hsset_uploaded.append(res)
                    render_hsset_output()
                    if res["success"]: ok += 1
                    else: bad += 1
                    status.text(
                        f"({i}/{total}) {'✅' if res['success'] else '❌'} {res['file_name']}"
                    )
                    progress.progress(min(1.0, i / max(1, total)))

                # Clean up temp files
                for p in tmp_paths:
                    try: os.remove(p)
                    except: pass
                try: os.rmdir(tmp_dir)
                except: pass

                if ok:
                    st.success(f"✅ {ok} file(s) uploaded successfully!")
                if bad:
                    st.error(f"❌ {bad} file(s) failed.")

    render_hsset_history()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: TRIOMPHE DE L'ART COMPETITION UPLOADER
# ─────────────────────────────────────────────────────────────────────────────
with mode[5]:
    st.markdown("""
    <style>
    .triomphe-badge { background: linear-gradient(135deg, #7c3aed, #4f46e5); color:#fff;
        padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; letter-spacing:.05em; }
    .triomphe-fail  { color:#ef4444; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    triomphe_output_ph = col2.empty()
    triomphe_history_ph = st.empty()

    def render_triomphe_output():
        with triomphe_output_ph.container():
            st.subheader("🔗 Public Upload Links")
            st.caption("Direct-access links — no login required")
            if st.session_state.triomphe_uploaded:
                ok_items   = [r for r in st.session_state.triomphe_uploaded if r["success"]]
                fail_items = [r for r in st.session_state.triomphe_uploaded if not r["success"]]

                if ok_items:
                    urls_text = "\n".join(r["public_url"] for r in ok_items)
                    st.markdown('<span class="triomphe-badge">✅ LIVE COMPETITION UPLOAD LINKS</span>',
                                unsafe_allow_html=True)
                    st.markdown("")
                    dyn_key = f"triomphe_{len(ok_items)}_{int(time.time())}"
                    st.text_area(
                        "Copy-paste box (one URL per line):",
                        value=urls_text,
                        height=260,
                        key=f"triomphe_copy_{dyn_key}",
                        help="Select all → Ctrl+C"
                    )
                    st.download_button(
                        "📥 Download URLs as .txt",
                        data=urls_text,
                        file_name="triomphe_upload_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"triomphe_dl_{dyn_key}"
                    )

                if fail_items:
                    st.markdown("**❌ Failed uploads:**")
                    for r in fail_items:
                        st.markdown(
                            f'<span class="triomphe-fail">✗ {r["file_name"]}</span>: {r["error"]}',
                            unsafe_allow_html=True
                        )
            else:
                st.info(
                    "Upload links will appear here.\n\n"
                    "Format: `https://triomphedelart.org/wp-content/uploads/"
                    "wp_dndcf7_uploads/wpcf7-files/<filename>`\n\n"
                    "Reference: [`usa16.pdf`](https://triomphedelart.org/wp-content/uploads/"
                    "wp_dndcf7_uploads/wpcf7-files/usa16.pdf)"
                )

    def render_triomphe_history():
        with triomphe_history_ph.container():
            if st.session_state.triomphe_uploaded:
                st.divider()
                st.subheader("📋 Upload History (This Session)")
                table_data = []
                for r in st.session_state.triomphe_uploaded:
                    table_data.append({
                        "File": r["file_name"],
                        "Status": "✅ Success" if r["success"] else "❌ Failed",
                        "Public URL": r.get("public_url") or r.get("error", "N/A")
                    })
                st.dataframe(table_data, use_container_width=True)

    render_triomphe_output()

    with col1:
        st.subheader("🎵 Triomphe de l'Art Uploader")
        st.caption(
            "Uploads PDFs/ZIPs to the [XI International Music Competition apply form]("
            "https://triomphedelart.org/language/en/international-music-competition/"
            "xi-international-music-competition-triomphe-de-lart-string-instruments-chamber-music/apply-2026/"
            ") and returns the direct public link. **No form submission.**"
        )
        st.markdown(
            "📎 Reference URL format: "
            "`https://triomphedelart.org/wp-content/uploads/wp_dndcf7_uploads/wpcf7-files/<filename>`"
        )
        st.markdown("")

        triomphe_files = st.file_uploader(
            "Upload PDF or ZIP file(s):",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="triomphe_file_uploader",
            help="Select up to 10 PDF or ZIP files"
        )

        col_t_opt1, col_t_opt2, col_t_opt3 = st.columns([1, 1, 1])
        with col_t_opt1:
            triomphe_start_num = st.number_input("▶️ Start from File #:", min_value=1, value=1, step=1, key="triomphe_start_num", help="Set to e.g. 369 to resume from file 369")
        with col_t_opt2:
            triomphe_auto_skip = st.checkbox("⏩ Auto-skip uploaded", value=True, key="triomphe_auto_skip", help="Skip files already in session history")
        with col_t_opt3:
            triomphe_clear_prev = st.checkbox("🗑️ Clear previous", value=False, key="triomphe_clear_prev", help="Check to erase old links before starting")

        if st.button(
            "🚀 Upload & Get Public Links",
            type="primary",
            use_container_width=True,
            key="btn_triomphe_upload",
            disabled=(not triomphe_files)
        ):
            import tempfile

            if triomphe_clear_prev:
                st.session_state.triomphe_uploaded = []
                render_triomphe_output()

            existing_t_filenames = set(
                r["file_name"] for r in st.session_state.triomphe_uploaded if r.get("success")
            )

            progress = st.progress(0)
            status   = st.empty()

            tmp_paths = []
            tmp_dir   = tempfile.mkdtemp()
            for uf in triomphe_files:
                if triomphe_auto_skip and uf.name in existing_t_filenames:
                    continue
                tmp_path = os.path.join(tmp_dir, uf.name)
                with open(tmp_path, "wb") as f:
                    f.write(uf.read())
                tmp_paths.append(tmp_path)

            total = len(triomphe_files)
            if not tmp_paths:
                st.info("All selected files are already uploaded in session history!")
            else:
                status.info(f"Uploading {len(tmp_paths)} file(s) (starting from #{triomphe_start_num})...")

                ok, bad = 0, 0
                start_val = int(triomphe_start_num)
                for i, res in enumerate(triomphe_batch_upload(tmp_paths, start_index=start_val), start_val):
                    st.session_state.triomphe_uploaded.append(res)
                    render_triomphe_output()
                    render_triomphe_history()
                    if res["success"]: ok += 1
                    else: bad += 1
                    status.text(
                        f"({i}/{total}) {'✅' if res['success'] else '❌'} {res['file_name']}"
                    )
                    progress.progress(min(1.0, i / max(1, total)))

                # Cleanup temp files
                for p in tmp_paths:
                    try: os.remove(p)
                    except: pass
                try: os.rmdir(tmp_dir)
                except: pass

                if ok:
                    st.success(f"✅ {ok} file(s) uploaded successfully!")
                if bad:
                    st.error(f"❌ {bad} file(s) failed.")

    render_triomphe_history()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 7: USP ABSTRACTS PDF/ZIP UPLOADER (UNIVERSIDADE DE SÃO PAULO)
# ─────────────────────────────────────────────────────────────────────────────
with mode[6]:
    st.markdown("""
    <style>
    .usp-badge { background: linear-gradient(135deg, #059669, #10b981); color:#fff;
        padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; letter-spacing:.05em; }
    .usp-fail  { color:#ef4444; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    usp_output_ph = col2.empty()
    usp_history_ph = st.empty()

    def render_usp_output():
        with usp_output_ph.container():
            st.subheader("🔗 Public Upload Links")
            st.caption("Direct-access USP webform links — no login required")
            if st.session_state.usp_uploaded:
                ok_items   = [r for r in st.session_state.usp_uploaded if r["success"]]
                fail_items = [r for r in st.session_state.usp_uploaded if not r["success"]]

                if ok_items:
                    urls_text = "\n".join(r["public_url"] for r in ok_items)
                    st.markdown('<span class="usp-badge">✅ LIVE USP PUBLIC PDF/ZIP LINKS</span>',
                                unsafe_allow_html=True)
                    st.markdown("")
                    dyn_key = f"usp_{len(ok_items)}_{int(time.time())}"
                    st.text_area(
                        "Copy-paste box (one URL per line):",
                        value=urls_text,
                        height=260,
                        key=f"usp_copy_{dyn_key}",
                        help="Select all → Ctrl+C"
                    )
                    st.download_button(
                        "📥 Download URLs as .txt",
                        data=urls_text,
                        file_name="usp_upload_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"usp_dl_{dyn_key}"
                    )

                if fail_items:
                    st.markdown("**❌ Failed uploads:**")
                    for r in fail_items:
                        st.markdown(
                            f'<span class="usp-fail">✗ {r["file_name"]}</span>: {r["error"]}',
                            unsafe_allow_html=True
                        )
            else:
                st.info(
                    "Upload links will appear here.\n\n"
                    "Format: `https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/<filename>`\n\n"
                    "Reference links:\n"
                    "- [`grow2.pdf`](https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/grow2.pdf)\n"
                    "- [`aeromexicopromote.pdf`](https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/aeromexicopromote.pdf)"
                )

    def render_usp_history():
        with usp_history_ph.container():
            if st.session_state.usp_uploaded:
                st.divider()
                st.subheader("📋 Upload History (This Session)")
                table_data = []
                for r in st.session_state.usp_uploaded:
                    table_data.append({
                        "File": r["file_name"],
                        "Status": "✅ Success" if r["success"] else "❌ Failed",
                        "Public URL": r.get("public_url") or r.get("error", "N/A")
                    })
                st.dataframe(table_data, use_container_width=True)

    render_usp_output()

    with col1:
        st.subheader("🧬 USP Abstracts Uploader")
        st.caption(
            "Uploads PDFs/ZIPs to [https://www.iq.usp.br/farmdna/abstracts-form.html]("
            "https://www.iq.usp.br/farmdna/abstracts-form.html"
            ") and returns direct public links. **No form submission required.**"
        )
        st.markdown(
            "📎 Reference link format: "
            "`https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/<filename>`"
        )
        st.markdown("")

        usp_files = st.file_uploader(
            "Upload PDF or ZIP file(s):",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="usp_file_uploader",
            help="Select PDF or ZIP files to upload"
        )

        col_u_opt1, col_u_opt2, col_u_opt3 = st.columns([1, 1, 1])
        with col_u_opt1:
            usp_start_num = st.number_input("▶️ Start from File #:", min_value=1, value=1, step=1, key="usp_start_num", help="Set to e.g. 369 to resume")
        with col_u_opt2:
            usp_auto_skip = st.checkbox("⏩ Auto-skip uploaded", value=True, key="usp_auto_skip", help="Skip files already in session history")
        with col_u_opt3:
            usp_clear_prev = st.checkbox("🗑️ Clear previous", value=False, key="usp_clear_prev", help="Check to erase old links before starting")

        if st.button(
            "🚀 Upload & Get Public Links",
            type="primary",
            use_container_width=True,
            key="btn_usp_upload",
            disabled=(not usp_files)
        ):
            import tempfile

            if usp_clear_prev:
                st.session_state.usp_uploaded = []
                render_usp_output()

            existing_u_filenames = set(
                r["file_name"] for r in st.session_state.usp_uploaded if r.get("success")
            )

            progress = st.progress(0)
            status   = st.empty()

            tmp_paths = []
            tmp_dir   = tempfile.mkdtemp()
            for uf in usp_files:
                if usp_auto_skip and uf.name in existing_u_filenames:
                    continue
                tmp_path = os.path.join(tmp_dir, uf.name)
                with open(tmp_path, "wb") as f:
                    f.write(uf.read())
                tmp_paths.append(tmp_path)

            total = len(usp_files)
            if not tmp_paths:
                st.info("All selected files are already uploaded in session history!")
            else:
                status.info(f"Uploading {len(tmp_paths)} file(s) (starting from #{usp_start_num})...")

                ok, bad = 0, 0
                start_val = int(usp_start_num)
                for i, res in enumerate(usp_batch_upload(tmp_paths, start_index=start_val), start_val):
                    st.session_state.usp_uploaded.append(res)
                    render_usp_output()
                    render_usp_history()
                    if res["success"]: ok += 1
                    else: bad += 1
                    status.text(
                        f"({i}/{total}) {'✅' if res['success'] else '❌'} {res['file_name']}"
                    )
                    progress.progress(min(1.0, i / max(1, total)))

                # Cleanup temp files
                for p in tmp_paths:
                    try: os.remove(p)
                    except: pass
                try: os.rmdir(tmp_dir)
                except: pass

                if ok:
                    st.success(f"✅ {ok} file(s) uploaded successfully!")
                if bad:
                    st.error(f"❌ {bad} file(s) failed.")

    render_usp_history()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 8: HIRE & WIRE PROFILE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
with mode[7]:
    st.markdown("""
    <style>
    .hw-badge { background: linear-gradient(135deg, #0284c7, #3b82f6); color:#fff;
        padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; letter-spacing:.05em; }
    .hw-fail  { color:#ef4444; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    hw_output_ph = col2.empty()
    hw_history_ph = st.empty()

    def render_hw_output():
        with hw_output_ph.container():
            st.subheader("🔗 Candidate Profile URLs")
            st.caption("Public candidate profile URLs generated on Hire & Wire")
            if st.session_state.hireandwire_created:
                ok_items   = [r for r in st.session_state.hireandwire_created if r["success"]]
                fail_items = [r for r in st.session_state.hireandwire_created if not r["success"]]

                if ok_items:
                    urls_text = "\n".join(r["public_profile_url"] for r in ok_items)
                    st.markdown('<span class="hw-badge">✅ LIVE HIRE & WIRE PROFILE LINKS</span>',
                                unsafe_allow_html=True)
                    st.markdown("")
                    dyn_key = f"hw_{len(ok_items)}_{int(time.time())}"
                    st.text_area(
                        "Copy-paste box (one Profile URL per line):",
                        value=urls_text,
                        height=260,
                        key=f"hw_copy_{dyn_key}",
                        help="Select all → Ctrl+C"
                    )
                    st.download_button(
                        "📥 Download Profile URLs as .txt",
                        data=urls_text,
                        file_name="hireandwire_profile_urls.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"hw_dl_{dyn_key}"
                    )

                if fail_items:
                    st.markdown("**❌ Failed profile creations:**")
                    for r in fail_items:
                        st.markdown(
                            f'<span class="hw-fail">✗ {r["job_title"]}</span>: {r["error"]}',
                            unsafe_allow_html=True
                        )
            else:
                st.info(
                    "Generated profile URLs will appear here.\n\n"
                    "Format: `https://hireandwire.com/candidate/<username>/`\n\n"
                    "Workflow:\n"
                    "1. Registers a new account on [`https://hireandwire.com/login-register/`](https://hireandwire.com/login-register/)\n"
                    "2. Fills **Job Title** and OpenRouter AI-generated **Description** on [`/profile/`](https://hireandwire.com/profile/)\n"
                    "3. Extracts candidate Profile URL\n"
                    "4. Logs out previous account automatically before creating the next profile!"
                )

    def render_hw_history():
        with hw_history_ph.container():
            if st.session_state.hireandwire_created:
                st.divider()
                st.subheader("📋 Created Profiles History (This Session)")
                table_data = []
                for r in st.session_state.hireandwire_created:
                    table_data.append({
                        "Job Title": r.get("job_title", "N/A"),
                        "Username": r.get("username", "N/A"),
                        "Status": "✅ Success" if r["success"] else "❌ Failed",
                        "Candidate Profile URL": r.get("public_profile_url") or r.get("error", "N/A")
                    })
                st.dataframe(table_data, use_container_width=True)

    render_hw_output()

    with col1:
        st.subheader("💼 Hire & Wire Profile Generator")
        st.caption(
            "Auto-registers accounts, generates AI descriptions via OpenRouter, populates candidate profiles, and extracts public URLs."
        )
        st.markdown("")

        hw_job_titles_raw = st.text_area(
            "Enter Job Title(s) (One per line or comma-separated):",
            value="Senior Python Developer & AI Automation Specialist\nFull Stack Web Developer & DevOps Engineer",
            height=140,
            key="hw_job_titles_input",
            help="Enter one job title per line. Each line will create a new candidate account + profile!"
        )

        col_h_opt1, col_h_opt2 = st.columns([1, 1])
        with col_h_opt1:
            hw_start_num = st.number_input("▶️ Start from Title #:", min_value=1, value=1, step=1, key="hw_start_num")
        with col_h_opt2:
            hw_clear_prev = st.checkbox("🗑️ Clear previous profiles", value=False, key="hw_clear_prev")

        hw_visible_browser = st.checkbox(
            "🖥️ Open visible browser window during creation (Playwright)",
            value=False,
            key="hw_visible_browser",
            help="Check this to watch the browser fill fields live! (Will NOT close your existing Chrome windows)"
        )

        if st.button(
            "🚀 Create Accounts & Get Profile URLs",
            type="primary",
            use_container_width=True,
            key="btn_hw_create"
        ):
            titles_list = [t.strip() for t in re.split(r'[\r\n,]+', hw_job_titles_raw) if t.strip()]

            if not titles_list:
                st.warning("Please enter at least one Job Title!")
            else:
                if hw_clear_prev:
                    st.session_state.hireandwire_created = []
                    render_hw_output()

                progress = st.progress(0)
                status   = st.empty()
                total = len(titles_list)
                start_val = int(hw_start_num)

                status.info(f"Creating {total} candidate profile(s)...")

                ok, bad = 0, 0
                for i, res in enumerate(hireandwire_batch_create(titles_list, openrouter_key=openrouter_key, start_index=start_val, visible_browser=hw_visible_browser), start_val):
                    st.session_state.hireandwire_created.append(res)
                    render_hw_output()
                    render_hw_history()
                    if res["success"]: ok += 1
                    else: bad += 1
                    status.text(
                        f"({i}/{total}) {'✅' if res['success'] else '❌'} {res.get('job_title')}"
                    )
                    progress.progress(min(1.0, i / max(1, total)))

                if ok:
                    st.success(f"✅ {ok} candidate profile(s) created successfully!")
                if bad:
                    st.error(f"❌ {bad} profile creation(s) failed.")

    render_hw_history()

# TAB 9: FIRSTORY PLAYLIST CREATOR
with mode[8]:
    st.markdown("""
    <style>
    .fs-badge { background: linear-gradient(135deg, #ec4899, #f43f5e); color:#fff;
        padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; letter-spacing:.05em; }
    .fs-fail  { color:#ef4444; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    fs_output_ph = col2.empty()
    fs_history_ph = st.empty()

    def render_fs_output():
        with fs_output_ph.container():
            st.subheader("🔗 Public Playlist Share URLs")
            st.caption("Public share links generated on Firstory Studio")
            if st.session_state.firstory_created:
                ok_items   = [r for r in st.session_state.firstory_created if r["success"]]
                fail_items = [r for r in st.session_state.firstory_created if not r["success"]]

                if ok_items:
                    urls_text = "\n".join(r["share_url"] for r in ok_items)
                    st.markdown('<span class="fs-badge">✅ LIVE FIRSTORY PLAYLIST LINKS</span>',
                                unsafe_allow_html=True)
                    st.markdown("")
                    dyn_key = f"fs_{len(ok_items)}_{int(time.time())}"
                    st.text_area(
                        "Copy-paste box (one Playlist URL per line):",
                        value=urls_text,
                        height=260,
                        key=f"fs_copy_{dyn_key}",
                        help="Select all → Ctrl+C"
                    )
                    st.download_button(
                        "📥 Download Playlist URLs as .txt",
                        data=urls_text,
                        file_name="firstory_playlist_urls.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"fs_dl_{dyn_key}"
                    )

                if fail_items:
                    st.markdown("**❌ Failed playlist creations:**")
                    for r in fail_items:
                        st.markdown(
                            f'<span class="fs-fail">✗ {r["title"]}</span>: {r["error"]}',
                            unsafe_allow_html=True
                        )
            else:
                st.info(
                    "Generated Playlist Share URLs will appear here.\n\n"
                    "Format: `https://open.firstory.me/playlists/<playlist_id>`\n\n"
                    "Workflow:\n"
                    "1. Log in to [`https://studio.firstory.me/login?role=creator`](https://studio.firstory.me/login?role=creator)\n"
                    "2. Opens [`/playlists/new`](https://studio.firstory.me/playlists/new)\n"
                    "3. Fills **Title** & OpenRouter AI-generated **Description** (with support phone numbers)\n"
                    "4. Saves Playlist & extracts public Share Playlist URL!"
                )

    def render_fs_history():
        with fs_history_ph.container():
            if st.session_state.firstory_created:
                st.divider()
                st.subheader("📋 Created Playlists History (This Session)")
                table_data = []
                for r in st.session_state.firstory_created:
                    table_data.append({
                        "Playlist Title": r.get("title", "N/A"),
                        "Status": "✅ Success" if r["success"] else "❌ Failed",
                        "Public Playlist Share URL": r.get("share_url") or r.get("error", "N/A")
                    })
                st.dataframe(table_data, use_container_width=True)

    render_fs_output()

    with col1:
        st.subheader("🎙️ Firstory Playlist Creator")
        st.caption(
            "Log in to Firstory Creator Studio, generates AI descriptions via OpenRouter, populates playlist Title & Description, and extracts public share URLs."
        )
        st.markdown("")

        fs_email = st.text_input("Firstory Creator Email:", value=FIRSTORY_DEFAULT_EMAIL, key="fs_email_input")
        fs_password = st.text_input("Firstory Creator Password:", value=FIRSTORY_DEFAULT_PASSWORD, type="password", key="fs_password_input")
        fs_tfn = st.text_input("Toll-Free Support Phone Number:", value="+1 888 308 7172", key="fs_tfn_input")
        fs_api_key = st.text_input("OpenRouter API Key:", value=DEFAULT_OPENROUTER_KEY, type="password", key="fs_api_key_input")

        fs_titles_raw = st.text_area(
            "Enter Playlist Title(s) (One per line):",
            value="How to cancel Total Adblock Subscription - Complete Guide\nHow to stop Adblock payments easily",
            height=140,
            key="fs_titles_input",
            help="Enter one title per line. Each line will create a new playlist on Firstory!"
        )

        col_f_opt1, col_f_opt2 = st.columns([1, 1])
        with col_f_opt1:
            fs_start_num = st.number_input("▶️ Start from Title #:", min_value=1, value=1, step=1, key="fs_start_num")
        with col_f_opt2:
            fs_clear_prev = st.checkbox("🗑️ Clear previous playlists", value=False, key="fs_clear_prev")

        fs_visible_browser = st.checkbox(
            "🖥️ Open visible browser window during creation (Playwright)",
            value=False,
            key="fs_visible_browser",
            help="Check this to watch Playwright fill fields live!"
        )

        if st.button(
            "🚀 Create Playlists & Get Links",
            type="primary",
            use_container_width=True,
            key="btn_fs_create"
        ):
            titles_list = [t.strip() for t in re.split(r'[\r\n,]+', fs_titles_raw) if t.strip()]

            if not titles_list:
                st.warning("Please enter at least one Playlist Title!")
            else:
                if fs_clear_prev:
                    st.session_state.firstory_created = []
                    render_fs_output()

                progress = st.progress(0)
                status   = st.empty()
                total = len(titles_list)
                start_val = int(fs_start_num)

                status.info(f"Creating {total} Firstory playlist(s)...")

                ok, bad = 0, 0
                for i, res in enumerate(batch_create_firstory_playlists(titles_list, email=fs_email, password=fs_password, start_index=start_val, headless=not fs_visible_browser, api_key=fs_api_key, tfn=fs_tfn), start_val):
                    st.session_state.firstory_created.append(res)
                    render_fs_output()
                    render_fs_history()
                    if res["success"]: ok += 1
                    else: bad += 1
                    status.text(
                        f"({i}/{total}) {'✅' if res['success'] else '❌'} {res.get('title')}"
                    )
                    progress.progress(min(1.0, i / max(1, total)))

                if ok:
                    st.success(f"✅ {ok} Firstory playlist(s) created successfully!")
                if bad:
                    st.error(f"❌ {bad} playlist creation(s) failed.")

    render_fs_history()

# TAB 10: STACKBLITZ EXCEL CONTENT BOT
with mode[9]:
    col_ex1, col_ex2 = st.columns([1, 1], gap="large")

    with col_ex2:
        st.subheader("📥 Live Content & Download Stream")
        live_status_box = st.empty()
        live_metrics_box = st.empty()
        live_downloads_box = st.empty()
        live_table_box = st.empty()
        st.markdown("---")
        st.write("### 🔍 Real-Time Article Feed (Instant View & PDF)")
        live_feed_container = st.container()

    def render_content_display(df_current, status_msg=None, key_suffix=None):
        if df_current is None or df_current.empty:
            live_status_box.info("👈 Enter titles on the left and click **Generate Unique Content & Export to Excel** to see articles appear in real time!")
            return

        import uuid
        ks = key_suffix or uuid.uuid4().hex[:6]
        articles_list = df_current.to_dict('records')
        total_articles = len(df_current)
        total_words = int(df_current['Word Count'].sum()) if 'Word Count' in df_current.columns else 0

        if status_msg:
            live_status_box.info(status_msg)
        else:
            live_status_box.success(f"✅ Generated {total_articles} article(s) ready! ({total_words:,} total words)")

        with live_metrics_box.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Articles Ready", f"{total_articles}")
            m2.metric("Total Words", f"{total_words:,}")
            m3.metric("Avg Words/Art.", f"{int(total_words / max(total_articles, 1)):,}")

        with live_downloads_box.container():
            st.write("#### 💾 Live Download Formats (Ready Immediately)")
            df_excel = df_current.copy()
            df_excel["Generated Content"] = df_excel["Generated Content"].apply(lambda x: str(x)[:32760] if len(str(x)) > 32760 else str(x))
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_excel.to_excel(writer, index=False, sheet_name='Unique Content')
            excel_bytes = excel_buffer.getvalue()
            csv_bytes = df_current.to_csv(index=False).encode('utf-8')
            combined_pdf_bytes = create_combined_pdf(articles_list)
            zip_pdf_bytes = create_articles_zip(articles_list)

            dl_c1, dl_c2 = st.columns(2)
            with dl_c1:
                st.download_button(
                    label=f"📥 Download Excel ({total_articles} Articles)",
                    data=excel_bytes,
                    file_name="StackBlitz_Unique_Content.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"btn_dl_excel_{total_articles}_{ks}"
                )
                st.download_button(
                    label=f"📄 Download CSV ({total_articles} Articles)",
                    data=csv_bytes,
                    file_name="StackBlitz_Unique_Content.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"btn_dl_csv_{total_articles}_{ks}"
                )
            with dl_c2:
                st.download_button(
                    label=f"📕 Download Combined PDF ({total_articles} Articles)",
                    data=combined_pdf_bytes,
                    file_name="StackBlitz_Unique_Content_All.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_dl_pdf_{total_articles}_{ks}"
                )
                st.download_button(
                    label=f"📦 Download All PDFs as ZIP ({total_articles} Articles)",
                    data=zip_pdf_bytes,
                    file_name="StackBlitz_Articles_PDFs.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key=f"btn_dl_zip_{total_articles}_{ks}"
                )

        with live_table_box.container():
            st.write("### 📋 Excel & PDF Table Summary")
            st.dataframe(df_current[["S.No", "Title", "Word Count", "Char Count"]], use_container_width=True)

    with col_ex1:
        st.subheader("📊 StackBlitz-Style Unique Content Generator")
        st.caption("Generate deep 3000+ words unique SEO articles for each title (no asterisks, phone interleaved every 8 words) and export directly into an Excel sheet (1 cell per content).")

        col_ex_cfg1, col_ex_cfg2 = st.columns([1, 1])
        with col_ex_cfg1:
            ex_phone_input = st.text_input("Toll-Free Support Phone Number", value="+1 888 308 7172", key="ex_phone_input")
        with col_ex_cfg2:
            ex_groq_key = st.text_input("Groq API Key (Fast 3000+ Words AI)", value=DEFAULT_GROQ_KEY, type="password", key="ex_groq_key")

        ex_titles_raw = st.text_area(
            "Enter Discussion/Article Titles (One title per line):",
            value="+1^888-308-7172 Trend Micro Cancel Subscription\n(fAq's\"'*1^888-308-7172)Cancel Trend Micro Subscription\nHow to cancel Norton subscription on iPhone?\nTrend Micro Won't Activate Follow the Complete Step-by-step\n1_888 308 7172 Forgot Yahoo Password\n1_888 308 7172 Old Yahoo Mail Login Recovery\nAt&T Email Address Complete Guide To Access\n1_888 308 7172 Yahoo Account E-Mail Sign-Up\nYahoo Account Hacked Recover: 1_888 308 7172\n1_888 308 7172 At&T Sbcglobal Email Password Reset\nSbcglobal Email Recovery 1_888 308 7172\nRecover Yahoo Mail Account 1_888 308 7172, Boston\n1_888 308 7172 How To Login Old Sbcglobal Email\n1_888 308 7172 How To Access At&T.Net Email Login\n1_888 308 7172 How Do I Login To My Sbcglobal Email",
            height=200,
            key="ex_titles_input"
        )

        ex_uploaded_file = st.file_uploader(
            "Or upload a .txt file containing titles",
            type=["txt"],
            key="ex_titles_file"
        )

        btn_gen = st.button("🚀 Generate Unique Content & Export to Excel", type="primary", use_container_width=True, key="btn_gen_excel")

        if btn_gen:
            ex_titles_list = []
            if ex_uploaded_file:
                content = ex_uploaded_file.read().decode("utf-8")
                ex_titles_list.extend([line.strip() for line in content.splitlines() if line.strip()])
            if ex_titles_raw:
                ex_titles_list.extend([line.strip() for line in ex_titles_raw.splitlines() if line.strip()])

            ex_titles_list = list(dict.fromkeys(ex_titles_list))

            if not ex_titles_list:
                st.error("Please enter or upload at least one title!")
            else:
                ex_progress = st.progress(0)
                ex_status = st.empty()

                rows = []
                for idx, title in enumerate(ex_titles_list):
                    cur_status = f"⏳ ({idx+1}/{len(ex_titles_list)}) Generating 3000+ words: **{title}**..."
                    ex_status.info(cur_status)
                    live_status_box.info(cur_status)

                    content_text = generate_proboards_content(
                        title=title,
                        phone=ex_phone_input,
                        groq_api_key=ex_groq_key
                    )

                    word_count = len(content_text.split())
                    char_count = len(content_text)
                    phone_tag_display = extract_phone_tag(title, ex_phone_input)

                    row_data = {
                        "S.No": idx + 1,
                        "Title": title,
                        "Generated Content": content_text,
                        "Word Count": word_count,
                        "Char Count": char_count,
                        "Phone Interleaved": phone_tag_display
                    }
                    rows.append(row_data)

                    current_df = pd.DataFrame(rows)
                    st.session_state.excel_content_df = current_df
                    ex_progress.progress((idx + 1) / len(ex_titles_list))

                    # LIVE ARTICLE EXPANDER DISPLAY: shows immediately as each article finishes!
                    with live_feed_container:
                        with st.expander(f"📄 #{idx+1} - {title} ({word_count:,} words | {char_count:,} chars)", expanded=True):
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.write(f"📞 **Phone Interleaved:** `{phone_tag_display}`")
                                st.write(f"📊 **Word Count:** {word_count:,} words | **Characters:** {char_count:,}")
                            with c2:
                                single_pdf_bytes = create_single_article_pdf(
                                    title=title,
                                    content=content_text,
                                    phone=phone_tag_display,
                                    word_count=word_count
                                )
                                clean_pdf_name = re.sub(r'[\\/*?:"<>|]', '', str(title))[:40].strip()
                                st.download_button(
                                    label=f"📕 Download Article #{idx+1} PDF",
                                    data=single_pdf_bytes,
                                    file_name=f"Article_{idx+1}_{clean_pdf_name}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key=f"live_btn_pdf_single_{idx}_{int(time.time()*1000)}"
                                )
                            st.text_area(
                                label="Full Generated Content (One Cell / Article):",
                                value=content_text,
                                height=220,
                                key=f"live_cell_preview_{idx}_{int(time.time()*1000)}"
                            )

                    # Update live download buttons, table, and metrics instantly!
                    render_content_display(current_df, status_msg=f"✅ Ready ({idx+1}/{len(ex_titles_list)}): {title}", key_suffix=f"step_{idx}")

                ex_status.success(f"✅ Finished generating all {len(ex_titles_list)} 3000+ words articles!")
                render_content_display(current_df, key_suffix="final_batch")
                st.balloons()
        else:
            # If not generating now, display existing session state if any
            if st.session_state.excel_content_df is not None and not st.session_state.excel_content_df.empty:
                df_existing = st.session_state.excel_content_df
                render_content_display(df_existing)
                with live_feed_container:
                    for index, row in df_existing.iterrows():
                        with st.expander(f"📄 #{row['S.No']} - {row['Title']} ({row['Word Count']} words | {row['Char Count']} chars)"):
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.write(f"📞 **Phone Interleaved:** `{row.get('Phone Interleaved', '')}`")
                                st.write(f"📊 **Word Count:** {row.get('Word Count', 0):,} words | **Characters:** {row.get('Char Count', 0):,}")
                            with c2:
                                single_pdf_bytes = create_single_article_pdf(
                                    title=row["Title"],
                                    content=row["Generated Content"],
                                    phone=row.get("Phone Interleaved", ""),
                                    word_count=row.get("Word Count", 0)
                                )
                                clean_pdf_name = re.sub(r'[\\/*?:"<>|]', '', str(row['Title']))[:40].strip()
                                st.download_button(
                                    label=f"📕 Download Article #{row['S.No']} PDF",
                                    data=single_pdf_bytes,
                                    file_name=f"Article_{row['S.No']}_{clean_pdf_name}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key=f"btn_pdf_single_{index}"
                                )
                            st.text_area(
                                label="Full Generated Content (One Cell / Article):",
                                value=row["Generated Content"],
                                height=220,
                                key=f"cell_preview_{index}"
                            )
            else:
                render_content_display(None)

# TAB 11: EDEN HOSPITALITY PDF UPLOADER
with mode[10]:
    col_ed1, col_ed2 = st.columns([1, 1], gap="large")

    if "eden_links" not in st.session_state:
        st.session_state.eden_links = []
        if os.path.exists("eden_uploaded_links.txt"):
            try:
                with open("eden_uploaded_links.txt", "r", encoding="utf-8") as ef:
                    st.session_state.eden_links = [l.strip() for l in ef if l.strip() and l.startswith("http")]
            except Exception:
                pass

    with col_ed1:
        st.subheader("🏨 Eden Hospitality Resume PDF Uploader")
        st.caption("Upload PDF resumes/documents directly to WPJobBoard on Eden Hospitality and obtain instant live public URLs.")

        ed_job_url = st.text_input("Target Job Application URL", value=DEFAULT_JOB_URL, key="sw_ed_job_url")

        ed_upload_mode = st.radio(
            "Upload Source:",
            ["📁 Upload My Own PDF(s)", "📦 Upload a ZIP of PDFs", "⚡ Auto-Generate Valid SEO PDF(s)"],
            horizontal=True,
            key="sw_ed_upload_mode"
        )

        ed_files_to_upload = []

        if ed_upload_mode == "📁 Upload My Own PDF(s)":
            ed_uploaded_files = st.file_uploader(
                "Choose one or more PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="sw_ed_pdf_uploader"
            )
            if ed_uploaded_files:
                for uf in ed_uploaded_files:
                    ed_files_to_upload.append({"name": uf.name, "bytes": uf.getvalue()})

        elif ed_upload_mode == "📦 Upload a ZIP of PDFs":
            ed_zip_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"], key="sw_ed_zip_uploader")
            if ed_zip_file:
                with zipfile.ZipFile(ed_zip_file) as z:
                    for filename in z.namelist():
                        if filename.lower().endswith(".pdf") and not filename.startswith("__MACOSX"):
                            ed_files_to_upload.append({"name": os.path.basename(filename), "bytes": z.read(filename)})
                st.info(f"Extracted {len(ed_files_to_upload)} PDF(s) from ZIP file.")

        else:
            ed_demo_titles = st.text_area(
                "Enter Custom PDF File Titles (one per line):",
                value="Executive_Resume_Dishwasher_Operations.pdf\nSenior_Hospitality_Lead_Profile.pdf\nKitchen_Operations_Resume.pdf",
                height=120,
                key="sw_ed_demo_titles"
            )
            if st.button("Generate Demo PDFs for Upload", key="sw_btn_gen_demo_eden"):
                titles_list = [t.strip() for t in ed_demo_titles.splitlines() if t.strip()]
                gen_list = []
                for t in titles_list:
                    pdf_b = create_single_article_pdf(title=t, content=f"Application and resume document for {t}.\nVerified hospitality submission.", phone="1 888 308 7172", word_count=20)
                    gen_list.append({"name": t if t.endswith(".pdf") else f"{t}.pdf", "bytes": pdf_b})
                st.session_state["sw_eden_generated_pdfs"] = gen_list
                st.success(f"Generated {len(gen_list)} valid PDF document(s) ready to upload!")

            if "sw_eden_generated_pdfs" in st.session_state and not ed_files_to_upload:
                ed_files_to_upload = st.session_state["sw_eden_generated_pdfs"]

        st.markdown("---")
        btn_eden_upload = st.button("🚀 Upload PDF(s) & Get Live Links", type="primary", use_container_width=True, key="sw_btn_eden_upload")

    with col_ed2:
        st.subheader("📋 Live Eden Uploaded URLs (Copy to Excel)")
        st.caption("Updates immediately after each PDF upload. Select all and copy directly into Excel!")

        ed_output_placeholder = st.empty()
        ed_count_placeholder = st.empty()
        ed_download_placeholder = st.empty()

        initial_ed_text = "\n".join(st.session_state.eden_links)
        ed_output_placeholder.text_area(
            label="Live Plain Text Uploaded Links Box:",
            value=initial_ed_text if initial_ed_text else "",
            height=320,
            key="sw_ed_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.eden_links:
            ed_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.eden_links)}")
            ed_download_placeholder.download_button(
                label="📥 Download Eden Links (.txt)",
                data=initial_ed_text,
                file_name="eden_uploaded_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="sw_ed_download_btn_init"
            )

        if st.button("🗑️ Clear Eden Links History", key="sw_btn_clear_eden"):
            st.session_state.eden_links = []
            if os.path.exists("eden_uploaded_links.txt"):
                try:
                    os.remove("eden_uploaded_links.txt")
                except Exception:
                    pass
            st.rerun()

        st.markdown("---")
        st.write("### 🔍 Live Upload Stream & Clickable Links")
        live_ed_container = st.container()

    if btn_eden_upload:
        if not ed_files_to_upload:
            st.error("Please select or generate at least one PDF to upload!")
        else:
            st.info(f"Starting upload of {len(ed_files_to_upload)} PDF(s)...")
            ed_progress = st.progress(0)
            ed_status = st.empty()

            for idx, item in enumerate(ed_files_to_upload):
                fname = item["name"]
                fbytes = item["bytes"]
                ed_status.text(f"Uploading ({idx+1}/{len(ed_files_to_upload)}): {fname}...")

                res = upload_pdf_to_eden(
                    file_source=fbytes,
                    filename=fname,
                    job_url=ed_job_url
                )

                ed_progress.progress((idx + 1) / len(ed_files_to_upload))

                if res.get("success") and res.get("url"):
                    live_url = res["url"]
                    if live_url not in st.session_state.eden_links:
                        st.session_state.eden_links.append(live_url)

                    cur_text = "\n".join(st.session_state.eden_links)
                    ed_output_placeholder.text_area(
                        label="Live Plain Text Uploaded Links Box:",
                        value=cur_text,
                        height=320,
                        key=f"sw_ed_text_area_live_{idx}",
                        help="Copy all links directly into Excel!"
                    )
                    ed_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.eden_links)}")
                    ed_download_placeholder.download_button(
                        label="📥 Download Eden Links (.txt)",
                        data=cur_text,
                        file_name="eden_uploaded_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"sw_ed_download_btn_live_{idx}"
                    )

                    with live_ed_container:
                        st.success(f"✅ **({idx + 1}/{len(ed_files_to_upload)}) {fname}** ({res.get('size', 0)} bytes) → [Open Live Uploaded PDF]({live_url})")
                else:
                    err = res.get("error", "Upload failed")
                    with live_ed_container:
                        st.error(f"❌ **({idx + 1}/{len(ed_files_to_upload)}) {fname}** → Error: {err}")

            if st.session_state.eden_links:
                st.balloons()
                st.success(f"🎉 Successfully uploaded {len(ed_files_to_upload)} PDF(s) to Eden Hospitality!")

# TAB 12: TENTH REVOLUTION PDF UPLOADER
with mode[11]:
    col_th1, col_th2 = st.columns([1, 1], gap="large")

    if "tenth_links" not in st.session_state:
        st.session_state.tenth_links = []
        if os.path.exists("tenth_uploaded_links.txt"):
            try:
                with open("tenth_uploaded_links.txt", "r", encoding="utf-8") as tf:
                    st.session_state.tenth_links = [l.strip() for l in tf if l.strip() and l.startswith("http")]
            except Exception:
                pass

    with col_th1:
        st.subheader("🏛️ Tenth Revolution Resume PDF Uploader")
        st.caption("Upload PDF documents/resumes directly to Tenth Revolution job applications and obtain instant live public URLs.")

        th_job_url = st.text_input("Target Job Application URL", value=TENTH_DEFAULT_JOB_URL, key="sw_th_job_url")

        th_upload_mode = st.radio(
            "Upload Source:",
            ["📁 Upload My Own PDF(s)", "📦 Upload a ZIP of PDFs", "⚡ Auto-Generate Valid SEO PDF(s)"],
            horizontal=True,
            key="sw_th_upload_mode"
        )

        th_files_to_upload = []

        if th_upload_mode == "📁 Upload My Own PDF(s)":
            th_uploaded_files = st.file_uploader(
                "Choose one or more PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="sw_th_pdf_uploader"
            )
            if th_uploaded_files:
                for uf in th_uploaded_files:
                    th_files_to_upload.append({"name": uf.name, "bytes": uf.getvalue()})

        elif th_upload_mode == "📦 Upload a ZIP of PDFs":
            th_zip_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"], key="sw_th_zip_uploader")
            if th_zip_file:
                with zipfile.ZipFile(th_zip_file) as z:
                    for filename in z.namelist():
                        if filename.lower().endswith(".pdf") and not filename.startswith("__MACOSX"):
                            th_files_to_upload.append({"name": os.path.basename(filename), "bytes": z.read(filename)})
                st.info(f"Extracted {len(th_files_to_upload)} PDF(s) from ZIP file.")

        else:
            th_demo_titles = st.text_area(
                "Enter Custom PDF File Titles (one per line):",
                value="Application_Consultant_D365_Resume.pdf\nSenior_Functional_Consultant_Profile.pdf\nEnterprise_Architect_Resume.pdf",
                height=120,
                key="sw_th_demo_titles"
            )
            if st.button("Generate Demo PDFs for Upload", key="sw_btn_gen_demo_tenth"):
                titles_list = [t.strip() for t in th_demo_titles.splitlines() if t.strip()]
                gen_list = []
                for t in titles_list:
                    pdf_b = create_single_article_pdf(title=t, content=f"Application and resume document for {t}.\nVerified Tenth Revolution consultant submission.", phone="1 888 308 7172", word_count=20)
                    gen_list.append({"name": t if t.endswith(".pdf") else f"{t}.pdf", "bytes": pdf_b})
                st.session_state["sw_tenth_generated_pdfs"] = gen_list
                st.success(f"Generated {len(gen_list)} valid PDF document(s) ready to upload!")

            if "sw_tenth_generated_pdfs" in st.session_state and not th_files_to_upload:
                th_files_to_upload = st.session_state["sw_tenth_generated_pdfs"]

        st.markdown("---")
        btn_tenth_upload = st.button("🚀 Upload PDF(s) to Tenth Revolution", type="primary", use_container_width=True, key="sw_btn_tenth_upload")

    with col_th2:
        st.subheader("📋 Live Tenth Revolution URLs (Copy to Excel)")
        st.caption("Updates immediately after each PDF upload. Select all and copy directly into Excel!")

        th_output_placeholder = st.empty()
        th_count_placeholder = st.empty()
        th_download_placeholder = st.empty()

        initial_th_text = "\n".join(st.session_state.tenth_links)
        th_output_placeholder.text_area(
            label="Live Plain Text Uploaded Links Box:",
            value=initial_th_text if initial_th_text else "",
            height=320,
            key="sw_th_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.tenth_links:
            th_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.tenth_links)}")
            th_download_placeholder.download_button(
                label="📥 Download Tenth Revolution Links (.txt)",
                data=initial_th_text,
                file_name="tenth_uploaded_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="sw_th_download_btn_init"
            )

        if st.button("🗑️ Clear Tenth Links History", key="sw_btn_clear_tenth"):
            st.session_state.tenth_links = []
            if os.path.exists("tenth_uploaded_links.txt"):
                try:
                    os.remove("tenth_uploaded_links.txt")
                except Exception:
                    pass
            st.rerun()

        st.markdown("---")
        st.write("### 🔍 Live Upload Stream & Clickable Links")
        live_th_container = st.container()

    if btn_tenth_upload:
        if not th_files_to_upload:
            st.error("Please select or generate at least one PDF to upload!")
        else:
            st.info(f"Starting upload of {len(th_files_to_upload)} PDF(s)...")
            th_progress = st.progress(0)
            th_status = st.empty()

            for idx, item in enumerate(th_files_to_upload):
                fname = item["name"]
                fbytes = item["bytes"]
                th_status.text(f"Uploading ({idx+1}/{len(th_files_to_upload)}): {fname}...")

                res = upload_pdf_to_tenth(
                    file_source=fbytes,
                    filename=fname,
                    job_url=th_job_url
                )

                th_progress.progress((idx + 1) / len(th_files_to_upload))

                if res.get("success") and res.get("url"):
                    live_url = res["url"]
                    if live_url not in st.session_state.tenth_links:
                        st.session_state.tenth_links.append(live_url)

                    cur_text = "\n".join(st.session_state.tenth_links)
                    th_output_placeholder.text_area(
                        label="Live Plain Text Uploaded Links Box:",
                        value=cur_text,
                        height=320,
                        key=f"sw_th_text_area_live_{idx}",
                        help="Copy all links directly into Excel!"
                    )
                    th_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.tenth_links)}")
                    th_download_placeholder.download_button(
                        label="📥 Download Tenth Revolution Links (.txt)",
                        data=cur_text,
                        file_name="tenth_uploaded_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"sw_th_download_btn_live_{idx}"
                    )

                    with live_th_container:
                        st.success(f"✅ **({idx + 1}/{len(th_files_to_upload)}) {fname}** ({res.get('size', 0)} bytes) → [Open Live Uploaded PDF]({live_url})")
                else:
                    err = res.get("error", "Upload failed")
                    with live_th_container:
                        st.error(f"❌ **({idx + 1}/{len(th_files_to_upload)}) {fname}** → Error: {err}")

            if st.session_state.tenth_links:
                st.balloons()
                st.success(f"🎉 Successfully uploaded {len(th_files_to_upload)} PDF(s) to Tenth Revolution!")

# TAB 13: USAL DIGITALSTACK MATRICULA PDF UPLOADER
with mode[12]:
    st.header("🎓 USAL Digitalstack Matricula PDF Uploader Bot")
    st.markdown(
        "Upload PDF files directly to **Universidad de Salamanca (USAL)** Digitalstack Matricula form: "
        "`https://digitalstack.usal.es/matricula`. Generates publicly accessible PDF links instantly."
    )
    st.info("📎 **Public Link Format:** `https://digitalstack.usal.es/sites/default/files/matriculas/<filename>`")

    col_usal1, col_usal2 = st.columns([1, 1], gap="large")

    usal_files_to_upload = []

    with col_usal1:
        st.subheader("📤 Step 1: Select or Generate PDF Files")

        usal_upload_mode = st.radio(
            "Choose Upload Source:",
            ["📂 Upload PDF Files", "📦 Upload a ZIP of PDFs", "✍️ Generate PDFs from Custom Titles"],
            key="sw_usal_upload_mode"
        )

        if usal_upload_mode == "📂 Upload PDF Files":
            usal_uploaded_files = st.file_uploader(
                "Upload PDF file(s):",
                type=["pdf"],
                accept_multiple_files=True,
                key="sw_usal_pdf_uploader"
            )
            if usal_uploaded_files:
                for uf in usal_uploaded_files:
                    usal_files_to_upload.append({"name": uf.name, "bytes": uf.getvalue()})

        elif usal_upload_mode == "📦 Upload a ZIP of PDFs":
            usal_zip_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"], key="sw_usal_zip_uploader")
            if usal_zip_file:
                with zipfile.ZipFile(usal_zip_file) as z:
                    for filename in z.namelist():
                        if filename.lower().endswith(".pdf") and not filename.startswith("__MACOSX"):
                            usal_files_to_upload.append({"name": os.path.basename(filename), "bytes": z.read(filename)})
                st.info(f"Extracted {len(usal_files_to_upload)} PDF(s) from ZIP file.")

        else:
            usal_demo_titles = st.text_area(
                "Enter Custom PDF File Titles (one per line):",
                value="Matricula_Curso_Fullstack_2026.pdf\nJustificante_Pago_Matricula.pdf\nCurriculum_Vitae_USAL.pdf",
                height=120,
                key="sw_usal_demo_titles"
            )
            if st.button("Generate Demo PDFs for Upload", key="sw_btn_gen_demo_usal"):
                titles_list = [t.strip() for t in usal_demo_titles.splitlines() if t.strip()]
                gen_list = []
                for t in titles_list:
                    pdf_b = create_single_article_pdf(title=t, content=f"Documento de matricula para {t}.\nVerificado USAL Digitalstack.", phone="1 888 308 7172", word_count=20)
                    gen_list.append({"name": t if t.endswith(".pdf") else f"{t}.pdf", "bytes": pdf_b})
                st.session_state["sw_usal_generated_pdfs"] = gen_list
                st.success(f"Generated {len(gen_list)} valid PDF document(s) ready to upload!")

            if "sw_usal_generated_pdfs" in st.session_state and not usal_files_to_upload:
                usal_files_to_upload = st.session_state["sw_usal_generated_pdfs"]

        st.markdown("---")
        usal_email = st.text_input("Correo electrónico:", value="estudiante@usal.es", key="sw_usal_email")
        usal_submit_form = st.checkbox("Submit Node Form (Save)", value=True, key="sw_usal_submit_form")

        btn_usal_upload = st.button("🚀 Upload PDF(s) to USAL Matricula", type="primary", use_container_width=True, key="sw_btn_usal_upload")

    with col_usal2:
        st.subheader("📋 Live USAL Matricula URLs (Copy to Excel)")
        st.caption("Updates immediately after each PDF upload. Select all and copy directly into Excel!")

        usal_output_placeholder = st.empty()
        usal_count_placeholder = st.empty()
        usal_download_placeholder = st.empty()

        initial_usal_text = "\n".join(st.session_state.usal_links)
        usal_output_placeholder.text_area(
            label="Live Plain Text Uploaded Links Box:",
            value=initial_usal_text if initial_usal_text else "",
            height=320,
            key="sw_usal_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.usal_links:
            usal_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.usal_links)}")
            usal_download_placeholder.download_button(
                label="📥 Download USAL Matricula Links (.txt)",
                data=initial_usal_text,
                file_name="usal_uploaded_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="sw_usal_download_btn_init"
            )

        if st.button("🗑️ Clear USAL Links History", key="sw_btn_clear_usal"):
            st.session_state.usal_links = []
            if os.path.exists("usal_uploaded_links.txt"):
                try:
                    os.remove("usal_uploaded_links.txt")
                except Exception:
                    pass
            st.rerun()

        st.markdown("---")
        st.write("### 🔍 Live Upload Stream & Clickable Links")
        live_usal_container = st.container()

    if btn_usal_upload:
        if not usal_files_to_upload:
            st.error("Please select or generate at least one PDF to upload!")
        else:
            st.info(f"Starting upload of {len(usal_files_to_upload)} PDF(s)...")
            usal_progress = st.progress(0)
            usal_status = st.empty()

            for idx, item in enumerate(usal_files_to_upload):
                fname = item["name"]
                fbytes = item["bytes"]
                usal_status.text(f"Uploading ({idx+1}/{len(usal_files_to_upload)}): {fname}...")

                res = upload_pdf_to_usal(
                    file_source=fbytes,
                    filename=fname,
                    email=usal_email,
                    submit_form=usal_submit_form
                )

                usal_progress.progress((idx + 1) / len(usal_files_to_upload))

                if res.get("success") and res.get("url"):
                    live_url = res["url"]
                    if live_url not in st.session_state.usal_links:
                        st.session_state.usal_links.append(live_url)

                    cur_text = "\n".join(st.session_state.usal_links)
                    usal_output_placeholder.text_area(
                        label="Live Plain Text Uploaded Links Box:",
                        value=cur_text,
                        height=320,
                        key=f"sw_usal_text_area_live_{idx}",
                        help="Copy all links directly into Excel!"
                    )
                    usal_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.usal_links)}")
                    usal_download_placeholder.download_button(
                        label="📥 Download USAL Matricula Links (.txt)",
                        data=cur_text,
                        file_name="usal_uploaded_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"sw_usal_download_btn_live_{idx}"
                    )

                    with live_usal_container:
                        st.success(f"✅ **({idx + 1}/{len(usal_files_to_upload)}) {fname}** ({res.get('size', 0)} bytes) → [Open Live Uploaded PDF]({live_url})")
                else:
                    err = res.get("error", "Upload failed")
                    with live_usal_container:
                        st.error(f"❌ **({idx + 1}/{len(usal_files_to_upload)}) {fname}** → Error: {err}")

            if st.session_state.usal_links:
                st.balloons()
                st.success(f"🎉 Successfully uploaded {len(usal_files_to_upload)} PDF(s) to USAL Digitalstack Matricula!")

# TAB 14: UFL INVASION SCIENCE AFFILIATE PDF UPLOADER
with mode[13]:
    st.header("🐊 UFL Invasion Science Affiliate PDF Uploader Bot")
    st.markdown(
        "Upload CV / Resume PDFs directly to **University of Florida (UFL) Invasion Science Institute** Affiliate Form: "
        "`https://invasionscience.ufl.edu/affiliation/become-an-affiliate/`."
    )
    st.info("📌 **Target Engine:** Forminator Module ID `1239` (WordPress Forminator AJAX)")

    col_ufl1, col_ufl2 = st.columns([1, 1], gap="large")

    ufl_files_to_upload = []

    with col_ufl1:
        st.subheader("📤 Step 1: Select or Generate CV PDF Files")

        ufl_upload_mode = st.radio(
            "Choose Upload Source:",
            ["📂 Upload PDF Files", "📦 Upload a ZIP of PDFs", "✍️ Generate PDFs from Custom Titles"],
            key="sw_ufl_upload_mode"
        )

        if ufl_upload_mode == "📂 Upload PDF Files":
            ufl_uploaded_files = st.file_uploader(
                "Upload CV / Resume PDF file(s):",
                type=["pdf", "doc", "docx"],
                accept_multiple_files=True,
                key="sw_ufl_pdf_uploader"
            )
            if ufl_uploaded_files:
                for uf in ufl_uploaded_files:
                    ufl_files_to_upload.append({"name": uf.name, "bytes": uf.getvalue()})

        elif ufl_upload_mode == "📦 Upload a ZIP of PDFs":
            ufl_zip_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"], key="sw_ufl_zip_uploader")
            if ufl_zip_file:
                with zipfile.ZipFile(ufl_zip_file) as z:
                    for filename in z.namelist():
                        if filename.lower().endswith((".pdf", ".doc", ".docx")) and not filename.startswith("__MACOSX"):
                            ufl_files_to_upload.append({"name": os.path.basename(filename), "bytes": z.read(filename)})
                st.info(f"Extracted {len(ufl_files_to_upload)} CV PDF(s) from ZIP file.")

        else:
            ufl_demo_titles = st.text_area(
                "Enter Applicant Name / File Titles (one per line):",
                value="Dr_Alex_Johnson_Invasion_Ecology_CV.pdf\nDr_Maria_Rodriguez_Plant_Pathology_CV.pdf\nDr_Sam_Taylor_Biosecurity_CV.pdf",
                height=120,
                key="sw_ufl_demo_titles"
            )
            if st.button("Generate Demo CV PDFs for Upload", key="sw_btn_gen_demo_ufl"):
                titles_list = [t.strip() for t in ufl_demo_titles.splitlines() if t.strip()]
                gen_list = []
                for t in titles_list:
                    pdf_b = create_single_article_pdf(title=t, content=f"Academic Curriculum Vitae for {t}.\nVerified University of Florida Invasion Science Affiliate submission.", phone="1 888 308 7172", word_count=25)
                    gen_list.append({"name": t if t.endswith(".pdf") else f"{t}.pdf", "bytes": pdf_b})
                st.session_state["sw_ufl_generated_pdfs"] = gen_list
                st.success(f"Generated {len(gen_list)} valid CV document(s) ready to upload!")

            if "sw_ufl_generated_pdfs" in st.session_state and not ufl_files_to_upload:
                ufl_files_to_upload = st.session_state["sw_ufl_generated_pdfs"]

        st.markdown("---")
        st.subheader("👤 Step 2: Applicant Default Info")
        ufl_applicant_name = st.text_input("Applicant Name:", value="Dr. Alex Johnson", key="sw_ufl_name")
        ufl_applicant_email = st.text_input("Applicant Email:", value="affiliate.applicant@ufl.edu", key="sw_ufl_email")
        ufl_applicant_title = st.text_input("Title / Department:", value="Assistant Professor of Invasion Ecology", key="sw_ufl_title")
        ufl_applicant_inst = st.text_input("Institution / Organization:", value="University of Florida", key="sw_ufl_inst")
        ufl_applicant_notes = st.text_area("Research Description / Notes:", value="Affiliation application with attached CV document.", height=80, key="sw_ufl_notes")

        btn_ufl_upload = st.button("🚀 Upload CV(s) to UFL Invasion Science Form", type="primary", use_container_width=True, key="sw_btn_ufl_upload")

    with col_ufl2:
        st.subheader("📋 Submitted Affiliate Submissions (Log)")
        st.caption("Updates immediately after each submission. Select all and copy directly into Excel!")

        ufl_output_placeholder = st.empty()
        ufl_count_placeholder = st.empty()
        ufl_download_placeholder = st.empty()

        initial_ufl_text = "\n".join(st.session_state.ufl_submissions)
        ufl_output_placeholder.text_area(
            label="Submissions Log Box:",
            value=initial_ufl_text if initial_ufl_text else "",
            height=320,
            key="sw_ufl_text_area_init",
            help="Copy all logs directly into Excel!"
        )

        if st.session_state.ufl_submissions:
            ufl_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.ufl_submissions)}")
            ufl_download_placeholder.download_button(
                label="📥 Download UFL Affiliate Links (.txt)",
                data=initial_ufl_text,
                file_name="ufl_uploaded_submissions.txt",
                mime="text/plain",
                use_container_width=True,
                key="sw_ufl_download_btn_init"
            )

        if st.button("🗑️ Clear UFL Affiliate Links History", key="sw_btn_clear_ufl"):
            st.session_state.ufl_submissions = []
            if os.path.exists("ufl_uploaded_submissions.txt"):
                try:
                    os.remove("ufl_uploaded_submissions.txt")
                except Exception:
                    pass
            st.rerun()

        st.markdown("---")
        st.write("### 🔍 Live Upload Stream & Clickable Links")
        live_ufl_container = st.container()

    if btn_ufl_upload:
        if not ufl_files_to_upload:
            st.error("Please select or generate at least one CV PDF to upload!")
        else:
            st.info(f"Starting upload of {len(ufl_files_to_upload)} CV PDF(s)...")
            ufl_progress = st.progress(0)
            ufl_status = st.empty()

            for idx, item in enumerate(ufl_files_to_upload):
                fname = item["name"]
                fbytes = item["bytes"]
                pname = f"{ufl_applicant_name} #{idx+1}" if len(ufl_files_to_upload) > 1 else ufl_applicant_name

                ufl_status.text(f"Uploading ({idx+1}/{len(ufl_files_to_upload)}): {fname} [{pname}]...")

                res = upload_pdf_to_ufl(
                    file_source=fbytes,
                    filename=fname,
                    name=pname,
                    email=ufl_applicant_email,
                    title=ufl_applicant_title,
                    institution=ufl_applicant_inst,
                    research_notes=ufl_applicant_notes
                )

                ufl_progress.progress((idx + 1) / len(ufl_files_to_upload))

                if res.get("success") and res.get("url"):
                    live_url = res["url"]
                    if live_url not in st.session_state.ufl_submissions:
                        st.session_state.ufl_submissions.append(live_url)

                    cur_text = "\n".join(st.session_state.ufl_submissions)
                    ufl_output_placeholder.text_area(
                        label="Live Plain Text Uploaded Links Box:",
                        value=cur_text,
                        height=320,
                        key=f"sw_ufl_text_area_live_{idx}",
                        help="Copy all logs directly into Excel!"
                    )
                    ufl_count_placeholder.success(f"Total Submitted CVs: {len(st.session_state.ufl_submissions)}")
                    ufl_download_placeholder.download_button(
                        label="📥 Download UFL Submissions Log (.txt)",
                        data=cur_text,
                        file_name="ufl_uploaded_submissions.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"sw_ufl_download_btn_live_{idx}"
                    )

                    with live_ufl_container:
                        st.success(f"✅ **({idx + 1}/{len(ufl_files_to_upload)}) {fname}** ({res.get('size', 0)} bytes) → Submitted for **{pname}**: *{msg}*")
                else:
                    err = res.get("error", "Submission failed")
                    with live_ufl_container:
                        st.error(f"❌ **({idx + 1}/{len(ufl_files_to_upload)}) {fname}** → Error: {err}")

            if st.session_state.ufl_submissions:
                st.balloons()
                st.success(f"🎉 Successfully submitted {len(ufl_files_to_upload)} CV PDF(s) to UFL Invasion Science Institute!")







