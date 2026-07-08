import zipfile
import os

def main():
    scratch_dir = os.path.dirname(__file__)
    zip_path = os.path.join(scratch_dir, "generated_app.zip")
    extract_dir = os.path.join(scratch_dir, "extracted_app")
    
    print(f"[*] Extracting {zip_path} to {extract_dir}...")
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
        
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    print("[+] Extraction completed successfully!")
    print("[*] Listing files in extracted app:")
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), extract_dir)
            print(f"  - {rel_path}")

if __name__ == "__main__":
    main()
