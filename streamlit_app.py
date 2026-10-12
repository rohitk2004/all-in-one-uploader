import streamlit as st
import asyncio
import os
import sys
import re
import time
import uuid

# Ensure current working directory is first in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def safe_print(*args, **kwargs):
    try:
        kwargs.pop("flush", None)
        print(*args, **kwargs)
    except Exception:
        pass

print = safe_print

import zipfile
import tempfile
import io
import pandas as pd
from fd_uploader import upload_pdf_to_fd
from capiaa_bot import upload_bulk_pdfs, process_uploaded_files
from firstory_bot import create_firstory_playlist, DEFAULT_EMAIL as FIRSTORY_EMAIL, DEFAULT_PASSWORD as FIRSTORY_PASS
from king_bot import create_king_discussion, register_king_account_visible, DEFAULT_EMAIL as KING_EMAIL, DEFAULT_PASSWORD as KING_PASS
from pdf_generator import create_valid_pdf
from unique_content_engine import generate_unique_description
from proboards_bot import create_proboards_thread, run_proboards_sync, generate_proboards_content, extract_phone_tag, DEFAULT_PHONE, DEFAULT_GROQ_KEY
from pdf_content_exporter import create_single_article_pdf, create_combined_pdf, create_articles_zip
from eden_uploader import upload_pdf_to_eden, batch_upload_pdfs, DEFAULT_JOB_URL
from tenth_uploader import upload_pdf_to_tenth, batch_upload_pdfs as batch_upload_tenth_pdfs, DEFAULT_JOB_URL as TENTH_DEFAULT_JOB_URL
from url_content_extractor import extract_url_content_playwright, create_docx_file, create_single_docx
from docx_articles_parser import parse_docx_articles

st.set_page_config(
    page_title="PDF & Forum Automation Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-weight: 700;
        font-size: 2.2rem;
    }
    
    .main-header p {
        color: #94A3B8;
        margin: 4px 0 0 0;
        font-size: 1rem;
    }
    
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stDownloadButton button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>⚡ PDF & Forum Automation Suite</h1>
    <p>Multi-Platform Document & Content Publishing Tools</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "📄 FD.org PDF Uploader",
    "🏢 CAPI AA Bulk PDF Uploader",
    "📻 Firstory Playlist Creator Bot",
    "👑 Community King Forum Bot",
    "📊 StackBlitz Excel Content Bot",
    "🌐 ProBoards Forum Bot (Naruto)",
    "🏨 Eden Hospitality PDF Uploader",
    "🏛️ Tenth Revolution PDF Uploader",
    "📥 Bulk URL Content Extractor (DOC Export)",
    "📑 Adminus ProBoards DOCX Poster",
    "🎮 Arcade Game Designer Bot",
    "💊 Quaalude ProBoards Bot"
])

# Session state initialization
if "fd_links" not in st.session_state:
    st.session_state.fd_links = []

if "capiaa_links" not in st.session_state:
    st.session_state.capiaa_links = []

if "firstory_links" not in st.session_state:
    st.session_state.firstory_links = []

if "king_links" not in st.session_state:
    st.session_state.king_links = []

if "excel_content_df" not in st.session_state:
    st.session_state.excel_content_df = None

if "proboards_links" not in st.session_state:
    st.session_state.proboards_links = []
    if os.path.exists("proboards_threads.txt"):
        try:
            with open("proboards_threads.txt", "r", encoding="utf-8") as pf:
                st.session_state.proboards_links = [l.strip() for l in pf if l.strip() and "/thread/" in l and "/thread/new/" not in l]
        except Exception:
            pass

if "eden_links" not in st.session_state:
    st.session_state.eden_links = []
    if os.path.exists("eden_uploaded_links.txt"):
        try:
            with open("eden_uploaded_links.txt", "r", encoding="utf-8") as ef:
                st.session_state.eden_links = [l.strip() for l in ef if l.strip() and l.startswith("http")]
        except Exception:
            pass

if "tenth_links" not in st.session_state:
    st.session_state.tenth_links = []
    if os.path.exists("tenth_uploaded_links.txt"):
        try:
            with open("tenth_uploaded_links.txt", "r", encoding="utf-8") as tf:
                st.session_state.tenth_links = [l.strip() for l in tf if l.strip() and l.startswith("http")]
        except Exception:
            pass

if "adminus_links" not in st.session_state:
    st.session_state.adminus_links = []
    if os.path.exists("adminus_threads.txt"):
        try:
            with open("adminus_threads.txt", "r", encoding="utf-8") as af:
                st.session_state.adminus_links = [l.strip() for l in af if l.strip() and "/thread/" in l and "/thread/new/" not in l]
        except Exception:
            pass

if "arcade_links" not in st.session_state:
    st.session_state.arcade_links = []
    if os.path.exists("arcade_threads.txt"):
        try:
            with open("arcade_threads.txt", "r", encoding="utf-8") as arf:
                st.session_state.arcade_links = [l.strip() for l in arf if l.strip() and "/thread/" in l and "/thread/new/" not in l]
        except Exception:
            pass

if "quaalude_links" not in st.session_state:
    st.session_state.quaalude_links = []
    if os.path.exists("quaalude_threads.txt"):
        try:
            with open("quaalude_threads.txt", "r", encoding="utf-8") as qf:
                st.session_state.quaalude_links = [l.strip() for l in qf if l.strip() and "/thread/" in l and "/thread/new/" not in l]
        except Exception:
            pass

