#!/usr/bin/env python3
"""
Ejecutar UNA SOLA VEZ para autorizar acceso a Google Calendar.
Genera token.json reutilizable por el MCP del Asistente TEA.

Uso:
    cd /home/yoste/Documents/asistente-tea
    source venv/bin/activate
    python3 tools/authorize_calendar.py
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES     = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = Path(__file__).parent.parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent.parent / "token.json"

flow  = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
creds = flow.run_local_server(port=0)

TOKEN_FILE.write_text(creds.to_json())
print(f"✅ token.json generado en: {TOKEN_FILE}")
print("El Asistente TEA ya puede acceder a Google Calendar de forma desatendida.")
