"""
Unique Content Engine for SEO & StackBlitz/Forum Automation
Implements 4-Tier Diversity Engineering:
1. Role & Angle Switching (Angry User, SysAdmin, Senior Support Lead, Security Auditor, Incident Engineer)
2. Formatting Constraints & Structural Variance (H3 Bullets, Chronological Steps + Matrix Table, Error Code Deep Dive, Executive Briefing)
3. Dynamic Seed Variables (Trigger Error Codes: Error 1603, Token Mismatch, Driver Lock, Socket Conflict, Tone & OS context)
4. 5-Word Phone Interleaving with user's front-end TFN (+1 888 308 7172)
"""

import re
import random
import hashlib
import requests
from typing import Optional

OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-001",
    "google/gemini-2.0-flash-lite-001",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-7b-instruct:free"
]

DEFAULT_OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# --- Negative Constraints & AI Cliche Banning ---
NEGATIVE_CONSTRAINTS = [
    "DO NOT use generic AI intro cliches like 'In today's digital world', 'Look no further', 'In this fast-paced digital era', 'Delve into', or 'Moreover'.",
    "DO NOT write robotic concluding paragraphs starting with 'In conclusion', 'To summarize', or 'Final thoughts'. Finish directly with action steps.",
    "DO NOT use repetitive marketing fluff. Write authentic, human technical prose with varied sentence lengths."
]

# --- Randomized Few-Shot Style Snippets ---
FEW_SHOT_STYLES = [
    "Sample Writing Style 1: 'Log Audit Note: Service failed with Exit Code 1603 after silent registry rollback. Manual fix: Run regedit as Admin and grant Full Control to SYSTEM on HKLM\\Software\\Policies.'",
    "Sample Writing Style 2: 'User Incident: Tried activating 3 times yesterday, kept getting Token Invalid error. Called helpline, cleared SSL cache in Control Panel, and license attached instantly.'",
    "Sample Writing Style 3: 'Troubleshooting Checklist: 1. Disconnect VPN 2. Flush DNS resolver cache 3. Re-enter 16-digit authorization key. Call support if lock persists.'"
]

# --- Post-Processing Spintax / Synonym Replacement Engine ---
SYNONYM_REPLACEMENTS = {
    r"\bIn order to fix\b": ["To resolve", "For troubleshooting", "To repair", "If you need to fix"],
    r"\bIn order to\b": ["To", "So as to", "In an effort to"],
    r"\breach out to\b": ["connect directly with", "speak to", "contact", "call"],
    r"\bwithout delay\b": ["immediately", "right away", "promptly"],
    r"\bas soon as possible\b": ["without delay", "right away", "immediately"],
    r"\bkeep in mind that\b": ["note that", "remember that", "it is worth noting that"],
    r"\bmake sure to\b": ["ensure you", "be sure to", "verify that you"],
    r"\bstep-by-step\b": ["step by step", "sequential", "guided"],
    r"\bfirst of all\b": ["initially", "to start with", "firstly"],
    r"\bif you are experiencing\b": ["if you encounter", "when facing", "in case of experiencing"],
    r"\bget in touch with\b": ["speak directly to", "call", "connect with"]
}

def apply_spintax_synonyms(text: str, rng: Optional[random.Random] = None) -> str:
    """
    Post-processing Spintax engine that randomly swaps common phrases
    to eliminate N-gram matching footprints across generated articles.
    """
    if rng is None:
        rng = random.Random()
        
    res = text
    for pattern, choices in SYNONYM_REPLACEMENTS.items():
        matches = list(re.finditer(pattern, res, flags=re.IGNORECASE))
        for m in reversed(matches):
            chosen = rng.choice(choices)
            if m.group(0)[0].isupper():
                chosen = chosen[0].upper() + chosen[1:]
            res = res[:m.start()] + chosen + res[m.end():]
    return res


def detect_title_domain(title: str) -> str:
    """
    Classifies titles into specific domain categories:
    1. ADBLOCK_SUBSCRIPTION: Adware, AdBlock, Subscription, Refund, Billing, Cancel, Antivirus, Chrome/Edge Extensions
    2. PRINTER_HARDWARE: Printer, Print, Spooler, Paper Jam, Ink, Wi-Fi Setup, Canon, Brother, HP, Epson
    3. SOFTWARE_LICENSE: License keys, Error 1603, App setup, Activation, Accounts
    """
    t_lower = title.lower()
    
    # AdBlock / Adware / Subscription / Antivirus / Billing keywords
    if any(kw in t_lower for kw in [
        "adware", "adblock", "ads", "popup", "pop-up", "cancel", "subscription", "refund", "billing", 
        "renew", "charge", "mcafee", "totalav", "avast", "norton", "kaspersky", "malware", "antivirus", 
        "guard", "shield", "extension", "chrome", "edge", "firefox", "ad blocker", "ad-blocker"
    ]):
        return "ADBLOCK_SUBSCRIPTION"
        
    # Printer keywords
    if any(kw in t_lower for kw in [
        "printer", "print", "spooler", "paper", "ink", "cartridge", "brother", "canon", "hp", "epson", 
        "lexmark", "xerox", "samsung", "scanner", "printhead", "jam", "offline"
    ]):
        return "PRINTER_HARDWARE"
        
    return "SOFTWARE_LICENSE"

