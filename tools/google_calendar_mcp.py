#!/usr/bin/env python3
"""
MCP Server stdio para Google Calendar — API Real (v3).
Herramientas: list_events, create_event, update_event, delete_event.

list_events devuelve:
  - 'events': todos los eventos de los próximos N días (default: 7)
  - 'today':  subconjunto de 'events' correspondiente al día de hoy (al final)

Diseñado para el Asistente Familiar TEA — Rutas 2 y 4 del system_prompt.
"""
import sys, json, os
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES     = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR   = Path(__file__).parent.parent
CREDS_FILE = BASE_DIR / os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
TOKEN_FILE = BASE_DIR / "token.json"
TIMEZONE   = "America/Caracas"


def get_service():
    """Autenticar con OAuth2 y retornar el servicio de Calendar API v3."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def fmt_event(e: dict) -> dict:
    """Serializar un evento de la API al formato usado por el agente TEA."""
    return {
        "id":          e["id"],
        "summary":     e.get("summary", "(Sin título)"),
        "start":       e["start"].get("dateTime", e["start"].get("date")),
        "end":         e["end"].get("dateTime",   e["end"].get("date")),
        "description": e.get("description", ""),
        "location":    e.get("location", ""),
    }


def is_today(start_str: str) -> bool:
    """True si el evento inicia hoy (soporta dateTime y date-only)."""
    today = date.today()
    try:
        return datetime.fromisoformat(start_str).date() == today
    except ValueError:
        return start_str[:10] == today.isoformat()


def handle_tool_call(name: str, args: dict) -> dict:
    try:
        service = get_service()
    except Exception as e:
        return {"error": f"Autenticación fallida: {str(e)}"}

    # ── list_events ────────────────────────────────────────────────────────────
    if name == "list_events":
        days     = int(args.get("days", 7))
        now      = datetime.now(timezone.utc)
        time_max = now + timedelta(days=days)

        result = service.events().list(
            calendarId   = "primary",
            timeMin      = now.isoformat(),
            timeMax      = time_max.isoformat(),
            maxResults   = 50,
            singleEvents = True,
            orderBy      = "startTime",
        ).execute()

        all_events   = [fmt_event(e) for e in result.get("items", [])]
        today_events = [e for e in all_events if is_today(e["start"])]

        return {
            "status":     "success",
            "range_days": days,
            "events":     all_events,    # próximos 7 días
            "today":      today_events,  # solo hoy (al final)
        }

    # ── create_event ───────────────────────────────────────────────────────────
    elif name == "create_event":
        body = {
            "summary":     args.get("summary", "Nuevo Evento"),
            "description": args.get("description", ""),
            "location":    args.get("location", ""),
            "start":       {"dateTime": args["start_time"], "timeZone": TIMEZONE},
            "end":         {"dateTime": args["end_time"],   "timeZone": TIMEZONE},
        }
        created = service.events().insert(calendarId="primary", body=body).execute()
        return {
            "status": "created",
            "event":  {"id": created["id"], "summary": created.get("summary")},
        }

    # ── update_event ───────────────────────────────────────────────────────────
    elif name == "update_event":
        event_id = args["event_id"]
        ev = service.events().get(calendarId="primary", eventId=event_id).execute()
        if "summary"     in args: ev["summary"]     = args["summary"]
        if "description" in args: ev["description"] = args["description"]
        if "start_time"  in args: ev["start"] = {"dateTime": args["start_time"], "timeZone": TIMEZONE}
        if "end_time"    in args: ev["end"]   = {"dateTime": args["end_time"],   "timeZone": TIMEZONE}
        updated = service.events().update(
            calendarId="primary", eventId=event_id, body=ev
        ).execute()
        return {"status": "updated", "event_id": updated["id"]}

    # ── delete_event ───────────────────────────────────────────────────────────
    elif name == "delete_event":
        service.events().delete(calendarId="primary", eventId=args["event_id"]).execute()
        return {"status": "deleted", "event_id": args["event_id"]}

    else:
        return {"error": f"Herramienta desconocida: {name}"}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req    = json.loads(line)
            result = handle_tool_call(req.get("tool"), req.get("arguments", {}))
            sys.stdout.write(json.dumps({"id": req.get("id"), "result": result}) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error MCP: {str(e)}\n")


if __name__ == "__main__":
    main()
