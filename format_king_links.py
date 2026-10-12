import re

def title_to_slug(title: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip().lower()
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug

TITLES_WITH_IDS = [
    ("Why Is AVG Activation Not Working? (Causes + Step-by-Step Solution)", "401383"),
    ("How to Confirm Your Bitdefender Purchase & Retrieve Your Key", "401384"),
    ("How to Set Up PC Matic for Beginners (Simple Step-by-Step Setup)", "401385"),
    ("Webroot Activation Failed After Reinstall? Fix It Fast (Step-by-Step)", "401386"),
    ("How to Install ESET on Windows 11 Step by Step (Beginner Guide)", "401387"),
    ("How to Activate Avast Offline (No Internet Activation Method)", "401389"),
    ("How to Set Up and Activate AVG Software for Beginners (Complete Guide)", "401391"),
    ("How to Enable CCleaner License After Purchase (Full Activation Guide)", "401393"),
    ("How to Use an Avast License Key Securely (Step-by-Step Activation)", "401394"),
    ("How to Activate McAfee After Trial Expiration (Full Renewal Guide)", "401396")
]

full_links = []
for title, disc_id in TITLES_WITH_IDS:
    slug = title_to_slug(title)
    url = f"https://community.king.com/en/candy-crush-friends-saga/discussion/{disc_id}/{slug}#latest"
    full_links.append(url)

with open("king_10_links.txt", "w", encoding="utf-8") as f:
    for l in full_links:
        f.write(f"{l}\n")

print("Full Public URLs with Slug & #latest saved to king_10_links.txt:\n")
for idx, l in enumerate(full_links, 1):
    print(f"{idx}. {l}")
