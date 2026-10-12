import os
import glob
from usal_matricula_uploader import upload_pdf_to_usal

def main():
    target_dir = r"C:\123\StackBlitz_Articles_PDFs (4)"
    if not os.path.exists(target_dir):
        print(f"[-] Directory not found: {target_dir}")
        return

    pdf_files = glob.glob(os.path.join(target_dir, "*.pdf"))
    pdf_files.sort()

    print(f"[*] Found {len(pdf_files)} PDF file(s) in {target_dir}", flush=True)
    if not pdf_files:
        print("[-] No PDF files found.", flush=True)
        return

    output_links_path = os.path.join(os.getcwd(), "user_uploaded_links.txt")

    success_count = 0
    results = []

    print("\n=== STARTING BATCH PDF UPLOAD & LIVE LINK GENERATION ===", flush=True)
    with open(output_links_path, "w", encoding="utf-8") as out_file:
        for idx, pdf_path in enumerate(pdf_files, 1):
            fname = os.path.basename(pdf_path)
            print(f"[{idx}/{len(pdf_files)}] Uploading: {fname}...", flush=True)
            
            res = upload_pdf_to_usal(pdf_path, filename=fname, submit_form=True)
            if res.get("success") and res.get("url"):
                url = res["url"]
                success_count += 1
                results.append((fname, url))
                out_file.write(f"{url}\n")
                out_file.flush()
                print(f"    [+] LIVE URL: {url}")
            else:
                err = res.get("error", "Upload failed")
                print(f"    [-] FAILED: {err}")

    print("\n=== BATCH UPLOAD COMPLETED ===")
    print(f"[+] Total Uploaded: {success_count}/{len(pdf_files)}")
    print(f"[+] All live links saved to: {output_links_path}")

if __name__ == "__main__":
    main()
