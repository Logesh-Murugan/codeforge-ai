import requests
import json

def main():
    session = requests.Session()
    
    # 1. Register users
    print("[*] Registering User A (usera@test.com)...")
    reg_a = session.post(
        "http://127.0.0.1:9000/auth/register",
        json={"email": "usera@test.com", "username": "usera", "password": "Password123!"}
    )
    print(f"    - Register User A status: {reg_a.status_code}")
    print(f"    - Response A: {reg_a.text}")
    
    print("[*] Registering User B (userb@test.com)...")
    reg_b = session.post(
        "http://127.0.0.1:9000/auth/register",
        json={"email": "userb@test.com", "username": "userb", "password": "Password123!"}
    )
    print(f"    - Register User B status: {reg_b.status_code}")
    print(f"    - Response B: {reg_b.text}")
    
    # 2. Log in
    print("[*] Logging in as User A...")
    login_a = session.post(
        "http://127.0.0.1:9000/auth/login",
        data={"username": "usera@test.com", "password": "Password123!"}
    )
    token_a = login_a.json().get("access_token")
    print(f"    - Token A: {token_a[:20]}...")
    
    print("[*] Logging in as User B...")
    login_b = session.post(
        "http://127.0.0.1:9000/auth/login",
        data={"username": "userb@test.com", "password": "Password123!"}
    )
    token_b = login_b.json().get("access_token")
    print(f"    - Token B: {token_b[:20]}...")
    
    # 3. Create resource as User A
    print("[*] Creating note as User A...")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    create_res = session.post(
        "http://127.0.0.1:9000/notes/",
        json={"title": "A's Private Info", "content": "This is top secret."},
        headers=headers_a
    )
    print(f"    - Create Note status: {create_res.status_code}")
    note = create_res.json()
    note_id = note.get("id")
    print(f"    - Created Note ID: {note_id}")
    print(f"    - Note content: {json.dumps(note)}")
    
    # 4. Adversarial tests as User B
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    print(f"[*] User B GET on User A's resource (ID: {note_id})...")
    get_res = session.get(f"http://127.0.0.1:9000/notes/{note_id}", headers=headers_b)
    print(f"    - Response status: {get_res.status_code}")
    print(f"    - Response body: {get_res.text}")
    
    print(f"[*] User B PUT on User A's resource (ID: {note_id})...")
    put_res = session.put(
        f"http://127.0.0.1:9000/notes/{note_id}",
        json={"title": "Hacked Title", "content": "Hacked Content"},
        headers=headers_b
    )
    print(f"    - Response status: {put_res.status_code}")
    print(f"    - Response body: {put_res.text}")
    
    print(f"[*] User B DELETE on User A's resource (ID: {note_id})...")
    del_res = session.delete(f"http://127.0.0.1:9000/notes/{note_id}", headers=headers_b)
    print(f"    - Response status: {del_res.status_code}")
    print(f"    - Response body: {del_res.text}")
    
    # 5. List resources as A and B
    print("[*] Listing notes as User A...")
    list_a = session.get("http://127.0.0.1:9000/notes/", headers=headers_a)
    print(f"    - User A Notes status: {list_a.status_code}")
    print(f"    - User A Notes content: {list_a.text}")
    
    print("[*] Listing notes as User B...")
    list_b = session.get("http://127.0.0.1:9000/notes/", headers=headers_b)
    print(f"    - User B Notes status: {list_b.status_code}")
    print(f"    - User B Notes content: {list_b.text}")

if __name__ == "__main__":
    main()
