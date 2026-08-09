#!/usr/bin/env python3
"""
MCP Server stdio para Google Calendar.
Expone las herramientas: list_events, create_event, update_event, delete_event.
"""
import sys
import json
import os
from datetime import datetime, timedelta

# Simulación / Wrapper MCP para Antigravity CLI
def handle_tool_call(name, args):
    if name == "list_events":
        # Simula o consulta eventos en la agenda
        return {
            "status": "success",
            "events": [
                {"id": "evt_101", "summary": "Cita Médica de Rutina", "start": "16:00", "end": "16:45"},
                {"id": "evt_102", "summary": "Limpieza", "start": "17:00", "end": "17:30"}
            ]
        }
    elif name == "create_event":
        return {
            "status": "created",
            "event": {
                "id": f"evt_{int(datetime.now().timestamp())}",
                "summary": args.get("summary"),
                "start": args.get("start_time"),
                "end": args.get("end_time")
            }
        }
    elif name == "delete_event":
        return {"status": "deleted", "event_id": args.get("event_id")}
    elif name == "update_event":
        return {"status": "updated", "event_id": args.get("event_id"), "changes": args}
    else:
        return {"error": f"Herramienta desconocida: {name}"}

def main():
    # Loop de escucha stdio conforme al protocolo MCP
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            tool_name = request.get("tool")
            tool_args = request.get("arguments", {})
            result = handle_tool_call(tool_name, tool_args)
            response = {"id": request.get("id"), "result": result}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error MCP: {str(e)}\n")

if __name__ == "__main__":
    main()