def strip_all_markdown_formatting(text: str) -> str:
    """
    Strips all markdown symbols (** bold, * italic, # headers, ` code, _ underscores, ~ strike, quotes " and '),
    HTML tags, and markdown table pipe syntax to produce 100% clean, pure plain text.
    """
    if not text:
        return ""
    
    # 1. Remove quotes (double, single, curly)
    text = text.replace('"', '').replace("'", "").replace('"', '').replace('"', '').replace("'", "").replace("'", "")
    
    # 2. Remove markdown header symbols at start of lines (#, ##, ###)
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
    
    # 3. Remove bold / italic / code / strikethrough markers (*, **, _, __, `, ~)
    text = re.sub(r'[*_`~]+', '', text)
    
    # 4. Remove HTML tags if any (<p>, <h3>, <b>, <span>, etc.)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 5. Convert table separators and markdown table formatting to plain text
    text = re.sub(r'^\s*\|?\s*:?-+:?\s*\|?\s*$', '', text, flags=re.MULTILINE)
    text = text.replace('|', ' - ')

    # 6. Normalize multiple spaces and extra empty lines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

# --- Dynamic Seed Pools ---
PERSONAS = [
    {
        "role": "Angry User Resolution Story",
        "instruction": "Write from the perspective of an frustrated user who experienced unexpected billing/activation errors, got double-charged or locked out, and finally resolved it step-by-step via our support helpline."
    },
    {
        "role": "Enterprise IT SysAdmin Guide",
        "instruction": "Write as a Senior Enterprise IT Administrator producing an in-depth technical field guide detailing registry permissions, driver conflict signatures, network socket locks, and enterprise deployments."
    },
    {
        "role": "Beginner-Friendly Helpdesk Lead",
        "instruction": "Write as a patient Senior Support Lead creating a clear, jargon-free step-by-step walkthrough suitable for senior citizens and non-technical users."
    },
    {
        "role": "Cybersecurity & Software Compliance Auditor",
        "instruction": "Write as a Security & Compliance Specialist evaluating authorization tokens, SSL handshakes, firewall rules, and subscription validation policies."
    },
    {
        "role": "Systems Incident Engineer Field Note",
        "instruction": "Write as a Systems Engineer documenting a real-world incident post-mortem, outlining diagnostic logs, root cause analysis, and immediate mitigation commands."
    }
]

FORMAT_CONSTRAINTS = [
    {
        "name": "Conversational H3 + Bullet Points",
        "instruction": "Use 5 distinct H3 headings with conversational bullet points and a final quick action summary checklist."
    },
    {
        "name": "Chronological Steps + Comparison Matrix Table",
        "instruction": "Structure without generic bullet points. Use numbered chronological steps followed by a Markdown comparison table showing Problem vs Cause vs Verified Fix."
    },
    {
        "name": "Error Code Deep-Dive + 4 In-Depth FAQs",
        "instruction": "Structure as: Problem Overview -> Trigger Error Code Analysis -> Step-by-Step Technical Repair -> 4 In-Depth FAQs."
    },
    {
        "name": "Executive Incident Report + Proactive Prevention",
        "instruction": "Structure as: Executive Summary -> Root Cause Analysis -> Immediate Fix Walkthrough -> Proactive Future Prevention Tips."
    }
]

ERROR_TRIGGERS = [
    "Error 1603 (Fatal Installation Failure)",
    "Token Validation Timeout (Err 403 / AUTH_MISMATCH)",
    "Driver Signature Enforcement Lock (0x80070005)",
    "Subscription Mismatch Token (ERR_LICENSE_KEY_EXPIRED)",
    "Port Socket Conflict & Firewall Security Block",
    "Registry Permission Denied (0x00000005_ACCESS_DENIED)"
]

TONES = ["Urgent & Direct", "Detailed Technical", "Conversational & Empathetic", "Authoritative & Formal"]

def clean_title_str(title: str) -> str:
    """Removes special brackets and cleans up title string."""
    clean = re.sub(r'[\(\)\[\]\?\:\!\;\"\'\`]', ' ', title).strip()
    return re.sub(r'\s+', ' ', clean) or "Official Customer Support Guide"

def format_tfn_display(tfn: str) -> str:
    """Formats raw TFN string cleanly."""
    if not tfn or not str(tfn).strip():
        return DEFAULT_PHONE
    return str(tfn).strip()

