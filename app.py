import os
import subprocess
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
def mega_put_kocheng(local, remote="/Kocheng_backup/"):
    return subprocess.run(
        ["mega-put", local, remote],
        capture_output=True, text=True
    )
    
def mega_put_skyforgia(local, remote="/Skyforgia_backup/"):
    return subprocess.run(
        ["mega-put", local, remote],
        capture_output=True, text=True
    )

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

    if result.returncode != 0:
        return jsonify({"error": "Mega upload failed", "detail": result.stderr}), 500

    return jsonify({"message": "Uploaded to MEGA", "filename": filename})
    
@app.route("/mega/skyforgia/upload", methods=["POST"])
def upload_skyforgia():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename
    local_path = os.path.join(UPLOAD_DIR, filename)
    file.save(local_path)

    result = mega_put_skyforgia(local_path)

    if result.returncode != 0:
        return jsonify({"error": "Mega upload failed", "detail": result.stderr}), 500

    return jsonify({"message": "Uploaded to MEGA", "filename": filename})


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