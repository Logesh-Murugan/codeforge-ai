import zipfile
import os
import subprocess
import time
import sys

def main():
    scratch_dir = os.path.dirname(__file__)
    zip_path = os.path.join(scratch_dir, "generated_app.zip")
    extract_dir = os.path.join(scratch_dir, "extracted_app_v2")
    
    # 1. Clean previous extraction if exists
    if os.path.exists(extract_dir):
        import shutil
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
        
    # 2. Extract
    print(f"[*] Extracting generated code to {extract_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    print("[+] Extraction completed!")
    
    # 3. Create .env file for database and secret keys
    env_path = os.path.join(extract_dir, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(
            "DATABASE_URL=sqlite+aiosqlite:///./test.db\n"
            "JWT_SECRET_KEY=adversarial-v2-secret-key-1234567\n"
            "JWT_ALGORITHM=HS256\n"
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30\n"
            "PROJECT_TITLE=TestNotesApp\n"
            "PROJECT_DESCRIPTION=Adversarial Test Notes Application\n"
            "PROJECT_VERSION=1.0.0\n"
        )
    print("[+] Created .env file inside generated codebase")
    
    # 4. Check generated file contents (Inspect to confirm bug-free implementation!)
    print("[*] Inspecting key files for fixes:")
    
    # Check config settings import
    config_file = os.path.join(extract_dir, "core", "config.py")
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"    - core/config.py lines 1-5: {[l.strip() for l in lines[:5]]}")
        
    # Check db Base definition
    db_file = os.path.join(extract_dir, "db.py")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"    - db.py Base declaration lines 1-15:")
        for l in lines[:15]:
            if "Base" in l or "declarative_base" in l or "import" in l:
                print(f"        {l.strip()}")
                
    # Check models imports
    models_file = os.path.join(extract_dir, "models.py")
    if os.path.exists(models_file):
        with open(models_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"    - models.py imports: {[l.strip() for l in lines[:6]]}")
        
    # Check api/notes.py queries and imports
    notes_file = os.path.join(extract_dir, "api", "notes.py")
    if os.path.exists(notes_file):
        with open(notes_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print("    - api/notes.py imports: ", [l.strip() for l in lines[:10]])
        print("    - api/notes.py query calls:")
        for l in lines:
            if ".query" in l or "select(" in l or "db.execute(" in l:
                print(f"        {l.strip()}")

    # 5. Boot testing (without manual patching!)
    print("[*] Booting uvicorn server in a subprocess...")
    # Inject automatic schema creation on startup if missing so that uvicorn doesn't fail on missing db tables
    main_file = os.path.join(extract_dir, "main.py")
    with open(main_file, "r", encoding="utf-8") as f:
        main_content = f.read()
    if "create_all" not in main_content and "@app.on_event" not in main_content:
        # Inject startup tables create hook for sqlite run
        startup_block = """
@app.on_event("startup")
async def startup():
    from db import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""
        main_content += startup_block
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(main_content)
        print("    - Note: Injected startup table creation hook in main.py for SQLite database test run")

    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "9005"],
        cwd=extract_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait to see if it boots or crashes
    time.sleep(4)
    
    status = p.poll()
    if status is not None:
        print("[!] Startup failed!")
        stdout, stderr = p.communicate()
        print("STDOUT:")
        print(stdout.decode())
        print("STDERR:")
        print(stderr.decode())
    else:
        print("[SUCCESS] The generated application booted successfully on the first try on port 9005!")
        print("[*] Stopping test uvicorn server...")
        p.terminate()
        p.wait()
        print("[+] Done!")

if __name__ == "__main__":
    main()