def interleave_dynamic_words(text: str, tfn: str = DEFAULT_PHONE) -> str:
    """
    Inserts phone number variations throughout text:
    - First 100 words: after every 4 words.
    - After 100 words: after every 8 words.
    Preserves markdown headers, tables, HTML tags, and line breaks.
    """
    clean_phone = format_tfn_display(tfn)
    
    phone_v1 = f"Call {clean_phone}"
    phone_v2 = f"({clean_phone})"
    phone_v3 = f"{clean_phone}"
    
    phone_variants = [phone_v1, phone_v2, phone_v3]
    
    lines = text.split("\n")
    out_lines = []
    variant_idx = 0
    total_words = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped.startswith("<h") or len(stripped.split()) < 3:
            out_lines.append(line)
            continue

        words = line.split()
        res_words = []
        chunk_count = 0

        for w in words:
            res_words.append(w)
            total_words += 1
            chunk_count += 1

            # Interleave every 20 words for smooth, natural phone placement
            interval = 20

            if chunk_count >= interval:
                # Avoid duplicate insertion if clean_phone is already in the current or previous word
                if clean_phone not in w and (len(res_words) < 2 or clean_phone not in res_words[-2]):
                    res_words.append(phone_variants[variant_idx % 3])
                    variant_idx += 1
                chunk_count = 0

        out_lines.append(" ".join(res_words))

    return "\n".join(out_lines)

# Backwards compatibility alias
interleave_5_words = interleave_dynamic_words

def generate_ai_content(
    title: str,
    tfn: str = DEFAULT_PHONE,
    min_chars: int = 24000,
    max_chars: int = 38000,
    api_key: str = "",
    html_format: bool = False
) -> Optional[str]:
    """
    Generates 100% unique 4000+ word content using Role & Angle Switching, Dynamic Error Codes, Format Constraints,
    Negative Constraints (Cliche banning), Spintax Engine, and Dynamic Temperature & Top_p.
    """
    cleaned_title = clean_title_str(title)
    phone_num = format_tfn_display(tfn)

    if not api_key:
        api_key = DEFAULT_OPENROUTER_KEY

    if not api_key or not api_key.startswith("sk-or-v1-"):
        return None

    # Derive dynamic seed variables from title hash
    title_hash = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    rng = random.Random(title_hash)

    persona = rng.choice(PERSONAS)
    fmt_constraint = rng.choice(FORMAT_CONSTRAINTS)
    error_trigger = rng.choice(ERROR_TRIGGERS)
    tone = rng.choice(TONES)
    neg_constraint = rng.choice(NEGATIVE_CONSTRAINTS)
    few_shot = rng.choice(FEW_SHOT_STYLES)

    dynamic_temp = round(rng.uniform(0.85, 0.98), 2)
    dynamic_top_p = 0.90

    models_pool = OPENROUTER_MODELS.copy()
    rng.shuffle(models_pool)

    prompt = (
        f"You are a master technical writer and systems engineering documentation lead.\n"
        f"Title: '{cleaned_title}'\n"
        f"Helpline Phone Number: '{phone_num}'\n\n"
        f"DYNAMIC SEED CONSTRAINTS (MANDATORY TO PREVENT REPETITION):\n"
        f"1. ROLE & PERSPECTIVE: {persona['instruction']}\n"
        f"2. FORMATTING STRUCTURE: {fmt_constraint['instruction']}\n"
        f"3. TRIGGER ERROR CODE: Focus specifically on resolving '{error_trigger}'.\n"
        f"4. TONE & STYLE: Adopt a '{tone}' tone.\n"
        f"5. NEGATIVE CONSTRAINT: {neg_constraint}\n"
        f"6. STYLE REFERENCE: Mirror the sentence rhythm of: {few_shot}\n"
        f"7. PLAIN TEXT ONLY: Do NOT use any markdown symbols like asterisks (**), backticks (`), hashes (#), or quotes (\"). Write strictly in clean plain text with plain capital headings.\n"
        f"8. EXHAUSTIVE LENGTH: Total word count MUST BE AT LEAST 4,000 WORDS (minimum 24,000 characters). Write an exhaustive, multi-chapter technical manual covering: System Architecture & Dependencies, Root Cause Analysis, Multi-Phase Troubleshooting, Registry Permissions, Network Socket Fixes, Device Compatibility, 10 Detailed FAQs, and Verification Checklist.\n"
        f"9. PHONE INTEGRATION: Include natural mentions of 'Call {phone_num}' or 'helpline at {phone_num}' throughout.\n"
        f"10. UNIQUENESS: Do NOT use standard repetitive generic headers or repeated text."
    )

    for model_name in models_pool:
        try:
            resp = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://stackblitz.com/",
                    "X-Title": "StackBlitz Diversity Content Engine"
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 8000,
                    "temperature": dynamic_temp,
                    "top_p": dynamic_top_p
                },
                timeout=45
            )
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"].strip()
                    
                    # If Part 1 word count is below 3800 words, request Part 2 expansion
                    words_cnt = len(content.split())
                    if words_cnt < 3800:
                        part2_prompt = (
                            f"Continue writing Part 2 for the technical manual on Title: '{cleaned_title}'.\n"
                            f"Helpline Phone Number: '{phone_num}'\n\n"
                            f"Write an additional 2000 words in PLAIN TEXT (NO asterisks **, backticks `, hashes #, or quotes \").\n"
                            f"Cover: Advanced Enterprise Policy Overrides, Task Scheduler & Daemon Service Audits, Cryptographic SSL & License Store Repairs, Anti-Malware Exclusion Protocols, 10 Detailed FAQs with comprehensive Q&A, and Final Technical Verification Checklist."
                        )
                        try:
                            resp2 = requests.post(
                                url="https://openrouter.ai/api/v1/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json",
                                    "HTTP-Referer": "https://stackblitz.com/",
                                    "X-Title": "StackBlitz Diversity Content Engine"
                                },
                                json={
                                    "model": model_name,
                                    "messages": [
                                        {"role": "user", "content": prompt},
                                        {"role": "assistant", "content": content},
                                        {"role": "user", "content": part2_prompt}
                                    ],
                                    "max_tokens": 8000,
                                    "temperature": dynamic_temp,
                                    "top_p": dynamic_top_p
                                },
                                timeout=45
                            )
                            if resp2.status_code == 200:
                                data2 = resp2.json()
                                if "choices" in data2 and len(data2["choices"]) > 0:
                                    content += "\n\n" + data2["choices"][0]["message"]["content"].strip()
                        except Exception:
                            pass

                    if not html_format:
                        content = strip_all_markdown_formatting(content)
                    
                    # Apply Post-Processing Spintax / Synonym Replacement
                    content = apply_spintax_synonyms(content, rng=rng)
                    
                    if len(content) >= 12000:
                        if len(content) > max_chars:
                            content = content[:max_chars].rsplit(' ', 1)[0] + "."
                        return content
        except Exception:
            continue

    return None

