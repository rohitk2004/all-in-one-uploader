# ⚡ All-in-One Uploader & Automation Suite

A multi-platform document uploader, forum publisher, and content automation suite with interactive **Streamlit** dashboards and headless/headful **Playwright** browser automation.

---

## 🚀 Key Features

### 📄 Document & PDF Uploaders
- **CAPIAA Bulk PDF Uploader**: Bulk PDF and ZIP uploads for [capiaa.ca.gov](https://capiaa.ca.gov/certificate/) with automatic WPForms tmp link extraction (`%2F` encoded download URLs).
- **FD.org PDF Uploader**: Multi-file / ZIP upload pipeline targeting [fd.org](https://fd.org/form/form-submission) with live Cloudinary link streaming.
- **Eden Hospitality Uploader**: Job application document uploader with real-time link aggregation.
- **Tenth Revolution Uploader**: Automated career document submitter with instant link extraction.
- **HSSET Application Uploader**: Form submission pipeline for HSSET PDF applications.
- **Triomphe de l'Art Uploader**: Competition submission automation with unique entry tokens.
- **USP Abstracts Uploader**: Academic abstract uploader for University of São Paulo portals.
- **USAL Digitalstack Matricula Uploader**: Student matriculation document processing.
- **UFL Invasion Science Uploader**: University of Florida affiliate document automation.

### 🌐 Forum & Content Automation Bots
- **ProBoards Multi-Board Bot**: Automated posting bot supporting Naruto Revelation, Quaalude, Adminus, Arcade, and YouTubeTV boards. Features Groq AI content generation and phone interleaving.
- **Community King Forum Bot**: Automatic account registration, category selection, and discussion thread posting.
- **Firstory Playlist Creator**: Headless/headful podcast playlist creation with cover art assignment.
- **Hugging Face Discourse Bot**: Discourse forum topic creator with custom category selection.
- **Hire & Wire Profile Generator**: Candidate profile creator with rich formatting.

### 📝 SmartWaiver Automation
- **Waiver Template Creator**: Automated template generator with Vue.js title panel expansion, HTML injection, and live public URL extraction.
- **Event Creator**: Event creation with automated validation, title sanitization, and direct UUID extraction.

### 🧠 Content Generation & Extraction Engines
- **Unique Content Engine**: Groq & OpenRouter AI integrations for authentic, human-like technical content with anti-cliché filters.
- **Bulk URL Content Extractor**: Playwright scraper extracting article content and exporting cleanly to DOCX and PDF bundles.
- **PDF & DOCX Parsers**: Batch generation of formatted PDFs and ZIP archives.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/rohitk2004/all-in-one-uploader.git
cd all-in-one-uploader
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install chromium
```

### 4. Configure Environment Variables (Optional)
Copy `.env.example` to `.env` and set your API keys:
```bash
cp .env.example .env
```

---

## 💻 Running the Dashboards

### Main All-in-One Dashboard
Launch the unified Streamlit dashboard:
```bash
streamlit run streamlit_app.py
```

### SmartWaiver & Form Automation Dashboard
Launch the specialized SmartWaiver management interface:
```bash
streamlit run smartwaiver_app.py
```

---

## ⚡ CLI Batch Runners

For headless batch execution from the terminal, specialized CLI runners are available:

| Runner Script | Description |
|---|---|
| `run_user_titles_batch.py` | Batch publish multiple titles to ProBoards |
| `run_arcade_batch.py` | Arcade designer forum batch automation |
| `run_flyx_batch.py` | Flyx ProBoards (`flyx.proboards.com`) automated batch poster |
| `run_quaalude_batch.py` | Quaalude forum batch poster |
| `run_naruto_batch.py` | Naruto Revelation forum batch poster |
| `run_youtubetv_bot.py` | YouTube TV forum runner |
| `run_huggingface_batch.py` | Hugging Face Discourse batch poster |
| `run_king_batch_10.py` | Community King batch discussion poster |
| `run_eden_upload.py` | Eden Hospitality PDF batch uploader |
| `run_tenth_upload.py` | Tenth Revolution PDF batch uploader |
| `run_triomphe_batch.py` | Triomphe de l'Art competition uploader |

Run any batch script using:
```bash
python run_user_titles_batch.py
```

---

## 📁 Repository Structure

```
all-in-one-uploader/
├── streamlit_app.py           # Main unified automation dashboard
├── smartwaiver_app.py         # SmartWaiver & certificate automation dashboard
│
├── capiaa_bot.py              # CAPIAA & WPForms PDF uploader
├── fd_uploader.py             # FD.org Cloudinary PDF uploader
├── eden_uploader.py           # Eden Hospitality uploader
├── tenth_uploader.py          # Tenth Revolution uploader
├── hsset_uploader.py          # HSSET application uploader
├── triomphe_uploader.py       # Triomphe competition uploader
├── usp_uploader.py            # USP abstracts uploader
├── usal_matricula_uploader.py # USAL matricula uploader
├── ufl_affiliate_uploader.py  # UFL affiliate uploader
│
├── proboards_bot.py           # ProBoards multi-board automation bot
├── run_flyx_batch.py          # Flyx ProBoards batch poster bot
├── king_bot.py                # Community King forum bot
├── firstory_bot.py            # Firstory playlist creator bot
├── huggingface_bot.py         # Hugging Face forum bot
├── hireandwire_bot.py         # Hire & Wire candidate bot
│
├── test_waiver_creation.py    # SmartWaiver waiver template automation
├── test_fill_event.py         # SmartWaiver event creator automation
│
├── unique_content_engine.py   # AI content generation engine (Groq/OpenRouter)
├── description_generator.py   # In-sentence phone interleaving engine
├── url_content_extractor.py   # Web scraper & DOCX converter
├── docx_articles_parser.py    # DOCX article batch parser
├── pdf_generator.py           # Valid PDF document generator
├── pdf_content_exporter.py    # PDF & ZIP exporter
│
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
└── README.md                  # Project documentation
```

---

## 🔒 Security & Privacy
- Sensitive keys and browser session profiles are excluded from version control via `.gitignore`.
- Provide your own API keys (`GROQ_API_KEY`, `OPENROUTER_API_KEY`) via environment variables or inside the Streamlit UI configuration panels.

---

## 📄 License
MIT License. Created by [rohitk2004](https://github.com/rohitk2004).
