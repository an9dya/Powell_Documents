from flask import Flask, request, redirect
from supabase import create_client, Client
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURATION ---
SUPABASE_URL = "https://your-id.supabase.co"
SUPABASE_KEY = "your-anon-key"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/your-id/exec"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Simple HTML stored as a string to avoid 404 errors
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Powell Labs Repo</title></head>
<body style="font-family:sans-serif; padding:40px;">
    <h1>Powell Document Manager</h1>
    <form action="/upload" method="post" enctype="multipart/form-data" style="background:#eee; padding:20px;">
        <input type="text" name="doc_name" placeholder="Doc Name" required><br><br>
        <input type="date" name="expiry_date" required><br><br>
        <input type="email" name="email" placeholder="Reminder Email" required><br><br>
        <input type="file" name="file" required><br><br>
        <button type="submit">Upload & Track</button>
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        path = file.filename
        supabase.storage.from_("documents").upload(path, file.read())
        url = supabase.storage.from_("documents").get_public_url(path)
        supabase.table("document_repo").insert({
            "filename": request.form['doc_name'],
            "expiry_date": request.form['expiry_date'],
            "email": request.form['email'],
            "drive_link": url
        }).execute()
    return redirect('/')

@app.route('/api/cron')
def cron_job():
    today = datetime.now().date()
    limit = (today + timedelta(days=30)).isoformat()
    res = supabase.table("document_repo").select("*").lte("expiry_date", limit).execute()
    for doc in res.data:
        requests.post(GOOGLE_SCRIPT_URL, json={"email":doc['email'], "filename":doc['filename'], "date":doc['expiry_date']})
    return "Check Done", 200

app = app