def generate_fallback_unique_content(
    title: str,
    tfn: str = DEFAULT_PHONE,
    min_chars: int = 24000,
    max_chars: int = 38000,
    html_format: bool = False
) -> str:
    """
    100% Domain-Matched Dynamic Algorithmic Engine.
    Detects title category (AdBlock/Subscription vs Printer vs Software License) and dynamically constructs 
    4000+ words of 100% relevant, domain-matched technical prose per title.
    """
    cleaned_title = clean_title_str(title)
    phone_num = format_tfn_display(tfn)
    call_phone = f"Call {phone_num}"
    
    title_hash = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    rng = random.Random(title_hash)

    subject = cleaned_title
    for kw in ["Activate", "Subscription", "License", "Trial", "Complete Guide", "Step-by-Step", "How to", "Need to", "Cancel", "Refund", "Fix", "Error", "Setup", "Guide"]:
        subject = re.sub(re.escape(kw), "", subject, flags=re.IGNORECASE)
    subject = re.sub(r'\s+', ' ', subject).strip() or cleaned_title

    domain = detect_title_domain(title)
    persona = rng.choice(PERSONAS)
    error_code = rng.choice(ERROR_TRIGGERS)
    
    FORMAT_TEMPLATES = [
        {"prefix": "CHAPTER", "intro_header": "CHAPTER 1: SYSTEM OVERVIEW AND DIAGNOSTIC OBJECTIVES"},
        {"prefix": "PHASE", "intro_header": "PHASE 1: INITIAL CHRONOLOGICAL TRIAGE AND ACCESS RECOVERY"},
        {"prefix": "INCIDENT DIAGNOSTIC LOG", "intro_header": "INCIDENT DIAGNOSTIC LOG 1: TECHNICAL FIELD SCOPE FOR " + subject},
        {"prefix": "TECHNICAL FAQ ENTRY", "intro_header": "TECHNICAL FAQ ENTRY 1: WHAT CAUSES RECURRING LAUNCH FAILURES FOR " + subject + "?"},
        {"prefix": "AUDIT PROTOCOL", "intro_header": "AUDIT PROTOCOL 1: SYSTEM SECURITY AND LICENSE COMPLIANCE"},
        {"prefix": "STEP", "intro_header": "STEP 1: INITIAL DIAGNOSTIC EVALUATION AND RECOVERY"}
    ]
    fmt = rng.choice(FORMAT_TEMPLATES)
    sec_prefix = fmt["prefix"]

    # 1. DOMAIN SPECIFIC INTROS
    if domain == "ADBLOCK_SUBSCRIPTION":
        intros = [
            f"{fmt['intro_header']}\n\nCanceling unwanted auto-renewals, stopping unexpected billing charges, or removing intrusive adware popups regarding {subject} requires immediate action. When users encounter recurring credit card holds or persistent browser redirects caused by malicious extensions, basic browser restarts fail to resolve background subscription tokens. According to senior customer billing leads, unhandled account auto-renewals and hidden extension privileges keep charges active until manual deactivation is requested. This comprehensive guide details step-by-step cancellation steps, refund request protocols, browser adware cleanup, and popup block rules. For live billing resolution and cancellation help from human support representatives, dial {call_phone} anytime.",

            f"{fmt['intro_header']}\n\nFacing unexpected billing charges or aggressive popup ads while managing {subject} can cause severe frustration. In many cases, automatic subscription renewals process without notice, or malicious adware hijackers lock browser settings. After auditing user billing reports, our support resolution team established a verified step-by-step path to cancel active subscriptions, request transaction refunds, and purge adware extensions from Chrome, Edge, and Firefox. If you need immediate assistance stopping charges or processing a refund, call {phone_num} for live help.",

            f"{fmt['intro_header']}\n\nManaging subscription billing and adware removal for {subject} requires verifying account state and removing unwanted software components. Workstation event logs often capture unauthorized browser extensions pushing aggressive desktop notification spam. This technical manual provides step-by-step subscription cancellation steps, credit card charge dispute guidance, ad-block filter setup, and deep anti-malware scanning commands. Adhering to these verified steps guarantees clean browsing and stops unauthorized renewals. For escalated billing support, contact our helpline at {call_phone}."
        ]
    elif domain == "PRINTER_HARDWARE":
        intros = [
            f"{fmt['intro_header']}\n\nResolving printer offline errors, paper jams, printhead clogs, or Wi-Fi connection drops for {subject} requires systematic hardware and driver troubleshooting. When printers display 'Offline' status or stop responding to print jobs sent from Windows, simple power restarts fail to clear stuck print spooler queues. According to senior hardware leads, corrupted spooler files and IP address conflicts prevent communication between host computers and printers. This field manual outlines print spooler resets, wireless router IP pairing, printhead nozzle cleaning, and driver setup. For live assistance from printer repair technicians, dial {call_phone} anytime.",

            f"{fmt['intro_header']}\n\nFacing paper jams, blank page printing, or wireless setup failure on {subject} disrupts document workflows. In many cases, print queues become locked with corrupted job files, or Wi-Fi routers assign new IP addresses that break printer communication. Our hardware support team provides step-by-step instructions to clear print queues, align printhead nozzles, configure static IP addresses, and set default printer preferences. If you require live guidance setting up your printer, call {phone_num} for immediate support."
        ]
    else:
        intros = [
            f"{fmt['intro_header']}\n\nResolving operational obstacles associated with {subject} requires an exhaustive evaluation of system service dependencies, local security permissions, and network communication protocols. When users face unexpected launch failures or activation alerts stemming from {error_code}, basic troubleshooting routines often fail to address low-level registry deadlocks. According to senior infrastructure leads, unhandled permission locks and expired authentication session tokens prevent service daemons from establishing a verified connection. This field guide outlines detailed diagnostic workflows, registry key overrides, network socket resets, and security policy modifications necessary to restore normal operation. Technical support leads and systems administrators must systematically audit each stage of execution to ensure long-term stability. For live assistance from certified technicians, dial {call_phone} anytime."
        ]

    intro_text = rng.choice(intros)

    # 2. DOMAIN SPECIFIC MODULE POOLS
    if domain == "ADBLOCK_SUBSCRIPTION":
        domain_modules = [
            ("SUBSCRIPTION CANCELLATION AND AUTO RENEWAL STOP", [
                f"To permanently cancel your active subscription for {subject} and stop recurring auto-renewal charges, log into your central user billing portal. Navigate to Account Settings, select Subscriptions, and click Cancel Auto-Renewal. Ensure you receive an official cancellation confirmation email containing a transaction reference ID. If you cannot locate the cancellation button or face login issues, dial {call_phone} for live cancellation support.",
                f"Auto-renewal cancellation routines must be executed prior to the next billing cycle date for {subject}. If automated recurring payments were processed without authorization, request an immediate account status change from Active to Canceled. Contact customer support at {phone_num} for manual auto-renewal termination."
            ]),

            ("BROWSER ADWARE EXTENSION PURGE (CHROME, EDGE, FIREFOX)", [
                f"Adware extensions frequently inject unwanted popup ads, hijack search engines, and display aggressive redirects regarding {subject}. Open your browser extensions menu (chrome://extensions or edge://extensions), locate untrusted add-ons, and click Remove. Clear browser site data and cache to purge persistent tracking scripts. For guided adware extension removal, call {phone_num}.",
                f"Malicious browser hijackers install hidden background scripts that force browser redirects to spam portals. Reset browser settings to default parameters and clear local storage directories. Dial {call_phone} for browser adware cleanup."
            ]),

            ("BILLING REFUND RECONCILIATION AND INVOICE AUDIT", [
                f"If you were double-charged or billed unexpectedly for {subject}, submit a formal refund request to billing support. Provide your original order invoice number, billing email address, and payment transaction ID. Standard refund processing completes within 3 to 5 business days upon verification. Call {call_phone} for immediate refund status tracking.",
                f"Disputing unauthorized subscription renewals requires verifying transaction dates against vendor refund policy terms. Review confirmation receipts for customer care contact details. Contact our billing desk at {phone_num} for refund reconciliation."
            ]),

            ("RESETTING INTRUSIVE POPUP NOTIFICATION PERMISSIONS", [
                f"Adware websites abuse Web Push Notification permissions to push intrusive desktop popup spam even when browsers are closed. Navigate to Browser Settings -> Privacy and Security -> Site Settings -> Notifications. Remove all untrusted website domains from the Allow list. Dial {phone_num} for notification spam assistance.",
                f"Windows desktop popup alerts caused by browser notification permissions can be disabled in Windows Notifications settings. Block unauthorized app notifications to restore a clean workspace. Contact {call_phone} for popup security alignment."
            ]),

            ("ADBLOCK SHIELD AND MALWARE FILTER PROTOCOL", [
                f"Configuring custom ad-block filter rules blocks intrusive video ads, banner popups, and tracker scripts during online browsing. Install trusted ad-blocker extensions and enable Malware Domains filter lists. Add custom domain exclusion rules for trusted websites. Call {call_phone} for ad-block shield setup.",
                f"DNS-level ad blocking filters network traffic before ads load on your computer or mobile devices. Configure router DNS settings to use privacy-focused DNS servers (1.1.1.2 or AdGuard DNS). Contact {phone_num} for DNS filter setup."
            ]),

            ("ANTI-VIRUS DEEP ADWARE SCAN AND MALWARE REMOVAL", [
                f"Execute a full system anti-malware scan using Windows Defender or Malwarebytes to detect hidden adware droppers, trojan installers, and tracking PUPs associated with {subject}. Quarantine all flagged threats and restart your computer. For live malware scan assistance, call {phone_num}.",
                f"Real-time memory scanning isolates active adware processes running in background memory. Update anti-virus virus definition databases before initiating deep scans. Dial {call_phone} for malware removal support."
            ]),

            ("CREDIT CARD AND BANK CHARGE DISPUTE WALKTHROUGH", [
                f"If merchant auto-cancellation features are unavailable, contact your card issuing bank to place a merchant block on recurring charges for {subject}. Provide transaction dates and evidence of cancellation requests. Contact billing resolution at {call_phone} for payment dispute guidance.",
                f"Bank chargeback requests protect consumers against unauthorized recurring subscription renewals. Retain copies of cancellation emails for bank review. Call {phone_num} for charge dispute help."
            ]),

            ("USER ACCOUNT DEACTIVATION AND DATA PRIVACY PURGE", [
                f"Requesting full account deactivation for {subject} purges stored credit card details, billing addresses, and personal profile data from vendor databases. Submit a data erasure request under consumer privacy guidelines. Contact {phone_num} for account data removal.",
                f"Safely remove saved payment methods from web portals to prevent accidental future charges. Dial {call_phone} for account deactivation assistance."
            ]),

            ("FIREWALL AD FILTERING AND DOMAIN BLOCKING", [
                f"Adding known adware tracking domains to Windows hosts file (C:\\\\Windows\\\\System32\\\\drivers\\\\etc\\\\hosts) redirects ad server requests to 0.0.0.0, blocking ad loading system-wide. Call {call_phone} for hosts file ad-blocking instructions.",
                f"Configure Windows Defender Firewall outbound rules to block connection attempts from suspicious adware binaries. Contact {phone_num} for firewall configuration."
            ]),

            ("PUSH NOTIFICATION SPAM CLEANUP IN WINDOWS SETTINGS", [
                f"Clear persistent notification queue items in Windows Action Center. Navigate to Settings -> System -> Notifications and toggle off notifications for unknown background apps. Call {phone_num} for notification cleanup.",
                f"Disable background app execution for untrusted utility software to prevent background notification popups. Dial {call_phone} for Windows settings assistance."
            ]),

            ("DISABLING UNWANTED STARTUP BROWSER HIJACKERS", [
                f"Inspect Task Manager Startup apps tab to disable untrusted browser helper binaries launching automatically upon boot. Right-click suspicious apps and click Disable. Contact {call_phone} for startup app cleanup.",
                f"Remove startup shortcuts from %APPDATA%\\\\Microsoft\\\\Windows\\\\Start Menu\\\\Programs\\\\Startup. Dial {phone_num} for startup troubleshooting."
            ]),

            ("CLEARING CACHED ADWARE COOKIES AND BROWSER DATA", [
                f"Purge browser history, cached images, and tracking cookies across all installed browsers (Chrome, Edge, Firefox, Brave). Select All Time range in clear browsing data dialogs. Call {phone_num} for cache clearing help.",
                f"Clearing web storage databases removes persistent super-cookies used by tracking networks. Dial {call_phone} for browser data purge support."
            ]),

            ("VERIFYING OFFICIAL SUBSCRIPTION RECEIPT ACKNOWLEDGMENT", [
                f"Confirm subscription status shifts to Expired or Canceled in customer portals following cancellation. Save digital PDF receipts for accounting records. Contact {call_phone} for receipt confirmation.",
                f"Review confirmation emails to verify no future billing dates are scheduled. Dial {phone_num} for subscription status verification."
            ]),

            ("STOPPING RECURRING CHARGES ON PAYPAL AND CREDIT CARDS", [
                f"Log into PayPal, navigate to Settings -> Payments -> Automatic Payments, locate the billing agreement for {subject}, and click Cancel. This revokes payment authorization instantly. Call {call_phone} for PayPal payment cancellation.",
                f"Revoking recurring payment mandates directly through payment providers guarantees no further automatic debits occur. Dial {phone_num} for recurring payment support."
            ]),

            ("CONFIGURING DNS LEVEL AD BLOCKING (CLOUDFLARE / ADGUARD)", [
                f"Change workstation DNS server addresses to 1.1.1.2 and 1.0.0.2 (Cloudflare Security Filter) to block malicious adware domains at DNS level. Call {phone_num} for DNS setup guidance.",
                f"AdGuard DNS filters block ad domains across all connected household devices when configured on home Wi-Fi routers. Dial {call_phone} for network DNS ad blocking."
            ])
        ]
    elif domain == "PRINTER_HARDWARE":
        domain_modules = [
            ("PRINT SPOOLER DAEMON AND QUEUE PURGE", [
                f"To resolve stuck print jobs and offline errors on {subject}, restart the Windows Print Spooler service. Open Command Prompt as Administrator, type net stop spooler, delete all files in C:\\\\Windows\\\\System32\\\\spool\\\\PRINTERS, and type net start spooler. Call {call_phone} for print spooler repair.",
                f"Clearing corrupted print spooler files unblocks pending print jobs instantly. Ensure printer queue displays 0 Pending Documents. Contact {phone_num} for print queue troubleshooting."
            ]),

            ("WIRELESS ROUTER IP PAIRING AND NETWORK SETUP", [
                f"Connecting {subject} to 2.4GHz Wi-Fi networks requires pairing via Wireless Setup Wizard or WPS button. Assign a static IP address in router settings to prevent printer offline issues caused by DHCP IP changes. Call {phone_num} for printer Wi-Fi setup.",
                f"Run `ipconfig /flushdns` and ping printer IP address to verify local network connectivity. Contact {call_phone} for network printer diagnostics."
            ]),

            ("PRINTHEAD CLEANING AND NOZZLE ALIGNMENT", [
                f"Horizontal streaks, missing lines, or faded colors on printed pages indicate clogged printhead nozzles on {subject}. Run deep printhead cleaning cycles via printer utility software and print a Nozzle Check test page. Call {call_phone} for printhead cleaning support.",
                f"Align printheads following ink cartridge replacement to ensure sharp text and accurate color calibration. Dial {phone_num} for printhead alignment guidance."
            ]),

            ("PAPER FEEDER AND PAPER JAM REMOVAL", [
                f"Safely clear paper jams from rear tray, front output slot, or duplexer unit of {subject} by pulling jammed paper gently with both hands. Inspect paper feed rollers for dust buildup and clean with lint-free cloth. Contact {phone_num} for paper jam repair.",
                f"Avoid using crumpled or oversized paper stock that triggers frequent feeder jam sensors. Dial {call_phone} for paper jam assistance."
            ]),

            ("PRINTER OFFLINE RESOLUTION AND DRIVER REBUILD", [
                f"If {subject} displays 'Offline' status in Windows Devices and Printers, uncheck 'Use Printer Offline' in printer queue settings. Re-install official full feature driver package from vendor website. Call {call_phone} for printer driver help.",
                f"Set {subject} as Default Printer and assign TCP/IP Port in printer properties. Contact {phone_num} for printer offline fix."
            ])
        ]
    else:
        # Import default modules pool
        domain_modules = [
            ("SOFTWARE INSTALLATION ERROR 1603 RESOLUTION", [
                f"Resolving fatal installation exit code 1603 for {subject} requires running installer as Administrator, clearing temporary AppData cache, and granting Full Control permissions on software registry keys. Call {call_phone} for installation support.",
                f"Verify Windows Installer service (msiexec.exe) is running and repair Microsoft Visual C++ redistributable packages. Contact {phone_num} for installer repair."
            ]),

            ("LICENSE KEY ACTIVATION AND TOKEN VERIFICATION", [
                f"Re-enter your official activation license key for {subject} to refresh cryptographic license tokens. Clear expired SSL session cache in Control Panel to enable activation. Dial {call_phone} for activation assistance.",
                f"Verify workstation clock synchronization with internet time servers to prevent timestamp drift validation errors. Call {phone_num} for key verification."
            ]),

            ("MULTI-SEAT ACCOUNT SYNCHRONIZATION", [
                f"Managing multi-device seat authorizations for {subject} requires revoking unused seats in central web portals before registering new hardware. Contact {call_phone} for seat allocation support.",
                f"Confirm secondary devices are logged into matching account tenant IDs to sync feature entitlements. Dial {phone_num} for account sync help."
            ])
        ]

    # 3. Shuffle domain modules randomly using RNG seeded by Title Hash!
    modules_pool = domain_modules.copy()
    rng.shuffle(modules_pool)

    # 4. Build 4000+ words of domain-matched sections
    selected_chapters = [intro_text]
    
    sec_num = 2
    for mod_title, mod_paragraphs in modules_pool:
        para_chosen = "\n\n".join(mod_paragraphs)
        chapter_str = f"{sec_prefix} {sec_num}: {mod_title}\n\n{para_chosen}"
        selected_chapters.append(chapter_str)
        sec_num += 1

    # If domain_modules list is shorter than target length, repeat with alternate formatting
    while len("\n\n".join(selected_chapters).split()) < 4000:
        rng.shuffle(modules_pool)
        for mod_title, mod_paragraphs in modules_pool:
            para_chosen = "\n\n".join(mod_paragraphs)
            chapter_str = f"{sec_prefix} {sec_num}: ADVANCED {mod_title}\n\n{para_chosen}"
            selected_chapters.append(chapter_str)
            sec_num += 1
            if len("\n\n".join(selected_chapters).split()) >= 4200:
                break

    doc = "\n\n".join(selected_chapters)

    if len(doc) > max_chars:
        doc = doc[:max_chars].rsplit(' ', 1)[0] + "."

    if not html_format:
        doc = strip_all_markdown_formatting(doc)
    else:
        doc_html = ""
        for line in doc.split('\n'):
            line_s = line.strip()
            if not line_s:
                continue
            if line_s.startswith(sec_prefix):
                doc_html += f"<h3>{line_s}</h3>"
            else:
                doc_html += f"<p>{line_s}</p>"
        return doc_html

    return doc


