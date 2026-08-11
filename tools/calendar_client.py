#!/usr/bin/env python3
"""
Cliente directo de Google Calendar API v3 para bot_telegram.py.
Usado cuando agy run no puede cargar el MCP en modo headless (Jetski bloquea
el permiso 'command' necesario para iniciar subprocesos MCP).
"""
import os
import json
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

BASE_DIR   = Path(__file__).parent.parent
TOKEN_FILE = BASE_DIR / "token.json"
TIMEZONE   = "America/Caracas"


def _get_service():
    """Obtiene el servicio autenticado de Google Calendar. Auto-renueva el token."""
    creds_file = BASE_DIR / os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        else:
            raise RuntimeError(
                "token.json no existe o es inválido. "
                "Ejecuta tools/authorize_calendar.py para autorizarte."
            )

    return build("calendar", "v3", credentials=creds)


def _fmt_event(e: dict) -> dict:
    """Convierte un evento de la API al formato compacto usado en el contexto."""
    return {
        "id":      e["id"],
        "summary": e.get("summary", "(Sin título)"),
        "start":   e["start"].get("dateTime", e["start"].get("date", "")),
        "end":     e["end"].get("dateTime",   e["end"].get("date", "")),
        "desc":    e.get("description", ""),
        "location": e.get("location", ""),
    }


def _is_today(start_str: str) -> bool:
    """Determina si un evento es de hoy."""
    today = date.today()
    try:
        return datetime.fromisoformat(start_str).date() == today
    except (ValueError, TypeError):
        return start_str[:10] == today.isoformat() if start_str else False


def get_events(days: int = 7) -> dict:
    """
    Retorna {'events': [...próximos N días...], 'today': [...eventos de hoy...]}
    Muestra primero los 7 días y luego al final los de hoy.
    """
    svc  = _get_service()
    now  = datetime.now(timezone.utc)
    tmax = now + timedelta(days=days)

    result = svc.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=tmax.isoformat(),
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    all_events = [_fmt_event(e) for e in result.get("items", [])]
    today_events = [e for e in all_events if _is_today(e["start"])]

    return {"events": all_events, "today": today_events}


def create_event(summary: str, start_time: str, end_time: str,
                 description: str = "", location: str = "") -> dict:
    """Crea un evento en el calendario primario."""
    svc = _get_service()
    body = {
        "summary":     summary,
        "description": description,
        "location":    location,
        "start": {"dateTime": start_time, "timeZone": TIMEZONE},
        "end":   {"dateTime": end_time,   "timeZone": TIMEZONE},
    }
    ev = svc.events().insert(calendarId="primary", body=body).execute()
    return {"status": "created", "id": ev["id"], "summary": ev.get("summary", "")}


def delete_event(event_id: str) -> dict:
    """Elimina un evento por su ID."""
    _get_service().events().delete(calendarId="primary", eventId=event_id).execute()
    return {"status": "deleted", "event_id": event_id}


def update_event(event_id: str, **kwargs) -> dict:
    """
    Actualiza campos de un evento existente.
    kwargs puede incluir: summary, description, start_time, end_time, location
    """
    svc = _get_service()
    ev  = svc.events().get(calendarId="primary", eventId=event_id).execute()

    if "summary"     in kwargs: ev["summary"]     = kwargs["summary"]
    if "description" in kwargs: ev["description"] = kwargs["description"]
    if "location"    in kwargs: ev["location"]    = kwargs["location"]
    if "start_time"  in kwargs:
        ev["start"] = {"dateTime": kwargs["start_time"], "timeZone": TIMEZONE}
    if "end_time"    in kwargs:
        ev["end"]   = {"dateTime": kwargs["end_time"],   "timeZone": TIMEZONE}

    updated = svc.events().update(
        calendarId="primary", eventId=event_id, body=ev
    ).execute()
    return {"status": "updated", "event_id": updated["id"]}