# --- TAB 1: FD.org PDF Uploader ---
with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col2:
        st.subheader("📋 Live FD.org Links (Copy to Excel)")
        st.caption("Updates instantly after EACH file upload. Select all and copy directly into Excel!")
        fd_output_placeholder = st.empty()
        fd_count_placeholder = st.empty()
        fd_download_placeholder = st.empty()

        initial_fd_text = "\n".join(st.session_state.fd_links)
        fd_output_placeholder.text_area(
            label="Live Plain Text Links Box:",
            value=initial_fd_text if initial_fd_text else "",
            height=380,
            key="fd_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.fd_links:
            fd_count_placeholder.success(f"Total Created Links: {len(st.session_state.fd_links)}")
            fd_download_placeholder.download_button(
                label="📥 Download All Links (.txt)",
                data=initial_fd_text,
                file_name="fd_uploaded_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="fd_download_btn_init"
            )

    with col1:
        st.subheader("📄 FD.org Single / Zip PDF Uploader")
        st.caption("Target URL: `https://fd.org/form/form-submission` | Instant Cloudinary Uploads")

        fd_uploaded_files = st.file_uploader(
            "Choose PDF files or ZIP archive",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="fd_files"
        )

        fd_titles_raw = st.text_area(
            "Or enter custom PDF Titles (One title per line to generate & upload PDFs):",
            placeholder="How to setup total adblock guide\nHow to cancel total adblock subscription",
            height=120,
            key="fd_titles"
        )

        if st.button("🚀 Upload to FD.org & Stream Live Links", type="primary", use_container_width=True, key="btn_fd"):
            pdf_jobs = []

            if fd_uploaded_files:
                for uf in fd_uploaded_files:
                    if uf.name.lower().endswith('.zip'):
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            zip_path = os.path.join(tmp_dir, uf.name)
                            with open(zip_path, 'wb') as f:
                                f.write(uf.read())
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(tmp_dir)
                            for root, _, files in os.walk(tmp_dir):
                                for file in files:
                                    if file.lower().endswith('.pdf'):
                                        fp = os.path.join(root, file)
                                        with open(fp, 'rb') as pf:
                                            pdf_jobs.append((file.rsplit('.', 1)[0], pf.read()))
                    elif uf.name.lower().endswith('.pdf'):
                        pdf_jobs.append((uf.name.rsplit('.', 1)[0], uf.read()))

            if fd_titles_raw:
                t_list = [t.strip() for t in fd_titles_raw.splitlines() if t.strip()]
                for t in t_list:
                    pdf_bytes = create_valid_pdf(t)
                    pdf_jobs.append((t, pdf_bytes))

            if not pdf_jobs:
                st.error("Please upload PDF/ZIP files or enter text titles to generate PDFs!")
            else:
                st.info(f"Processing {len(pdf_jobs)} PDF upload(s)...")
                fd_progress_bar = st.progress(0)
                fd_status_text = st.empty()
                fd_live_container = st.container()

                async def run_fd_batch():
                    for idx, (title, pdf_data) in enumerate(pdf_jobs):
                        fd_status_text.text(f"Uploading ({idx + 1}/{len(pdf_jobs)}): {title}...")
                        res = await upload_pdf_to_fd(title, pdf_data)
                        fd_progress_bar.progress((idx + 1) / len(pdf_jobs))

                        if res.get("success") and res.get("url"):
                            url = res["url"]
                            if url not in st.session_state.fd_links:
                                st.session_state.fd_links.append(url)

                            with open("fd_uploaded_links.txt", "a", encoding="utf-8") as out:
                                out.write(f"{url}\n")

                            curr_text = "\n".join(st.session_state.fd_links)
                            fd_output_placeholder.text_area(
                                label="Live Plain Text Links Box:",
                                value=curr_text,
                                height=380,
                                key=f"fd_text_area_live_{idx}",
                                help="Copy all links directly into Excel!"
                            )
                            fd_count_placeholder.success(f"Total Created Links: {len(st.session_state.fd_links)}")
                            fd_download_placeholder.download_button(
                                label="📥 Download All Links (.txt)",
                                data=curr_text,
                                file_name="fd_uploaded_links.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key=f"fd_download_btn_live_{idx}"
                            )

                            with fd_live_container:
                                st.write(f"✅ **({idx + 1}/{len(pdf_jobs)}) {title}** → [View Document]({url})")
                        else:
                            err = res.get("error", "Unknown error")
                            with fd_live_container:
                                st.write(f"❌ **({idx + 1}/{len(pdf_jobs)}) {title}** → Error: {err}")

                    if st.session_state.fd_links:
                        st.balloons()
                        st.success(f"Finished uploading all {len(pdf_jobs)} document(s)!")

                asyncio.run(run_fd_batch())

# --- TAB 2: CAPI AA Bulk PDF Uploader ---
with tab2:
    col1, col2 = st.columns([1, 1], gap="large")

    with col2:
        st.subheader("📋 Live CAPI AA Links (Copy to Excel)")
        st.caption("Updates instantly after EACH file upload. Select all and copy directly into Excel!")
        capiaa_output_placeholder = st.empty()
        capiaa_count_placeholder = st.empty()
        capiaa_download_placeholder = st.empty()

        initial_capiaa_text = "\n".join(st.session_state.capiaa_links)
        capiaa_output_placeholder.text_area(
            label="Live Plain Text CAPI AA Links Box:",
            value=initial_capiaa_text if initial_capiaa_text else "",
            height=380,
            key="capiaa_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.capiaa_links:
            capiaa_count_placeholder.success(f"Total Created Links: {len(st.session_state.capiaa_links)}")
            capiaa_download_placeholder.download_button(
                label="📥 Download CAPI AA Links (.txt)",
                data=initial_capiaa_text,
                file_name="capiaa_uploaded_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="capiaa_download_btn_init"
            )

    with col1:
        st.subheader("🏢 CAPI AA Bulk PDF Uploader")
        st.caption("Target URL: `https://capiaa.org/members/claim-form.php` | Direct Form Submissions")

        capiaa_uploaded_files = st.file_uploader(
            "Choose PDF files or ZIP archive for CAPI AA",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="capiaa_files"
        )

        capiaa_titles_raw = st.text_area(
            "Or enter custom PDF Titles (One title per line):",
            placeholder="How to setup total adblock guide\nHow to cancel total adblock subscription",
            height=120,
            key="capiaa_titles"
        )

        if st.button("🚀 Upload to CAPI AA & Stream Live Links", type="primary", use_container_width=True, key="btn_capiaa"):
            capiaa_jobs = []

            if capiaa_uploaded_files:
                for uf in capiaa_uploaded_files:
                    if uf.name.lower().endswith('.zip'):
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            zip_path = os.path.join(tmp_dir, uf.name)
                            with open(zip_path, 'wb') as f:
                                f.write(uf.read())
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(tmp_dir)
                            for root, _, files in os.walk(tmp_dir):
                                for file in files:
                                    if file.lower().endswith('.pdf'):
                                        fp = os.path.join(root, file)
                                        with open(fp, 'rb') as pf:
                                            capiaa_jobs.append((file.rsplit('.', 1)[0], pf.read()))
                    elif uf.name.lower().endswith('.pdf'):
                        capiaa_jobs.append((uf.name.rsplit('.', 1)[0], uf.read()))

            if capiaa_titles_raw:
                t_list = [t.strip() for t in capiaa_titles_raw.splitlines() if t.strip()]
                for t in t_list:
                    pdf_bytes = create_valid_pdf(t)
                    capiaa_jobs.append((t, pdf_bytes))

            if not capiaa_jobs:
                st.error("Please upload PDF/ZIP files or enter text titles for CAPI AA!")
            else:
                st.info(f"Processing {len(capiaa_jobs)} CAPI AA upload(s)...")
                capiaa_progress_bar = st.progress(0)
                capiaa_status_text = st.empty()
                capiaa_live_container = st.container()

                async def run_capiaa_batch():
                    for idx, (title, pdf_data) in enumerate(capiaa_jobs):
                        capiaa_status_text.text(f"Uploading CAPI AA ({idx + 1}/{len(capiaa_jobs)}): {title}...")
                        res = await upload_bulk_pdfs([(title, pdf_data)])
                        capiaa_progress_bar.progress((idx + 1) / len(capiaa_jobs))

                        if res and len(res) > 0 and res[0].get("success") and res[0].get("url"):
                            url = res[0]["url"]
                            if url not in st.session_state.capiaa_links:
                                st.session_state.capiaa_links.append(url)

                            with open("capiaa_uploaded_links.txt", "a", encoding="utf-8") as out:
                                out.write(f"{url}\n")

                            curr_text = "\n".join(st.session_state.capiaa_links)
                            capiaa_output_placeholder.text_area(
                                label="Live Plain Text CAPI AA Links Box:",
                                value=curr_text,
                                height=380,
                                key=f"capiaa_text_area_live_{idx}",
                                help="Copy all links directly into Excel!"
                            )
                            capiaa_count_placeholder.success(f"Total Created Links: {len(st.session_state.capiaa_links)}")
                            capiaa_download_placeholder.download_button(
                                label="📥 Download CAPI AA Links (.txt)",
                                data=curr_text,
                                file_name="capiaa_uploaded_links.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key=f"capiaa_download_btn_live_{idx}"
                            )

                            with capiaa_live_container:
                                st.write(f"✅ **({idx + 1}/{len(capiaa_jobs)}) {title}** → [View Document]({url})")
                        else:
                            err = res[0].get("error", "Unknown error") if res else "Failed"
                            with capiaa_live_container:
                                st.write(f"❌ **({idx + 1}/{len(capiaa_jobs)}) {title}** → Error: {err}")

                    if st.session_state.capiaa_links:
                        st.balloons()
                        st.success(f"Finished uploading all {len(capiaa_jobs)} CAPI AA document(s)!")

                asyncio.run(run_capiaa_batch())

# --- TAB 3: Firstory Playlist Creator Bot ---
with tab3:
    col1, col2 = st.columns([1, 1], gap="large")

    with col2:
        st.subheader("📋 Live Firstory Playlist Links (Copy to Excel)")
        st.caption("Updates instantly after EACH playlist creation. Select all and copy directly into Excel!")
        firstory_output_placeholder = st.empty()
        firstory_count_placeholder = st.empty()
        firstory_download_placeholder = st.empty()

        initial_firstory_text = "\n".join(st.session_state.firstory_links)
        firstory_output_placeholder.text_area(
            label="Live Plain Text Playlist Links Box:",
            value=initial_firstory_text if initial_firstory_text else "",
            height=380,
            key="firstory_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.firstory_links:
            firstory_count_placeholder.success(f"Total Created Playlists: {len(st.session_state.firstory_links)}")
            firstory_download_placeholder.download_button(
                label="📥 Download Firstory Links (.txt)",
                data=initial_firstory_text,
                file_name="firstory_playlist_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="firstory_download_btn_init"
            )

    with col1:
        st.subheader("📻 Firstory Podcast Playlist Creator Bot")
        st.caption("Target Login: `https://studio.firstory.me/login` | Audio Podcast Publishing")

        email_input = st.text_input("Firstory Account Email", value=FIRSTORY_EMAIL, key="firstory_email")
        password_input = st.text_input("Firstory Password", value=FIRSTORY_PASS, type="password", key="firstory_pass")
        headless_mode = st.toggle("Headless Mode (Background Browser)", value=False, key="firstory_headless")

        titles_raw = st.text_area(
            "Enter Podcast Titles (One title per line):",
            value="How to cancel Total Adblock subscription",
            height=140,
            key="firstory_titles_input"
        )

        uploaded_file = st.file_uploader(
            "Or upload a .txt file containing podcast titles",
            type=["txt"],
            key="firstory_titles_file"
        )

        if st.button("🚀 Start Firstory Bot & Stream Live Links", type="primary", use_container_width=True, key="btn_firstory"):
            titles_list = []

            if uploaded_file:
                content = uploaded_file.read().decode("utf-8")
                titles_list.extend([line.strip() for line in content.splitlines() if line.strip()])

            if titles_raw:
                titles_list.extend([line.strip() for line in titles_raw.splitlines() if line.strip()])

            titles_list = list(dict.fromkeys(titles_list))

            if not titles_list:
                st.error("Please enter or upload at least one title!")
            else:
                st.info(f"Processing {len(titles_list)} podcast title(s)...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                live_list_container = st.container()

                async def run_firstory_batch():
                    for idx, title in enumerate(titles_list):
                        status_text.text(f"Creating Playlist ({idx + 1}/{len(titles_list)}): {title}...")
                        res = await create_firstory_playlist(
                            title=title,
                            email=email_input,
                            password=password_input,
                            headless=headless_mode
                        )
                        progress_bar.progress((idx + 1) / len(titles_list))

                        if res.get("success") and res.get("url"):
                            url = res["url"]
                            if url not in st.session_state.firstory_links:
                                st.session_state.firstory_links.append(url)

                            with open("firstory_playlist_links.txt", "a", encoding="utf-8") as out:
                                out.write(f"{url}\n")

                            curr_text = "\n".join(st.session_state.firstory_links)
                            firstory_output_placeholder.text_area(
                                label="Live Plain Text Playlist Links Box:",
                                value=curr_text,
                                height=380,
                                key=f"firstory_text_area_live_{idx}",
                                help="Copy all links directly into Excel!"
                            )
                            firstory_count_placeholder.success(f"Total Created Playlists: {len(st.session_state.firstory_links)}")
                            firstory_download_placeholder.download_button(
                                label="📥 Download Firstory Links (.txt)",
                                data=curr_text,
                                file_name="firstory_playlist_links.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key=f"firstory_download_btn_live_{idx}"
                            )

                            with live_list_container:
                                st.write(f"✅ **({idx + 1}/{len(titles_list)}) {title}** → [Playlist Link]({url})")
                        else:
                            err = res.get("error", "Unknown error")
                            with live_list_container:
                                st.write(f"❌ **({idx + 1}/{len(titles_list)}) {title}** → Error: {err}")

                if st.session_state.firstory_links:
                    st.balloons()
                    st.success(f"Finished processing all {len(titles_list)} playlist(s)!")

                asyncio.run(run_firstory_batch())

# --- TAB 4: Community King Forum Bot ---
with tab4:
    col1, col2 = st.columns([1, 1], gap="large")

    with col2:
        st.subheader("📋 Live Community King Forum Links (Copy to Excel)")
        st.caption("Updates instantly after EACH thread creation. Select all and copy directly into Excel!")
        king_output_placeholder = st.empty()
        king_count_placeholder = st.empty()
        king_download_placeholder = st.empty()

        initial_king_text = "\n".join(st.session_state.king_links)
        king_output_placeholder.text_area(
            label="Live Plain Text Thread Links Box:",
            value=initial_king_text if initial_king_text else "",
            height=380,
            key="king_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.king_links:
            king_count_placeholder.success(f"Total Created Threads: {len(st.session_state.king_links)}")
            king_download_placeholder.download_button(
                label="📥 Download King Thread Links (.txt)",
                data=initial_king_text,
                file_name="king_thread_links.txt",
                mime="text/plain",
                use_container_width=True,
                key="king_download_btn_init"
            )

    with col1:
        st.subheader("👑 Community King (Candy Crush) Forum Bot")
        st.caption("Target Login: `https://community.king.com/en/candy-crush-friends-saga/entry/signin` | Forum Discussions")

        k_email_input = st.text_input("King Account Email", value=KING_EMAIL, key="king_email")
        k_password_input = st.text_input("King Password", value=KING_PASS, type="password", key="king_pass")
        k_auto_register = st.toggle("🔄 Auto-Register New Account Every 2 Posts (Opens Visible Window for Captcha Click)", value=True, key="king_auto_register")
        k_headless = st.toggle("Headless Mode (Background Browser for Posting)", value=False, key="king_headless")

        k_titles_raw = st.text_area(
            "Enter Discussion Titles (One title per line):",
            value="Why Is AVG Activation Not Working? (Causes + Step-by-Step Solution)\nHow to Confirm Your Bitdefender Purchase & Retrieve Your Key\nHow to Set Up PC Matic for Beginners (Simple Step-by-Step Setup)",
            height=140,
            key="king_titles_input"
        )

        k_uploaded_file = st.file_uploader(
            "Or upload a .txt file containing thread titles",
            type=["txt"],
            key="king_titles_file"
        )

        col_btn1, col_btn2 = st.columns([1, 1])
        if st.button("🚀 Start Community King Bot & Stream Live Links", type="primary", use_container_width=True, key="btn_king"):
            k_titles_list = []

            if k_uploaded_file:
                content = k_uploaded_file.read().decode("utf-8")
                k_titles_list.extend([line.strip() for line in content.splitlines() if line.strip()])

            if k_titles_raw:
                k_titles_list.extend([line.strip() for line in k_titles_raw.splitlines() if line.strip()])

            k_titles_list = list(dict.fromkeys(k_titles_list))

            if not k_titles_list:
                st.error("Please enter or upload at least one thread title!")
            else:
                st.info(f"Processing {len(k_titles_list)} thread title(s)...")
                k_progress_bar = st.progress(0)
                k_status_text = st.empty()
                k_live_container = st.container()

                async def run_king_batch():
                    active_email = k_email_input
                    active_password = k_password_input

                    for idx, title in enumerate(k_titles_list):
                        # Trigger registration on post #1 or every 2 posts if auto-register is enabled
                        should_register = k_auto_register and (idx % 2 == 0)

                        if should_register:
                            k_status_text.text(f"Opening visible window to Register New Account for posts #{idx+1} & #{idx+2}... Please click reCAPTCHA!")
                            st.warning(f"🔔 [Action Required] Opening visible registration window on King.com. Please click the reCAPTCHA box in the open browser!")
                        else:
                            k_status_text.text(f"Creating Discussion ({idx + 1}/{len(k_titles_list)}) using [{active_email}]: {title}...")

                        res = await create_king_discussion(
                            title=title,
                            email=active_email,
                            password=active_password,
                            headless=k_headless,
                            do_register=should_register
                        )
                        k_progress_bar.progress((idx + 1) / len(k_titles_list))

                        if res.get("email"):
                            active_email = res["email"]
                            if res.get("password"):
                                active_password = res["password"]

                        if res.get("success") and res.get("public_url"):
                            url = res["public_url"]
                            if url not in st.session_state.king_links:
                                st.session_state.king_links.append(url)

                            with open("king_thread_links.txt", "a", encoding="utf-8") as out:
                                out.write(f"{url}\n")

                            curr_text = "\n".join(st.session_state.king_links)
                            king_output_placeholder.text_area(
                                label="Live Plain Text Thread Links Box:",
                                value=curr_text,
                                height=380,
                                key=f"king_text_area_live_{idx}",
                                help="Copy all links directly into Excel!"
                            )
                            king_count_placeholder.success(f"Total Created Threads: {len(st.session_state.king_links)}")
                            king_download_placeholder.download_button(
                                label="📥 Download King Thread Links (.txt)",
                                data=curr_text,
                                file_name="king_thread_links.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key=f"king_download_btn_live_{idx}"
                            )

                            with k_live_container:
                                st.write(f"✅ **({idx + 1}/{len(k_titles_list)}) {title}** → [{active_email}] → [Thread Link]({url})")
                        else:
                            err = res.get("error", "Unknown error")
                            with k_live_container:
                                st.write(f"❌ **({idx + 1}/{len(k_titles_list)}) {title}** → Error: {err}")

                    if st.session_state.king_links:
                        st.balloons()
                        st.success(f"Finished creating all {len(k_titles_list)} discussion(s)!")

                asyncio.run(run_king_batch())

# --- TAB 5: StackBlitz Excel Content Generator ---
with tab5:
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
        st.caption("Generate deep 3000+ words unique SEO articles for each title (no asterisks, phone interleaved every 8 words) and export directly to Excel (1 cell per article).")

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

# --- TAB 6: Mormon Teen (ProBoards) Forum Bot ---
with tab6:
    col_pb1, col_pb2 = st.columns([1, 1], gap="large")

    with col_pb2:
        st.subheader("📋 Live ProBoards Forum Links (Copy to Excel)")
        st.caption("Updates instantly after EACH thread creation. Select all and copy directly into Excel!")
        pb_output_placeholder = st.empty()
        pb_count_placeholder = st.empty()
        pb_download_placeholder = st.empty()

        initial_pb_text = "\n".join(st.session_state.proboards_links)
        pb_output_placeholder.text_area(
            label="Live Plain Text Thread Links Box:",
            value=initial_pb_text if initial_pb_text else "",
            height=380,
            key="pb_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.proboards_links:
            pb_count_placeholder.success(f"Total Created Threads: {len(st.session_state.proboards_links)}")
            pb_download_placeholder.download_button(
                label="📥 Download ProBoards Links (.txt)",
                data=initial_pb_text,
                file_name="proboards_threads.txt",
                mime="text/plain",
                use_container_width=True,
                key="pb_download_btn_init"
            )

    with col_pb1:
        st.subheader("🌐 Mormon Teen (ProBoards) Forum Bot")
        st.caption("Target Board: `https://mormonteenworld.proboards.com/thread/new/27` | Guest Posting")

        col_cfg1, col_cfg2 = st.columns([1, 1])
        with col_cfg1:
            pb_guest_name = st.text_input("Guest Name", value="Alex Parker", key="pb_guest_name_input")
        with col_cfg2:
            pb_phone_input = st.text_input("Support Toll-Free Phone", value="+1 888 308 7172", key="pb_phone_input")

        pb_groq_key = st.text_input("Groq API Key (StackBlitz-Style High-Speed AI)", value=DEFAULT_GROQ_KEY, type="password", key="pb_groq_key")

        post_mode = st.radio("Posting Mode", ["Single Thread Post", "Batch Posting (Multiple Titles)"], horizontal=True, key="pb_post_mode")

        if post_mode == "Single Thread Post":
            pb_subject = st.text_input(
                "Thread Subject / Title",
                value="《FAQ'S™》1 888 308 7172 How to Cancel Norton Subscription",
                key="pb_single_subject"
            )

            col_gen, _ = st.columns([1, 1])
            if col_gen.button("✨ Auto-Generate StackBlitz Content for This Title", key="btn_gen_single_content"):
                with st.spinner("Generating authentic content with Groq..."):
                    gen_txt = generate_proboards_content(title=pb_subject, phone=pb_phone_input, groq_api_key=pb_groq_key)
                    st.session_state.pb_single_content_val = gen_txt

            if "pb_single_content_val" not in st.session_state:
                st.session_state.pb_single_content_val = "Click '✨ Auto-Generate StackBlitz Content for This Title' above to generate 3000+ words unique content with Groq AI, or enter your custom content here."
            single_val = st.session_state.pb_single_content_val

            pb_content = st.text_area(
                "Thread Content (StackBlitz Style):",
                value=single_val,
                height=220,
                key="pb_single_content_area"
            )
            pb_titles_list = [pb_subject] if pb_subject.strip() else []
        else:
            pb_titles_raw = st.text_area(
                "Enter Thread Titles (One title per line):",
                value="+1^888-308-7172 Trend Micro Cancel Subscription\n(fAq's\"'*1^888-308-7172)Cancel Trend Micro Subscription\nHow to cancel Norton subscription on iPhone?\nTrend Micro Won't Activate Follow the Complete Step-by-step\n1_888 308 7172 Forgot Yahoo Password\n1_888 308 7172 Old Yahoo Mail Login Recovery\nAt&T Email Address Complete Guide To Access\n1_888 308 7172 Yahoo Account E-Mail Sign-Up\nYahoo Account Hacked Recover: 1_888 308 7172\n1_888 308 7172 At&T Sbcglobal Email Password Reset\nSbcglobal Email Recovery 1_888 308 7172\nRecover Yahoo Mail Account 1_888 308 7172, Boston\n1_888 308 7172 How To Login Old Sbcglobal Email\n1_888 308 7172 How To Access At&T.Net Email Login\n1_888 308 7172 How Do I Login To My Sbcglobal Email",
                height=180,
                key="pb_batch_titles_input"
            )
            pb_uploaded_file = st.file_uploader(
                "Or upload a .txt file containing thread titles",
                type=["txt"],
                key="pb_titles_file"
            )
            pb_auto_content = st.checkbox("Auto-generate StackBlitz-style unique content for each title using Groq AI", value=True, key="pb_auto_content")
            pb_custom_content = ""
            if not pb_auto_content:
                pb_custom_content = st.text_area("Default Content for all titles:", value="Hello everyone! Looking forward to hearing your thoughts and experiences on this topic.", height=100, key="pb_custom_default_content")

            pb_titles_list = []
            if pb_uploaded_file:
                content_file = pb_uploaded_file.read().decode("utf-8")
                pb_titles_list.extend([line.strip() for line in content_file.splitlines() if line.strip()])
            if pb_titles_raw:
                pb_titles_list.extend([line.strip() for line in pb_titles_raw.splitlines() if line.strip()])
            pb_titles_list = list(dict.fromkeys(pb_titles_list))

        pb_timeout = st.slider("Timeout waiting for Captcha / Publish (seconds)", min_value=60, max_value=300, value=180, step=30, key="pb_timeout_slider")

        st.info("💡 **Browser Workflow**: Bot launches a real visible Chromium window, fills Guest Name, Subject & Content, clicks 'Create Thread', checks Terms of Service automatically. Solve the reCAPTCHA if prompted, and the bot will capture the published live link instantly!")

        if st.button("🚀 Start ProBoards Forum Bot", type="primary", use_container_width=True, key="btn_pb_start"):
            if not pb_titles_list:
                st.error("Please provide at least one subject / title!")
            else:
                st.write(f"🔄 Starting bot for {len(pb_titles_list)} thread(s)...")
                pb_progress_bar = st.progress(0)
                pb_status = st.empty()
                live_pb_container = st.container()

                for idx, t_title in enumerate(pb_titles_list):
                    pb_status.info(f"⏳ Processing ({idx + 1}/{len(pb_titles_list)}): **{t_title}** - Browser is opening...")

                    if post_mode == "Single Thread Post":
                        t_content = pb_content
                    else:
                        if pb_auto_content:
                            try:
                                t_content = generate_proboards_content(title=t_title, phone=pb_phone_input, groq_api_key=pb_groq_key)
                            except Exception:
                                t_content = f"Hello friends!\n\nI wanted to open up a discussion about '{t_title}'. For live support dial {pb_phone_input}."
                        else:
                            t_content = pb_custom_content if pb_custom_content else f"Discussion on {t_title}"

                    # Run sync
                    res = run_proboards_sync(
                        guest_name=pb_guest_name,
                        subject=t_title,
                        content=t_content,
                        timeout_sec=pb_timeout,
                        groq_api_key=pb_groq_key
                    )

                    pb_progress_bar.progress((idx + 1) / len(pb_titles_list))

                    if res.get("success") and res.get("url"):
                        new_url = res["url"]
                        if new_url not in st.session_state.proboards_links:
                            st.session_state.proboards_links.append(new_url)

                        updated_pb_text = "\n".join(st.session_state.proboards_links)
                        pb_output_placeholder.text_area(
                            label="Live Plain Text Thread Links Box:",
                            value=updated_pb_text,
                            height=380,
                            key=f"pb_text_area_live_{idx}",
                            help="Copy all links directly into Excel!"
                        )
                        pb_count_placeholder.success(f"Total Created Threads: {len(st.session_state.proboards_links)}")
                        pb_download_placeholder.download_button(
                            label="📥 Download ProBoards Links (.txt)",
                            data=updated_pb_text,
                            file_name="proboards_threads.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"pb_download_btn_live_{idx}"
                        )

                        with live_pb_container:
                            st.success(f"✅ **({idx + 1}/{len(pb_titles_list)}) {t_title}** → [Created Thread Link]({new_url})")
                    else:
                        err_msg = res.get("error", "Unknown error or timeout")
                        with live_pb_container:
                            st.error(f"❌ **({idx + 1}/{len(pb_titles_list)}) {t_title}** → Error: {err_msg}")

                if st.session_state.proboards_links:
                    st.balloons()
                    st.success(f"🎉 Completed all {len(pb_titles_list)} thread(s)!")

# --- TAB 7: Eden Hospitality PDF Uploader ---
with tab7:
    col_ed1, col_ed2 = st.columns([1, 1], gap="large")

    with col_ed1:
        st.subheader("🏨 Eden Hospitality Resume PDF Uploader")
        st.caption("Upload PDF resumes/documents directly to WPJobBoard on Eden Hospitality and obtain instant live public URLs.")

        ed_job_url = st.text_input("Target Job Application URL", value=DEFAULT_JOB_URL, key="ed_job_url")

        ed_upload_mode = st.radio(
            "Upload Source:",
            ["📁 Upload My Own PDF(s)", "📦 Upload a ZIP of PDFs", "⚡ Auto-Generate Valid SEO PDF(s)"],
            horizontal=True,
            key="ed_upload_mode"
        )

        ed_files_to_upload = []

        if ed_upload_mode == "📁 Upload My Own PDF(s)":
            ed_uploaded_files = st.file_uploader(
                "Choose one or more PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="ed_pdf_uploader"
            )
            if ed_uploaded_files:
                for uf in ed_uploaded_files:
                    ed_files_to_upload.append({"name": uf.name, "bytes": uf.getvalue()})

        elif ed_upload_mode == "📦 Upload a ZIP of PDFs":
            ed_zip_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"], key="ed_zip_uploader")
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
                key="ed_demo_titles"
            )
            if st.button("Generate Demo PDFs for Upload", key="btn_gen_demo_eden"):
                titles_list = [t.strip() for t in ed_demo_titles.splitlines() if t.strip()]
                gen_list = []
                for t in titles_list:
                    pdf_b = create_single_article_pdf(title=t, content=f"Application and resume document for {t}.\nVerified hospitality submission.", phone="1 888 308 7172", word_count=20)
                    gen_list.append({"name": t if t.endswith(".pdf") else f"{t}.pdf", "bytes": pdf_b})
                st.session_state["eden_generated_pdfs"] = gen_list
                st.success(f"Generated {len(gen_list)} valid PDF document(s) ready to upload!")

            if "eden_generated_pdfs" in st.session_state and not ed_files_to_upload:
                ed_files_to_upload = st.session_state["eden_generated_pdfs"]

        st.markdown("---")
        btn_eden_upload = st.button("🚀 Upload PDF(s) & Get Live Links", type="primary", use_container_width=True, key="btn_eden_upload")

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
            key="ed_text_area_init",
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
                key="ed_download_btn_init"
            )

        if st.button("🗑️ Clear Eden Links History", key="btn_clear_eden"):
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
                        key=f"ed_text_area_live_{idx}",
                        help="Copy all links directly into Excel!"
                    )
                    ed_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.eden_links)}")
                    ed_download_placeholder.download_button(
                        label="📥 Download Eden Links (.txt)",
                        data=cur_text,
                        file_name="eden_uploaded_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"ed_download_btn_live_{idx}"
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

# --- TAB 8: Tenth Revolution PDF Uploader ---
with tab8:
    col_th1, col_th2 = st.columns([1, 1], gap="large")

    with col_th1:
        st.subheader("🏛️ Tenth Revolution Resume PDF Uploader")
        st.caption("Upload PDF documents/resumes directly to Tenth Revolution job applications and obtain instant live public URLs.")

        th_job_url = st.text_input("Target Job Application URL", value=TENTH_DEFAULT_JOB_URL, key="th_job_url")

        th_upload_mode = st.radio(
            "Upload Source:",
            ["📁 Upload My Own PDF(s)", "📦 Upload a ZIP of PDFs", "⚡ Auto-Generate Valid SEO PDF(s)"],
            horizontal=True,
            key="th_upload_mode"
        )

        th_files_to_upload = []

        if th_upload_mode == "📁 Upload My Own PDF(s)":
            th_uploaded_files = st.file_uploader(
                "Choose one or more PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="th_pdf_uploader"
            )
            if th_uploaded_files:
                for uf in th_uploaded_files:
                    th_files_to_upload.append({"name": uf.name, "bytes": uf.getvalue()})

        elif th_upload_mode == "📦 Upload a ZIP of PDFs":
            th_zip_file = st.file_uploader("Upload a ZIP file containing PDFs", type=["zip"], key="th_zip_uploader")
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
                key="th_demo_titles"
            )
            if st.button("Generate Demo PDFs for Upload", key="btn_gen_demo_tenth"):
                titles_list = [t.strip() for t in th_demo_titles.splitlines() if t.strip()]
                gen_list = []
                for t in titles_list:
                    pdf_b = create_single_article_pdf(title=t, content=f"Application and resume document for {t}.\nVerified Tenth Revolution consultant submission.", phone="1 888 308 7172", word_count=20)
                    gen_list.append({"name": t if t.endswith(".pdf") else f"{t}.pdf", "bytes": pdf_b})
                st.session_state["tenth_generated_pdfs"] = gen_list
                st.success(f"Generated {len(gen_list)} valid PDF document(s) ready to upload!")

            if "tenth_generated_pdfs" in st.session_state and not th_files_to_upload:
                th_files_to_upload = st.session_state["tenth_generated_pdfs"]

        st.markdown("---")
        btn_tenth_upload = st.button("🚀 Upload PDF(s) to Tenth Revolution", type="primary", use_container_width=True, key="btn_tenth_upload")

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
            key="th_text_area_init",
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
                key="th_download_btn_init"
            )

        if st.button("🗑️ Clear Tenth Links History", key="btn_clear_tenth"):
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
                        key=f"th_text_area_live_{idx}",
                        help="Copy all links directly into Excel!"
                    )
                    th_count_placeholder.success(f"Total Uploaded PDFs: {len(st.session_state.tenth_links)}")
                    th_download_placeholder.download_button(
                        label="📥 Download Tenth Revolution Links (.txt)",
                        data=cur_text,
                        file_name="tenth_uploaded_links.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"th_download_btn_live_{idx}"
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

# --- TAB 9: Bulk URL Content Extractor (DOC Export) ---
with tab9:
    col_ext1, col_ext2 = st.columns([1, 1], gap="large")

    with col_ext1:
        st.subheader("📥 Bulk Forum & URL Content Extractor")
        st.caption("Paste forum/webpage URLs in bulk. The bot will extract Title and Content and generate downloadable Word (.DOCX) files.")

        url_input_raw = st.text_area(
            "Enter URLs (One URL per line):",
            value="https://adminus.freeforums.net/thread/49/faqs-explained-install-after-purchase\nhttps://adminus.freeforums.net/thread/50/validate-mcafee-license-key-errors",
            height=200,
            key="ext_urls_input"
        )

        url_file_upload = st.file_uploader(
            "Or upload a .txt file containing URLs:",
            type=["txt"],
            key="ext_urls_file"
        )

        btn_start_extract = st.button("🚀 Extract Titles & Contents (DOCX Export)", type="primary", use_container_width=True, key="btn_start_extract")

    with col_ext2:
        st.subheader("📋 Extracted Output & Downloads")
        st.caption("Extracted titles, text content, and downloadable Word (.docx) documents appear here live.")

        ext_results_placeholder = st.empty()
        ext_download_placeholder = st.empty()
        ext_container = st.container()

    if btn_start_extract:
        urls_to_process = []
        if url_file_upload:
            file_str = url_file_upload.read().decode("utf-8", errors="ignore")
            urls_to_process.extend([u.strip() for u in file_str.splitlines() if u.strip()])
        if url_input_raw:
            urls_to_process.extend([u.strip() for u in url_input_raw.splitlines() if u.strip()])

        urls_to_process = list(dict.fromkeys(urls_to_process))

        if not urls_to_process:
            st.error("Please enter or upload at least one valid URL!")
        else:
            ext_progress = st.progress(0)
            ext_status = st.empty()
            extracted_items = []

            async def run_extraction():
                for idx, target_u in enumerate(urls_to_process):
                    ext_status.info(f"⏳ Extracting ({idx+1}/{len(urls_to_process)}): `{target_u}`...")
                    res = await extract_url_content_playwright(target_u)
                    extracted_items.append(res)
                    ext_progress.progress((idx + 1) / len(urls_to_process))

                    with ext_container:
                        if res.get("success"):
                            st.success(f"✅ **#{idx+1} Title:** {res.get('title')}")
                            with st.expander(f"📄 #{idx+1} Content Preview ({len(res.get('content', ''))} chars)", expanded=False):
                                st.text_area("Title & Content:", value=f"TITLE: {res.get('title')}\n\nCONTENT:\n{res.get('content')}", height=200, key=f"ext_preview_{idx}")
                                single_doc = create_single_docx(res.get('title'), res.get('content'), res.get('url'))
                                st.download_button(
                                    label=f"📥 Download #{idx+1} (.docx)",
                                    data=single_doc,
                                    file_name=f"Extracted_{idx+1}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"ext_single_dl_{idx}"
                                )
                        else:
                            st.error(f"❌ #{idx+1} Failed: {res.get('url')} - Error: {res.get('error')}")

            asyncio.run(run_extraction())

            ext_status.success(f"🎉 Completed extraction of {len(extracted_items)} URL(s)!")
            st.balloons()

            # Create combined docx
            combined_docx_bytes = create_docx_file(extracted_items)
            ext_download_placeholder.download_button(
                label="📥 Download ALL Extracted Content (.DOCX)",
                data=combined_docx_bytes,
                file_name="Bulk_Extracted_Content.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="btn_combined_docx_dl"
            )

# --- TAB 10: Adminus ProBoards DOCX Poster ---
with tab10:
    col_adm1, col_adm2 = st.columns([1, 1], gap="large")

    with col_adm1:
        st.subheader("📑 Adminus ProBoards DOCX Poster")
        st.caption("Upload a `.docx` file containing multiple extracted/edited articles. The bot will log into ProBoards (`adminus`), navigate to `thread/new/1`, fill Title and Content for each article, publish, and record live thread URLs.")

        adm_login_url = st.text_input("ProBoards Login URL", value="https://login.proboards.com/login/7485305/1", key="adm_login_url")
        
        col_cred1, col_cred2 = st.columns([1, 1])
        with col_cred1:
            adm_username = st.text_input("Username / Email", value="akashbhai", key="adm_username")
        with col_cred2:
            adm_password = st.text_input("Password", value="Rohit@123321", type="password", key="adm_password")

        adm_target_url = st.text_input("Target New Thread URL", value="https://adminus.freeforums.net/thread/new/1", key="adm_target_url")

        adm_docx_file = st.file_uploader("Upload Articles (.DOCX) File:", type=["docx"], key="adm_docx_uploader")

        articles_to_post = []
        if adm_docx_file:
            try:
                articles_to_post = parse_docx_articles(adm_docx_file.getvalue())
                st.success(f"✅ Extracted {len(articles_to_post)} article(s) from `.docx`!")
            except Exception as e:
                st.error(f"Error parsing .docx file: {e}")

        if articles_to_post:
            with st.expander(f"📋 Preview {len(articles_to_post)} Extracted Articles", expanded=False):
                for idx, art in enumerate(articles_to_post, 1):
                    st.markdown(f"**Article #{idx}:** {art['title']}")
                    st.caption(f"Content Length: {len(art['content'])} chars | Preview: `{art['content'][:120]}...`")
                    st.divider()

        adm_timeout = st.slider("Timeout per post (seconds)", min_value=60, max_value=300, value=180, step=30, key="adm_timeout_slider")

        btn_start_adminus = st.button("🚀 Start Adminus DOCX Batch Posting", type="primary", use_container_width=True, key="btn_start_adminus")

    with col_adm2:
        st.subheader("📋 Live Adminus Published Threads (Copy to Excel)")
        st.caption("Updates immediately after each thread publication. Select all and copy directly into Excel!")

        adm_output_placeholder = st.empty()
        adm_count_placeholder = st.empty()
        adm_download_placeholder = st.empty()
        adm_live_container = st.container()

        initial_adm_text = "\n".join(st.session_state.adminus_links)
        adm_output_placeholder.text_area(
            label="Live Plain Text Thread Links Box:",
            value=initial_adm_text if initial_adm_text else "",
            height=380,
            key="adm_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.adminus_links:
            adm_count_placeholder.success(f"Total Created Threads: {len(st.session_state.adminus_links)}")
            adm_download_placeholder.download_button(
                label="📥 Download Adminus Links (.txt)",
                data=initial_adm_text,
                file_name="adminus_threads.txt",
                mime="text/plain",
                use_container_width=True,
                key="adm_download_btn_init"
            )

    if btn_start_adminus:
        if not articles_to_post:
            st.error("Please upload a valid `.docx` file containing articles before starting!")
        else:
            adm_progress = st.progress(0)
            adm_status = st.empty()

            for idx, art in enumerate(articles_to_post):
                t_title = art["title"]
                t_content = art["content"]
                adm_status.info(f"⏳ Posting ({idx + 1}/{len(articles_to_post)}): **{t_title}** - Browser opening...")

                res = run_proboards_sync(
                    guest_name="Akash Bhai",
                    subject=t_title,
                    content=t_content,
                    login_url=adm_login_url,
                    username=adm_username,
                    password=adm_password,
                    target_url=adm_target_url,
                    timeout_sec=adm_timeout
                )

                adm_progress.progress((idx + 1) / len(articles_to_post))

                if res.get("success") and res.get("url"):
                    new_url = res["url"]
                    if new_url not in st.session_state.adminus_links:
                        st.session_state.adminus_links.append(new_url)
                    
                    with open("adminus_threads.txt", "a", encoding="utf-8") as af:
                        af.write(f"{new_url}\n")

                    updated_adm_text = "\n".join(st.session_state.adminus_links)
                    adm_output_placeholder.text_area(
                        label="Live Plain Text Thread Links Box:",
                        value=updated_adm_text,
                        height=380,
                        key=f"adm_text_area_live_{idx}",
                        help="Copy all links directly into Excel!"
                    )
                    adm_count_placeholder.success(f"Total Created Threads: {len(st.session_state.adminus_links)}")
                    adm_download_placeholder.download_button(
                        label="📥 Download Adminus Links (.txt)",
                        data=updated_adm_text,
                        file_name="adminus_threads.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"adm_download_btn_live_{idx}"
                    )

                    with adm_live_container:
                        st.success(f"✅ **({idx + 1}/{len(articles_to_post)}) {t_title}** → [Created Thread Link]({new_url})")
                else:
                    err_msg = res.get("error", "Unknown error or timeout")
                    with adm_live_container:
                        st.error(f"❌ **({idx + 1}/{len(articles_to_post)}) {t_title}** → Error: {err_msg}")

            if st.session_state.adminus_links:
                st.balloons()
                st.success(f"🎉 Completed posting all {len(articles_to_post)} article(s) to Adminus ProBoards!")

# --- TAB 11: Arcade Game Designer (ProBoards) Bot ---
with tab11:
    col_arc1, col_arc2 = st.columns([1, 1], gap="large")

    with col_arc2:
        st.subheader("📋 Live Arcade Game Designer Links (Copy to Excel)")
        st.caption("Updates instantly after EACH thread creation. Select all and copy directly into Excel!")
        arc_output_placeholder = st.empty()
        arc_count_placeholder = st.empty()
        arc_download_placeholder = st.empty()

        initial_arc_text = "\n".join(st.session_state.arcade_links)
        arc_output_placeholder.text_area(
            label="Live Plain Text Thread Links Box:",
            value=initial_arc_text if initial_arc_text else "",
            height=380,
            key="arc_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.arcade_links:
            arc_count_placeholder.success(f"Total Created Threads: {len(st.session_state.arcade_links)}")
            arc_download_placeholder.download_button(
                label="📥 Download Arcade Game Designer Links (.txt)",
                data=initial_arc_text,
                file_name="arcade_threads.txt",
                mime="text/plain",
                use_container_width=True,
                key="arc_download_btn_init"
            )

    with col_arc1:
        st.subheader("🎮 Arcade Game Designer ProBoards Bot")
        st.caption("Target Board: `https://arcadegamedesigner.proboards.com/thread/new/4` | AI Content Generation")

        arc_login_url = st.text_input("ProBoards Login URL", value="https://login.proboards.com/login/3425386/1", key="arc_login_url")
        
        col_arc_c1, col_arc_c2 = st.columns([1, 1])
        with col_arc_c1:
            arc_username = st.text_input("Username / Email", value="leomendis", key="arc_username")
        with col_arc_c2:
            arc_password = st.text_input("Password", value="Rohit@123321", type="password", key="arc_password")

        arc_target_url = st.text_input("Target New Thread URL", value="https://arcadegamedesigner.proboards.com/thread/new/4", key="arc_target_url")

        arc_phone_input = st.text_input("Support Toll-Free Phone", value="+1 888 308 7172", key="arc_phone_input")
        arc_groq_key = st.text_input("Groq API Key (High-Speed AI)", value=DEFAULT_GROQ_KEY, type="password", key="arc_groq_key")

        arc_post_mode = st.radio("Posting Mode", ["Single Thread Post", "Batch Posting (Multiple Titles)"], horizontal=True, key="arc_post_mode")

        if arc_post_mode == "Single Thread Post":
            arc_subject = st.text_input(
                "Thread Subject / Title",
                value="《FAQ'S™》1 888 308 7172 How to Cancel CCleaner Subscription",
                key="arc_single_subject"
            )

            col_gen_arc, _ = st.columns([1, 1])
            if col_gen_arc.button("✨ Auto-Generate AI Content for This Title", key="btn_gen_single_content_arc"):
                with st.spinner("Generating authentic content with Groq AI..."):
                    gen_txt = generate_proboards_content(title=arc_subject, phone=arc_phone_input, groq_api_key=arc_groq_key)
                    st.session_state.arc_single_content_val = gen_txt

            if "arc_single_content_val" not in st.session_state:
                st.session_state.arc_single_content_val = "Click '✨ Auto-Generate AI Content for This Title' above to generate unique content with Groq AI, or enter your custom content here."
            arc_single_val = st.session_state.arc_single_content_val

            arc_content = st.text_area(
                "Thread Content:",
                value=arc_single_val,
                height=220,
                key="arc_single_content_area"
            )
            arc_titles_list = [arc_subject] if arc_subject.strip() else []
        else:
            arc_titles_raw = st.text_area(
                "Enter Thread Titles (One title per line):",
                value="[2026 Updated] How Do I Confirm CCleaner Purchase Details?\nHow to Cancel CCleaner and Manage Your Subscription Settings\nWhere Can I Find My CCleaner Activation Code?",
                height=180,
                key="arc_batch_titles_input"
            )
            arc_uploaded_file = st.file_uploader(
                "Or upload a .txt file containing thread titles",
                type=["txt"],
                key="arc_titles_file"
            )
            arc_auto_content = st.checkbox("Auto-generate unique content for each title using Groq AI", value=True, key="arc_auto_content")
            arc_custom_content = ""
            if not arc_auto_content:
                arc_custom_content = st.text_area("Default Content for all titles:", value="Hello everyone! Looking forward to hearing your thoughts on this topic.", height=100, key="arc_custom_default_content")

            arc_titles_list = []
            if arc_uploaded_file:
                content_file = arc_uploaded_file.read().decode("utf-8")
                arc_titles_list.extend([line.strip() for line in content_file.splitlines() if line.strip()])
            if arc_titles_raw:
                arc_titles_list.extend([line.strip() for line in arc_titles_raw.splitlines() if line.strip()])
            arc_titles_list = list(dict.fromkeys(arc_titles_list))

        arc_timeout = st.slider("Timeout waiting for Captcha / Publish (seconds)", min_value=60, max_value=300, value=180, step=30, key="arc_timeout_slider")

        st.info("💡 **Browser Workflow**: Bot launches a real visible Chromium window, logs in to ProBoards (`leomendis`), fills Subject & AI Content, clicks 'Create Thread', auto-checks TOS. Solve captcha if prompted!")

        if st.button("🚀 Start Arcade Game Designer Bot", type="primary", use_container_width=True, key="btn_arc_start"):
            if not arc_titles_list:
                st.error("Please provide at least one subject / title!")
            else:
                st.write(f"🔄 Starting bot for {len(arc_titles_list)} thread(s)...")
                arc_progress_bar = st.progress(0)
                arc_status = st.empty()
                live_arc_container = st.container()

                for idx, t_title in enumerate(arc_titles_list):
                    arc_status.info(f"⏳ Processing ({idx + 1}/{len(arc_titles_list)}): **{t_title}** - Browser is opening...")

                    if arc_post_mode == "Single Thread Post":
                        t_content = arc_content
                    else:
                        if arc_auto_content:
                            try:
                                t_content = generate_proboards_content(title=t_title, phone=arc_phone_input, groq_api_key=arc_groq_key)
                            except Exception:
                                t_content = f"Hello friends!\n\nI wanted to open up a discussion about '{t_title}'. For live support dial {arc_phone_input}."
                        else:
                            t_content = arc_custom_content if arc_custom_content else f"Discussion on {t_title}"

                    res = run_proboards_sync(
                        guest_name="Leo Mendis",
                        subject=t_title,
                        content=t_content,
                        login_url=arc_login_url,
                        username=arc_username,
                        password=arc_password,
                        target_url=arc_target_url,
                        timeout_sec=arc_timeout,
                        groq_api_key=arc_groq_key
                    )

                    arc_progress_bar.progress((idx + 1) / len(arc_titles_list))

                    if res.get("success") and res.get("url"):
                        new_url = res["url"]
                        if new_url not in st.session_state.arcade_links:
                            st.session_state.arcade_links.append(new_url)

                        with open("arcade_threads.txt", "a", encoding="utf-8") as arf:
                            arf.write(f"{new_url}\n")

                        updated_arc_text = "\n".join(st.session_state.arcade_links)
                        arc_output_placeholder.text_area(
                            label="Live Plain Text Thread Links Box:",
                            value=updated_arc_text,
                            height=380,
                            key=f"arc_text_area_live_{idx}",
                            help="Copy all links directly into Excel!"
                        )
                        arc_count_placeholder.success(f"Total Created Threads: {len(st.session_state.arcade_links)}")
                        arc_download_placeholder.download_button(
                            label="📥 Download Arcade Game Designer Links (.txt)",
                            data=updated_arc_text,
                            file_name="arcade_threads.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"arc_download_btn_live_{idx}"
                        )

                        with live_arc_container:
                            st.success(f"✅ **({idx + 1}/{len(arc_titles_list)}) {t_title}** → [Created Thread Link]({new_url})")
                    else:
                        err_msg = res.get("error", "Unknown error or timeout")
                        with live_arc_container:
                            st.error(f"❌ **({idx + 1}/{len(arc_titles_list)}) {t_title}** → Error: {err_msg}")

                if st.session_state.arcade_links:
                    st.balloons()
                    st.success(f"🎉 Completed all {len(arc_titles_list)} thread(s)!")

# --- TAB 12: Quaalude (ProBoards) Bot ---
with tab12:
    col_qua1, col_qua2 = st.columns([1, 1], gap="large")

    with col_qua2:
        st.subheader("📋 Live Quaalude Forum Links (Copy to Excel)")
        st.caption("Updates instantly after EACH thread creation. Select all and copy directly into Excel!")
        qua_output_placeholder = st.empty()
        qua_count_placeholder = st.empty()
        qua_download_placeholder = st.empty()

        initial_qua_text = "\n".join(st.session_state.quaalude_links)
        qua_output_placeholder.text_area(
            label="Live Plain Text Thread Links Box:",
            value=initial_qua_text if initial_qua_text else "",
            height=380,
            key="qua_text_area_init",
            help="Copy all links directly into Excel!"
        )

        if st.session_state.quaalude_links:
            qua_count_placeholder.success(f"Total Created Threads: {len(st.session_state.quaalude_links)}")
            qua_download_placeholder.download_button(
                label="📥 Download Quaalude Links (.txt)",
                data=initial_qua_text,
                file_name="quaalude_threads.txt",
                mime="text/plain",
                use_container_width=True,
                key="qua_download_btn_init"
            )

    with col_qua1:
        st.subheader("💊 Quaalude ProBoards Bot")
        st.caption("Target Board: `https://quaalude.proboards.com/thread/new/31` | AI Content Generation")

        qua_login_url = st.text_input("ProBoards Login URL", value="https://login.proboards.com/login/2426311/1", key="qua_login_url")
        
        col_qua_c1, col_qua_c2 = st.columns([1, 1])
        with col_qua_c1:
            qua_username = st.text_input("Username / Email", value="leomendis", key="qua_username")
        with col_qua_c2:
            qua_password = st.text_input("Password", value="Rohit@123321#", type="password", key="qua_password")

        qua_target_url = st.text_input("Target New Thread URL", value="https://quaalude.proboards.com/thread/new/31", key="qua_target_url")

        qua_phone_input = st.text_input("Support Toll-Free Phone", value="+1 888 308 7172", key="qua_phone_input")
        qua_groq_key = st.text_input("Groq API Key (High-Speed AI)", value=DEFAULT_GROQ_KEY, type="password", key="qua_groq_key")

        qua_post_mode = st.radio("Posting Mode", ["Single Thread Post", "Batch Posting (Multiple Titles)"], horizontal=True, key="qua_post_mode")

        if qua_post_mode == "Single Thread Post":
            qua_subject = st.text_input(
                "Thread Subject / Title",
                value="《FAQ'S™》1 888 308 7172 How to Cancel Norton Subscription",
                key="qua_single_subject"
            )

            col_gen_qua, _ = st.columns([1, 1])
            if col_gen_qua.button("✨ Auto-Generate AI Content for This Title", key="btn_gen_single_content_qua"):
                with st.spinner("Generating authentic content with Groq AI..."):
                    gen_txt = generate_proboards_content(title=qua_subject, phone=qua_phone_input, groq_api_key=qua_groq_key)
                    st.session_state.qua_single_content_val = gen_txt

            if "qua_single_content_val" not in st.session_state:
                st.session_state.qua_single_content_val = "Click '✨ Auto-Generate AI Content for This Title' above to generate unique content with Groq AI, or enter your custom content here."
            qua_single_val = st.session_state.qua_single_content_val

            qua_content = st.text_area(
                "Thread Content:",
                value=qua_single_val,
                height=220,
                key="qua_single_content_area"
            )
            qua_titles_list = [qua_subject] if qua_subject.strip() else []
        else:
            qua_titles_raw = st.text_area(
                "Enter Thread Titles (One title per line):",
                value="[2026 Updated] How Do I Confirm Norton Purchase Details?\nHow to Cancel Norton and Manage Your Subscription Settings",
                height=180,
                key="qua_batch_titles_input"
            )
            qua_uploaded_file = st.file_uploader(
                "Or upload a .txt file containing thread titles",
                type=["txt"],
                key="qua_titles_file"
            )
            qua_auto_content = st.checkbox("Auto-generate unique content for each title using Groq AI", value=True, key="qua_auto_content")
            qua_custom_content = ""
            if not qua_auto_content:
                qua_custom_content = st.text_area("Default Content for all titles:", value="Hello everyone! Looking forward to hearing your thoughts on this topic.", height=100, key="qua_custom_default_content")

            qua_titles_list = []
            if qua_uploaded_file:
                content_file = qua_uploaded_file.read().decode("utf-8")
                qua_titles_list.extend([line.strip() for line in content_file.splitlines() if line.strip()])
            if qua_titles_raw:
                qua_titles_list.extend([line.strip() for line in qua_titles_raw.splitlines() if line.strip()])
            qua_titles_list = list(dict.fromkeys(qua_titles_list))

        qua_timeout = st.slider("Timeout waiting for Captcha / Publish (seconds)", min_value=60, max_value=300, value=180, step=30, key="qua_timeout_slider")

        st.info("💡 **Browser Workflow**: Bot launches a real visible Chromium window, logs in to ProBoards (`leomendis`), fills Subject & AI Content, clicks 'Create Thread', auto-checks TOS. Solve captcha if prompted!")

        if st.button("🚀 Start Quaalude ProBoards Bot", type="primary", use_container_width=True, key="btn_qua_start"):
            if not qua_titles_list:
                st.error("Please provide at least one subject / title!")
            else:
                st.write(f"🔄 Starting bot for {len(qua_titles_list)} thread(s)...")
                qua_progress_bar = st.progress(0)
                qua_status = st.empty()
                live_qua_container = st.container()

                for idx, t_title in enumerate(qua_titles_list):
                    qua_status.info(f"⏳ Processing ({idx + 1}/{len(qua_titles_list)}): **{t_title}** - Browser is opening...")

                    if qua_post_mode == "Single Thread Post":
                        t_content = qua_content
                    else:
                        if qua_auto_content:
                            try:
                                t_content = generate_proboards_content(title=t_title, phone=qua_phone_input, groq_api_key=qua_groq_key)
                            except Exception:
                                t_content = f"Hello friends!\n\nI wanted to open up a discussion about '{t_title}'. For live support dial {qua_phone_input}."
                        else:
                            t_content = qua_custom_content if qua_custom_content else f"Discussion on {t_title}"

                    res = run_proboards_sync(
                        guest_name="Leo Mendis",
                        subject=t_title,
                        content=t_content,
                        login_url=qua_login_url,
                        username=qua_username,
                        password=qua_password,
                        target_url=qua_target_url,
                        timeout_sec=qua_timeout,
                        groq_api_key=qua_groq_key
                    )

                    qua_progress_bar.progress((idx + 1) / len(qua_titles_list))

                    if res.get("success") and res.get("url"):
                        new_url = res["url"]
                        if new_url not in st.session_state.quaalude_links:
                            st.session_state.quaalude_links.append(new_url)

                        with open("quaalude_threads.txt", "a", encoding="utf-8") as qf:
                            qf.write(f"{new_url}\n")

                        updated_qua_text = "\n".join(st.session_state.quaalude_links)
                        qua_output_placeholder.text_area(
                            label="Live Plain Text Thread Links Box:",
                            value=updated_qua_text,
                            height=380,
                            key=f"qua_text_area_live_{idx}",
                            help="Copy all links directly into Excel!"
                        )
                        qua_count_placeholder.success(f"Total Created Threads: {len(st.session_state.quaalude_links)}")
                        qua_download_placeholder.download_button(
                            label="📥 Download Quaalude Links (.txt)",
                            data=updated_qua_text,
                            file_name="quaalude_threads.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"qua_download_btn_live_{idx}"
                        )

                        with live_qua_container:
                            st.success(f"✅ **({idx + 1}/{len(qua_titles_list)}) {t_title}** → [Created Thread Link]({new_url})")
                    else:
                        err_msg = res.get("error", "Unknown error or timeout")
                        with live_qua_container:
                            st.error(f"❌ **({idx + 1}/{len(qua_titles_list)}) {t_title}** → Error: {err_msg}")

                if st.session_state.quaalude_links:
                    st.balloons()
                    st.success(f"🎉 Completed all {len(qua_titles_list)} thread(s)!")



