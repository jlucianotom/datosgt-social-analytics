import http.server
import os
import secrets
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / "config" / ".env"
load_dotenv(ENV_PATH)

PORT = 8921
REDIRECT_URI = f"http://localhost:{PORT}/callback"
SCOPES = "user.info.basic,video.list"
STATE = secrets.token_urlsafe(16)

_result = {}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if params.get("state", [None])[0] != STATE:
            self.wfile.write("<h1>Estado invalido. Cierra esta ventana e intenta de nuevo.</h1>".encode())
            return

        if "code" in params:
            _result["code"] = params["code"][0]
            self.wfile.write("<h1>Listo. Ya puedes cerrar esta ventana y volver a la terminal.</h1>".encode())
        else:
            _result["error"] = params.get("error_description", ["desconocido"])[0]
            self.wfile.write(f"<h1>Error: {_result['error']}</h1>".encode())

    def log_message(self, *args):
        pass


def main():
    client_key = os.environ["TIKTOK_CLIENT_KEY"]
    client_secret = os.environ["TIKTOK_CLIENT_SECRET"]

    auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": client_key,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": STATE,
    })

    print("Abriendo el navegador para que autorices la app en TikTok...")
    print(f"Si no se abre solo, entra manualmente a:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = http.server.HTTPServer(("localhost", PORT), CallbackHandler)
    print(f"Esperando la autorizacion en {REDIRECT_URI} ...")
    while "code" not in _result and "error" not in _result:
        server.handle_request()

    if "error" in _result:
        raise SystemExit(f"TikTok devolvio un error: {_result['error']}")

    token_resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": _result["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )
    token_resp.raise_for_status()
    payload = token_resp.json()

    set_key(str(ENV_PATH), "TIKTOK_ACCESS_TOKEN", payload["access_token"])
    set_key(str(ENV_PATH), "TIKTOK_OPEN_ID", payload["open_id"])

    print("Token guardado en config/.env correctamente.")
    print(f"Vence en {payload.get('expires_in')} segundos. Refresh token guardado por separado si lo necesitas:")
    print(payload.get("refresh_token"))


if __name__ == "__main__":
    main()
