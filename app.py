import os
import subprocess
from flask import Flask, request, jsonify, send_file
import requests
import io
import zipfile
import time
from threading import Thread

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

PANELS_KOCHENG = {
    "server1": {
        "url": "https://console.kocheng.tech",
        "api_key": "ptla_iSj8zMtCvlSV05XphQKr4QLKUa7t5jm2CG9rXsJlYSZ",
        "client_api_key": "ptlc_OurES0aIGdkGJIHxQF4Iym1FwqLllcJczG1fBtBC2kZ"
    },
    "server2": {
        "url": "https://console.kocheng.biz.id",
        "api_key": "ptla_VyaEyCBXizyfI5Cew5RmfSXOhUdSzJT68KRTHWOXG7G",
        "client_api_key": "ptlc_VXyniYgN9KnHm0xp3oGpLt3iSotH8tVIkQGCbTcOoSo"
    }
    # Bisa ditambah server3, dst...
}

PANELS_SKYFORGIA = {
    "server1": {
        "url": "https://console.skyforgia.web.id",
        "api_key": "ptla_KCpE3wrwnAsOBUp54Glx8onHfVEvtC0PDtDtuZIUz0v",
        "client_api_key": "ptlc_rAAYmyY18RGbDR3aaLW4VbamzuZfSEdAekKGo8ankwm"
    }
    # Bisa ditambah server3, dst...
}

