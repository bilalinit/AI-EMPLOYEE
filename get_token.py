from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request, urllib.parse, json
from pathlib import Path
import os

# Load credentials from .env file
env_path = Path(__file__).parent / 'ai_employee_scripts' / '.env'

def load_env():
    """Load .env file manually."""
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ Error: LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set in .env")
    exit(1)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = parse_qs(urlparse(self.path).query).get('code', [None])[0]
        if code:
            data = urllib.parse.urlencode({
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': 'http://localhost:8000/callback'
            }).encode()
            try:
                res = urllib.request.urlopen('https://www.linkedin.com/oauth/v2/accessToken', data)
                token_data = json.loads(res.read().decode())
                print("\n" + "="*70)
                print("✅ ACCESS TOKEN RECEIVED!")
                print("="*70)
                print("\nCopy this token to your .env file as LINKEDIN_ACCESS_TOKEN:\n")
                print(token_data['access_token'])
                print("\n" + "="*70 + "\n")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Got the token! Check your terminal.")
            except Exception as e:
                print("Error:", e)
    def log_message(self, *args): pass

print("Waiting for LinkedIn... Open the URL in your browser now.")
HTTPServer(('', 8000), Handler).handle_request()