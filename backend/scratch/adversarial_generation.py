import requests
import time
import sys
import os
import json
import random

BACKEND_URL = "https://codeforge-ai-klzw.onrender.com"

def main():
    session = requests.Session()
    
    # 1. Generate unique email
    rand_suffix = random.randint(1000, 9999)
    email = f"adv_tester_{rand_suffix}@codeforge.com"
    password = "TestPass123!"
    
    print(f"[*] Registering user on live system: {email}")
    reg_response = session.post(
        f"{BACKEND_URL}/auth/register",
        json={"email": email, "password": password}
    )
    if reg_response.status_code not in (200, 201):
        print(f"[!] Registration failed: {reg_response.status_code} - {reg_response.text}")
        sys.exit(1)
        
    print("[*] Logging in...")
    login_response = session.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if login_response.status_code != 200:
        print(f"[!] Login failed: {login_response.status_code} - {login_response.text}")
        sys.exit(1)
        
    token = login_response.json().get("access_token")
    if not token:
        print("[!] Token not found in response!")
        sys.exit(1)
        
    print("[*] Authentication successful!")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # 2. Create project
    idea = (
        "A personal notes app where users can sign up, create private notes, "
        "and only the note's author can view, edit, or delete it."
    )
    print("[*] Creating project...")
    proj_response = session.post(
        f"{BACKEND_URL}/projects",
        json={"title": "Adversarial Test Notes App", "description": idea}
    )
    if proj_response.status_code not in (200, 201):
        print(f"[!] Project creation failed: {proj_response.status_code} - {proj_response.text}")
        sys.exit(1)
        
    project = proj_response.json()
    project_id = project.get("id")
    print(f"[+] Project created successfully! ID: {project_id}")
    
    # 3. Trigger generation
    print("[*] Triggering codebase generation...")
    gen_response = session.post(f"{BACKEND_URL}/projects/{project_id}/generate", json={"idea": idea})
    if gen_response.status_code != 200:
        print(f"[!] Triggering generation failed: {gen_response.status_code} - {gen_response.text}")
        sys.exit(1)
        
    print("[+] Generation triggered successfully. Polling status...")
    
    # 4. Poll status
    start_time = time.time()
    while True:
        status_resp = session.get(f"{BACKEND_URL}/projects/{project_id}/status")
        if status_resp.status_code != 200:
            print(f"[!] Status check failed: {status_resp.status_code} - {status_resp.text}")
            time.sleep(10)
            continue
            
        status_data = status_resp.json()
        print(f"[*] Elapsed time: {int(time.time() - start_time)}s")
        
        # Check all runs
        all_done = True
        failed_agent = None
        
        # If status_data is a list of runs
        for run in status_data:
            agent_name = run.get("agent_name")
            status = run.get("status")
            print(f"    - Agent: {agent_name:<20} Status: {status}")
            if status == "failed":
                failed_agent = agent_name
            elif status != "completed":
                all_done = False
                
        if failed_agent:
            print(f"[!] Generation failed on agent: {failed_agent}")
            sys.exit(1)
            
        if all_done and len(status_data) >= 8:
            print(f"[+] All agents finished successfully in {int(time.time() - start_time)}s!")
            break
            
        time.sleep(10)
        
    # 5. Download codebase ZIP
    print("[*] Downloading generated zip archive...")
    dl_resp = session.get(f"{BACKEND_URL}/projects/{project_id}/download")
    if dl_resp.status_code != 200:
        print(f"[!] ZIP download failed: {dl_resp.status_code} - {dl_resp.text}")
        sys.exit(1)
        
    zip_path = os.path.join(os.path.dirname(__file__), "generated_app.zip")
    with open(zip_path, "wb") as f:
        f.write(dl_resp.content)
        
    print(f"[+] Download complete! Saved to {zip_path}")

if __name__ == "__main__":
    main()