def get_headers_kocheng(panel_id):
    return {
        "Authorization": f"Bearer {PANELS_KOCHENG[panel_id]['api_key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
def get_headers_skyforgia(panel_id):
    return {
        "Authorization": f"Bearer {PANELS_SKYFORGIA[panel_id]['api_key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
def get_client_headers_kocheng(panel_id):
    return {
        "Authorization": f"Bearer {PANELS_KOCHENG[panel_id]['client_api_key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
def get_client_headers_skyforgia(panel_id):
    return {
        "Authorization": f"Bearer {PANELS_SKYFORGIA[panel_id]['client_api_key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

# ==================================================================
# LOGIN MEGA SAAT CONTAINER START
# ==================================================================
MEGA_EMAIL = "kentukimeme@gmail.com"
MEGA_PASSWORD = "Bintang123**"

def mega_login():
    if not MEGA_EMAIL or not MEGA_PASSWORD:
        print("[MEGA] ERROR: MEGA_EMAIL atau MEGA_PASSWORD belum di-set!")
        return

    print("[MEGA] Logging in...")
    result = subprocess.run(
        ["mega-login", MEGA_EMAIL, MEGA_PASSWORD],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("[MEGA] Login failed:", result.stderr)
    else:
        print("[MEGA] Login success!")

mega_login()  # auto login


# ==================================================================
# Helper: Menjalankan MEGAcmd
# ==================================================================
def mega_put_kocheng(local, remote="/Kocheng_backup/", retry=3, timeout=300):
    filename = os.path.basename(local)
    remote_path = remote + filename

    for attempt in range(1, retry + 1):
        try:
            print(f"[MEGA] Upload attempt {attempt}: {local}")

            result = subprocess.run(
                ["mega-put", local, remote],
                capture_output=True,
                text=True,
                timeout=timeout   # ✅ cegah hang
            )

            if result.returncode == 0:
                print("[MEGA] Upload sukses")

                # ✅ LANGSUNG AMBIL LINK
                export = subprocess.run(
                    ["mega-export", "-a", remote_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if export.returncode == 0:
                    for line in export.stdout.splitlines():
                        if "https://mega.nz/" in line:
                            mega_link = line.strip()
                            print("[MEGA] Link:", mega_link)

                            return {
                                "success": True,
                                "link": mega_link
                            }

                print("[MEGA] Gagal ambil link:", export.stderr)
                return {
                    "success": True,
                    "link": None
                }

            print("[MEGA] Upload gagal:", result.stderr)

        except subprocess.TimeoutExpired:
            print("[MEGA] Timeout saat upload (mega-put terlalu lama)")

        except Exception as e:
            print("[MEGA] Error:", str(e))

        time.sleep(5)

    return {
        "success": False,
        "link": None
    }
    
def mega_put_skyforgia(local, remote="/Skyforgia_backup/", retry=3, timeout=300):
    filename = os.path.basename(local)
    remote_path = remote + filename

    for attempt in range(1, retry + 1):
        try:
            print(f"[MEGA] Upload attempt {attempt}: {local}")

            result = subprocess.run(
                ["mega-put", local, remote],
                capture_output=True,
                text=True,
                timeout=timeout   # ✅ cegah hang
            )

            if result.returncode == 0:
                print("[MEGA] Upload sukses")

                # ✅ LANGSUNG AMBIL LINK
                export = subprocess.run(
                    ["mega-export", "-a", remote_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if export.returncode == 0:
                    for line in export.stdout.splitlines():
                        if "https://mega.nz/" in line:
                            mega_link = line.strip()
                            print("[MEGA] Link:", mega_link)

                            return {
                                "success": True,
                                "link": mega_link
                            }

                print("[MEGA] Gagal ambil link:", export.stderr)
                return {
                    "success": True,
                    "link": None
                }

            print("[MEGA] Upload gagal:", result.stderr)

        except subprocess.TimeoutExpired:
            print("[MEGA] Timeout saat upload (mega-put terlalu lama)")

        except Exception as e:
            print("[MEGA] Error:", str(e))

        time.sleep(5)

    return {
        "success": False,
        "link": None
    }

def mega_get(remote, local):
    return subprocess.run(
        ["mega-get", remote, local],
        capture_output=True, text=True
    )

def mega_check(remote):
    return subprocess.run(
        ["mega-ls", remote],
        capture_output=True, text=True
    )
 
def get_ptero_user_kocheng(email, panel_id):
    panel = PANELS_KOCHENG.get(panel_id)
    if not panel:
        return None

    url = f"{panel['url']}/api/application/users?filter[email]={email}"
    res = requests.get(url, headers=get_headers_kocheng(panel_id)).json()
    if "data" not in res or res["meta"]["pagination"]["total"] == 0:
        return None
    return res["data"][0]["attributes"]
    
def get_ptero_user_skyforgia(email, panel_id):
    panel = PANELS_SKYFORGIA.get(panel_id)
    if not panel:
        return None

    url = f"{panel['url']}/api/application/users?filter[email]={email}"
    res = requests.get(url, headers=get_headers_skyforgia(panel_id)).json()
    if "data" not in res or res["meta"]["pagination"]["total"] == 0:
        return None
    return res["data"][0]["attributes"]

def get_servers_by_userid_kocheng(user_id, panel_id):
    panel = PANELS_KOCHENG.get(panel_id)
    if not panel:
        return []
    url = f"{panel['url']}/api/application/users/{user_id}?include=servers"
    res = requests.get(url, headers=get_headers_kocheng(panel_id)).json()
    if "relationships" not in res["attributes"]:
        return []
    return res["attributes"]["relationships"]["servers"]["data"]
    
def get_servers_by_userid_skyforgia(user_id, panel_id):
    panel = PANELS_SKYFORGIA.get(panel_id)
    if not panel:
        return []
    url = f"{panel['url']}/api/application/users/{user_id}?include=servers"
    res = requests.get(url, headers=get_headers_skyforgia(panel_id)).json()
    if "relationships" not in res["attributes"]:
        return []
    return res["attributes"]["relationships"]["servers"]["data"]
    
def list_files_kocheng(panel_id, uuid, directory="/"):
    panel = PANELS_KOCHENG.get(panel_id)
    url = f"{panel['url']}/api/client/servers/{uuid}/files/list?directory={directory}"
    return requests.get(url, headers=get_client_headers_kocheng(panel_id)).json()
    
def list_files_skyforgia(panel_id, uuid, directory="/"):
    panel = PANELS_SKYFORGIA.get(panel_id)
    url = f"{panel['url']}/api/client/servers/{uuid}/files/list?directory={directory}"
    return requests.get(url, headers=get_client_headers_skyforgia(panel_id)).json()

def ptero_download_file_kocheng(panel_id, uuid, path):
    panel = PANELS_KOCHENG.get(panel_id)
    url = f"{panel['url']}/api/client/servers/{uuid}/files/contents?file={path}"
    res = requests.get(url, headers=get_client_headers_kocheng(panel_id))
    return res.content if res.status_code == 200 else None
    
def ptero_download_file_skyforgia(panel_id, uuid, path):
    panel = PANELS_SKYFORGIA.get(panel_id)
    url = f"{panel['url']}/api/client/servers/{uuid}/files/contents?file={path}"
    res = requests.get(url, headers=get_client_headers_skyforgia(panel_id))
    return res.content if res.status_code == 200 else None
    
def build_zip_file_kocheng(panel_id, uuid, email):
    visited_paths = set()

    zip_path = f"/tmp/backup_{email}.zip"

    # ✅ Pastikan tidak ada file lama
    if os.path.exists(zip_path):
        os.remove(zip_path)

    zipf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)

    def add_path(base_dir="/"):
        if base_dir in visited_paths:
            return
        visited_paths.add(base_dir)

        files = list_files_kocheng(panel_id, uuid, base_dir)

        for f in files.get("data", []):
            name = f["attributes"]["name"]
            is_file = f["attributes"]["is_file"]
            size = f["attributes"]["size"]

            rel_path = os.path.join(base_dir, name).replace("//", "/")

            if name in ("node_modules", ".", ".."):
                continue

            # ✅ Skip file besar
            if is_file and size > 50 * 1024 * 1024:
                continue

            if is_file:
                content = ptero_download_file_kocheng(panel_id, uuid, rel_path)
                if content:
                    zipf.writestr(rel_path.lstrip("/"), content)
            else:
                add_path(rel_path)

    add_path("/")
    zipf.close()

    return zip_path
    
def build_zip_file_skyforgia(panel_id, uuid, email):
    visited_paths = set()

    zip_path = f"/tmp/backup_{email}.zip"

    # ✅ Pastikan tidak ada file lama
    if os.path.exists(zip_path):
        os.remove(zip_path)

    zipf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)

    def add_path(base_dir="/"):
        if base_dir in visited_paths:
            return
        visited_paths.add(base_dir)

        files = list_files_skyforgia(panel_id, uuid, base_dir)

        for f in files.get("data", []):
            name = f["attributes"]["name"]
            is_file = f["attributes"]["is_file"]
            size = f["attributes"]["size"]

            rel_path = os.path.join(base_dir, name).replace("//", "/")

            if name in ("node_modules", ".", ".."):
                continue

            # ✅ Skip file besar
            if is_file and size > 50 * 1024 * 1024:
                continue

            if is_file:
                content = ptero_download_file_skyforgia(panel_id, uuid, rel_path)
                if content:
                    zipf.writestr(rel_path.lstrip("/"), content)
            else:
                add_path(rel_path)

    add_path("/")
    zipf.close()

    return zip_path
    
def notify_heroku_backup_done_kocheng(email, filename, mega_link):
    try:
        requests.post(
            "https://control.kocheng.biz.id/api/backup-finished",
            json={
                "email": email,
                "filename": filename,
                "mega_link": mega_link
            },
            timeout=5
        )
    except Exception as e:
        print("Callback gagal:", str(e))
        
def notify_heroku_backup_done_skyforgia(email, filename, mega_link):
    try:
        requests.post(
            "https://control.skyforgia.web.id/api/backup-finished",
            json={
                "email": email,
                "filename": filename,
                "mega_link": mega_link
            },
            timeout=5
        )
    except Exception as e:
        print("Callback gagal:", str(e))
        
def process_backup_kocheng(email, panel_id):
    zip_path = None

    try:
        p_user = get_ptero_user_kocheng(email, panel_id)
        if not p_user:
            print("User panel tidak ditemukan")
            return

        servers = get_servers_by_userid_kocheng(p_user["id"], panel_id)
        if not servers:
            print("Server tidak ditemukan")
            return

        uuid = servers[0]["attributes"]["uuid"]

        print("Mulai build zip:", email)

        zip_path = build_zip_file_kocheng(panel_id, uuid, email)
        filename = os.path.basename(zip_path)

        print("Upload ke MEGA:", filename)

        with open(zip_path, "rb") as f:
            files = {
                "file": (filename, f, "application/zip")
            }

            r = requests.post(
                f"{MEGA_API}/mega/kocheng/upload",
                files=files,
                timeout=300
            )

            if r.status_code != 200:
                print("Gagal upload ke MEGA:", r.text)
                return

            data = r.json()
            mega_link = data.get("mega_link")

            print("Upload selesai:", filename)
            print("Link MEGA:", mega_link)

        # ✅ NOTIFY HEROKU + KIRIM LINK
        notify_heroku_backup_done_kocheng(email, filename, mega_link)

    except Exception as e:
        print("Backup error:", str(e))

    finally:
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)
        
def process_backup_skyforgia(email, panel_id):
    zip_path = None

    try:
        p_user = get_ptero_user_skyforgia(email, panel_id)
        if not p_user:
            print("User panel tidak ditemukan")
            return

        servers = get_servers_by_userid_skyforgia(p_user["id"], panel_id)
        if not servers:
            print("Server tidak ditemukan")
            return

        uuid = servers[0]["attributes"]["uuid"]

        print("Mulai build zip:", email)

        zip_path = build_zip_file_skyforgia(panel_id, uuid, email)
        filename = os.path.basename(zip_path)

        print("Upload ke MEGA:", filename)

        with open(zip_path, "rb") as f:
            files = {
                "file": (filename, f, "application/zip")
            }

            r = requests.post(
                f"{MEGA_API}/mega/skyforgia/upload",
                files=files,
                timeout=300
            )

            if r.status_code != 200:
                print("Gagal upload ke MEGA:", r.text)
                return

            data = r.json()
            mega_link = data.get("mega_link")

            print("Upload selesai:", filename)
            print("Link MEGA:", mega_link)

        # ✅ NOTIFY HEROKU + KIRIM LINK
        notify_heroku_backup_done_skyforgia(email, filename, mega_link)

    except Exception as e:
        print("Backup error:", str(e))

    finally:
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)

# ==================================================================
# UPLOAD (Heroku -> Railway -> MEGA)
# ==================================================================
@app.route("/mega/kocheng/upload", methods=["POST"])
def upload_kocheng():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename
    local_path = os.path.join(UPLOAD_DIR, filename)
    file.save(local_path)

    result = mega_put_kocheng(local_path)

    if not result["success"]:
        return jsonify({"error": "Mega upload failed"}), 500

    return jsonify({
        "message": "Uploaded to MEGA",
        "filename": filename,
        "mega_link": result["link"]
    })
    
@app.route("/mega/skyforgia/upload", methods=["POST"])
def upload_kocheng():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename
    local_path = os.path.join(UPLOAD_DIR, filename)
    file.save(local_path)

    result = mega_put_skyforgia(local_path)

    if not result["success"]:
        return jsonify({"error": "Mega upload failed"}), 500

    return jsonify({
        "message": "Uploaded to MEGA",
        "filename": filename,
        "mega_link": result["link"]
    })

@app.route("/build/kocheng/backup", methods=["POST"])
def build_backup_kocheng():
    data = request.get_json()

    email = data.get("email")
    panel_id = data.get("panel_id")

    if not email or not panel_id:
        return jsonify({"error": "email & panel_id wajib"}), 400

    Thread(
        target=process_backup_kocheng,
        args=(email, panel_id)
    ).start()

    return jsonify({
        "status": "Backup sedang diproses",
        "email": email
    }), 200
    
@app.route("/build/skyforgia/backup", methods=["POST"])
def build_backup_kocheng():
    data = request.get_json()

    email = data.get("email")
    panel_id = data.get("panel_id")

    if not email or not panel_id:
        return jsonify({"error": "email & panel_id wajib"}), 400

    Thread(
        target=process_backup_skyforgia,
        args=(email, panel_id)
    ).start()

    return jsonify({
        "status": "Backup sedang diproses",
        "email": email
    }), 200
# ==================================================================
# DOWNLOAD (Heroku -> Railway)
# ==================================================================
@app.route("/mega/kocheng/download")
def download_kocheng():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename required"}), 400

    local_path = os.path.join(UPLOAD_DIR, filename)
    remote_path = f"/Kocheng_backup/{filename}"

    result = mega_get(remote_path, local_path)

    if result.returncode != 0:
        return jsonify({"error": "Mega get failed", "detail": result.stderr}), 500

    return send_file(local_path, as_attachment=True)
    
@app.route("/mega/skyforgia/download")
def download_skyforgia():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename required"}), 400

    local_path = os.path.join(UPLOAD_DIR, filename)
    remote_path = f"/Skyforgia_backup/{filename}"

    result = mega_get(remote_path, local_path)

    if result.returncode != 0:
        return jsonify({"error": "Mega get failed", "detail": result.stderr}), 500

    return send_file(local_path, as_attachment=True)


# ==================================================================
# CHECK FILE
# ==================================================================
@app.route("/mega/kocheng/check")
def check_kocheng():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename required"}), 400

    remote_path = f"/Kocheng_backup/{filename}"

    result = mega_check(remote_path)

    if result.returncode == 0:
        return jsonify({"has_backup": True, "filename": filename})

    return jsonify({"has_backup": False})
    
@app.route("/mega/skyforgia/check")
def check_skyforgia():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename required"}), 400

    remote_path = f"/Skyforgia_backup/{filename}"

    result = mega_check(remote_path)

    if result.returncode == 0:
        return jsonify({"has_backup": True, "filename": filename})

    return jsonify({"has_backup": False})


# ==================================================================
# RUN APP
# ==================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))