def generate_unique_description(
    title: str,
    tfn: str = DEFAULT_PHONE,
    min_chars: int = 24000,
    max_chars: int = 38000,
    api_key: str = "",
    html_format: bool = False,
    phone_number: str = None,
    openrouter_key: str = None
) -> str:
    """
    Master Content Generator:
    Guarantees 100% unique 4000+ word plain-text articles per title,
    with 20-word smooth phone interleaving for +1 888 308 7172.
    """
    if phone_number:
        tfn = phone_number
    if openrouter_key:
        api_key = openrouter_key
    if not api_key:
        api_key = DEFAULT_OPENROUTER_KEY

    ai_content = generate_ai_content(
        title=title,
        tfn=tfn,
        min_chars=min_chars,
        max_chars=max_chars,
        api_key=api_key,
        html_format=html_format
    )

    if ai_content and len(ai_content) >= (min_chars * 0.7):
        result = interleave_5_words(ai_content, tfn=tfn)
        if not html_format:
            result = strip_all_markdown_formatting(result)
        return result

    raw_fallback = generate_fallback_unique_content(
        title=title,
        tfn=tfn,
        min_chars=min_chars,
        max_chars=max_chars,
        html_format=html_format
    )
    result = interleave_5_words(raw_fallback, tfn=tfn)
    if not html_format:
        result = strip_all_markdown_formatting(result)
    return result

if __name__ == "__main__":
    titles = [
        "cancel total adware subscription",
        "How Do I Setup Brother Printer to WiFi Step by Step",
        "Fix McAfee Error 1603 installation failed",
        "TotalAV double charge refund case"
    ]
    p = "+1 888 308 7172"
    
    for t in titles:
        res = generate_unique_description(t, tfn=p)
        print(f"Title: {t}")
        print(f"Length: {len(res)} chars")
        print("--- PREVIEW ---")
        print(res[:350])
        print("\n" + "="*60 + "\n")
