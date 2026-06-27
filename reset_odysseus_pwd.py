
import json
import bcrypt
import os

AUTH_FILE = "/app/data/auth.json"

def reset_password(username, new_password):
    if not os.path.exists(AUTH_FILE):
        print(f"Error: {AUTH_FILE} not found")
        return
    
    with open(AUTH_FILE, "r") as f:
        auth_data = json.load(f)
    
    if username not in auth_data["users"]:
        print(f"Error: User {username} not found")
        return
    
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    auth_data["users"][username]["password_hash"] = hashed
    
    with open(AUTH_FILE, "w") as f:
        json.dump(auth_data, f, indent=2)
    
    print(f"Successfully reset password for {username}")

if __name__ == "__main__":
    reset_password("admin", "twisterlab_admin")
