from dotenv import load_dotenv
import os
import sys
import json
import asyncio
import logging
import re
import glob
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
from google import genai
import edge_tts
from google.antigravity import Agent, LocalAgentConfig

# Integración directa de Google Calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from tools.calendar_client import get_events, create_event, delete_event, update_event
    CALENDAR_AVAILABLE = True
except ImportError as _cal_err:
    CALENDAR_AVAILABLE = False
    logging.warning(f"calendar_client no disponible: {_cal_err}")

# 1. Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CALENDAR_EMAIL = os.getenv("GOOGLE_CALENDAR_EMAIL", "tu_correo@gmail.com")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

NAME_FILE = "assistant_name.txt"
MEMORY_FILE = "memory.md"

def get_assistant_name() -> str:
    if os.path.exists(NAME_FILE):
        with open(NAME_FILE, "r") as f:
            name = f.read().strip()
            return name if name else "TEA ia"
    return "TEA ia"

def set_assistant_name(new_name: str):
    with open(NAME_FILE, "w") as f:
        f.write(new_name.strip())

def load_knowledge_base() -> str:
    kb_text = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Leer system prompt base
    sys_prompt_path = os.path.join(base_dir, "system_prompt.md")
    if os.path.exists(sys_prompt_path):
        with open(sys_prompt_path, "r", encoding="utf-8") as f:
            kb_text.append(f.read())
            
    # 2. Leer base de conocimiento
    knowledge_dir = os.path.join(base_dir, "knowledge")
    if os.path.exists(knowledge_dir):
        kb_text.append("\n\n--- BASE DE CONOCIMIENTO ---")
        for md_file in glob.glob(os.path.join(knowledge_dir, "*.md")):
            with open(md_file, "r", encoding="utf-8") as f:
                kb_text.append(f"\n# {os.path.basename(md_file)}\n")
                kb_text.append(f.read())
                
    # 3. Leer skills
    skills_dir = os.path.join(base_dir, ".agents", "skills")
    if os.path.exists(skills_dir):
        kb_text.append("\n\n--- SKILLS (Habilidades) ---")
        for md_file in glob.glob(os.path.join(skills_dir, "**", "SKILL.md"), recursive=True):
            with open(md_file, "r", encoding="utf-8") as f:
                skill_name = os.path.basename(os.path.dirname(md_file))
                kb_text.append(f"\n# Skill: {skill_name}\n")
                kb_text.append(f.read())
                
    return "\n".join(kb_text)

def check_oauth_expiration_warning() -> str:
    token_path = "token.json"
    if not os.path.exists(token_path):
        return ""
    try:
        with open(token_path, "r") as f:
            data = json.load(f)
        expiry_str = data.get("expiry")
        if expiry_str:
            expiry_dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_left = (expiry_dt - now).total_seconds() / 3600.0

            if hours_left <= 0:
                return "\n\n⚠️ **Alerta OAuth:** La sesión de Google OAuth ha expirado. Vuelve a autenticarte para renovar `token.json`."
            elif hours_left < 1:
                minutes_left = int(hours_left * 60)
                if minutes_left <= 5:
                    return f"\n\n⚠️ **Recordatorio OAuth:** La sesión de Google expira en {minutes_left} minutos."
    except Exception as e:
        logger.warning(f"Error verificando OAuth: {e}")
    return ""

async def execute_agent_prompt(user_prompt: str) -> str:
    current_name = get_assistant_name()
    
    match_name = re.search(
        r'(?:ahora te llamas|tu nombre es|llámate|quiero que te llames|puedo llamarte|te vas a llamar|llamarás|te llamaré)\s+([A-Za-z0-9ÁéíóúÁÉÍÓÚñÑ\s]{2,30}?)(?=[.,!?\n]|$)',
        user_prompt, re.IGNORECASE
    )
    if match_name:
        extracted_name = match_name.group(1).strip()
        if 1 <= len(extracted_name.split()) <= 4:
            current_name = extracted_name
            set_assistant_name(current_name)

    now_context = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")

    try:
        calendar_context = ""
        if CALENDAR_AVAILABLE:
            try:
                cal_data = get_events(days=7)
                n_events = len(cal_data['events'])
                n_today  = len(cal_data['today'])
                calendar_context = (
                    f"\n[Google Calendar {GOOGLE_CALENDAR_EMAIL} — {now_context}]\n"
                    f"Próximos 7 días ({n_events} eventos): "
                    + json.dumps(cal_data['events'], ensure_ascii=False)
                    + f" | HOY ({n_today} eventos): "
                    + json.dumps(cal_data['today'], ensure_ascii=False)
                    + ".\n"
                )
            except Exception as _cal_ex:
                calendar_context = f"\n[Google Calendar: no disponible — {_cal_ex}].\n"
                
        # Cargar memoria activa
        memory_context = ""
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory_content = f.read().strip()
                if memory_content:
                    memory_context = f"\n[Memoria Activa]\n{memory_content}\n"

        system_instruction = load_knowledge_base()
        
        contextualized_prompt = (
            f"[Contexto de Sistema: Tu nombre asignado es '{current_name}'. "
            f"Fecha y hora actual del sistema: {now_context}."
            f"{calendar_context}"
            f"{memory_context}"
            f" Eres el Asistente Familiar TEA. PROHIBIDO ofrecer videojuegos o código.]\n\n"
            f"Usuario dice: {user_prompt}"
        )

        logger.info("Enviando prompt a google-antigravity SDK (OAuth)...")
        config = LocalAgentConfig(
            system_instructions=system_instruction,
            model="gemini-3.6-pro"
        )
        async with Agent(config) as agent:
            response_stream = await agent.chat(contextualized_prompt)
            full_response = ""
            async for token in response_stream:
                full_response += token
                
        base_response = full_response.strip()
        if not base_response:
            base_response = f"Soy {current_name}. ¿En qué te ayudo?"

        base_response, _ = parse_and_execute_calendar_ops(base_response)
        base_response = parse_and_execute_memory_ops(base_response)
        oauth_warning = check_oauth_expiration_warning()
        return base_response + oauth_warning

    except Exception as e:
        logger.error(f"Error ejecutando Gemini API: {str(e)}")
        return f"Error ejecutando Gemini API: {str(e)}"

_CAL_OP_RE = re.compile(r'\[📅\s*(\w+)\s*:\s*(\{.*?\})\]', re.DOTALL)
_MEM_OP_RE = re.compile(r'\[🧠\s*MEMORIA\s*:\s*"(.*?)"\]', re.DOTALL | re.IGNORECASE)

def parse_and_execute_calendar_ops(response: str) -> tuple:
    ops_log = []
    if not CALENDAR_AVAILABLE:
        return response, ops_log

    def _run_op(match):
        op   = match.group(1).upper()
        raw  = match.group(2)
        try:
            args = json.loads(raw)
            if op == "CREAR_EVENTO":
                result = create_event(**args)
                ops_log.append(f"✅ Evento creado: {result.get('summary')}")
            elif op == "ELIMINAR_EVENTO":
                result = delete_event(args["event_id"])
                ops_log.append(f"🗑️ Evento eliminado: {args['event_id']}")
            elif op == "ACTUALIZAR_EVENTO":
                result = update_event(**args)
                ops_log.append(f"✏️ Evento actualizado: {args.get('event_id')}")
            else:
                ops_log.append(f"⚠️ Operación desconocida: {op}")
        except Exception as _e:
            ops_log.append(f"❌ Error en {op}: {_e}")
        return ""
        
    clean = _CAL_OP_RE.sub(_run_op, response).strip()
    if ops_log:
        logger.info(f"[Calendar ops] {ops_log}")
    return clean, ops_log

def parse_and_execute_memory_ops(response: str) -> str:
    def _save_memory(match):
        memory_text = match.group(1).strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(MEMORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"- [{timestamp}] {memory_text}\n")
            logger.info(f"[Memoria guardada]: {memory_text}")
        except Exception as e:
            logger.error(f"Error guardando memoria: {e}")
        return ""
        
    return _MEM_OP_RE.sub(_save_memory, response).strip()

async def text_to_speech(text_content: str, output_audio_path: str, is_sos: bool = False):
    voice = "es-ES-ElviraNeural"
    rate = "-15%" if is_sos else "+0%"
    communicate = edge_tts.Communicate(text_content, voice=voice, rate=rate)
    await communicate.save(output_audio_path)

async def handle_voice_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_input_text = ""
    current_name = get_assistant_name()

    if update.message.voice or update.message.audio:
        print("\n[Telegram] 🎙️ Transcribiendo audio con gemini-3.6-pro...")
        status_msg = await update.message.reply_text("🎙️ Transcribiendo audio...")
        voice_path = f"temp_{update.message.message_id}.ogg"

        try:
            file_obj = await (update.message.voice or update.message.audio).get_file(read_timeout=60.0)
            await file_obj.download_to_drive(voice_path, read_timeout=60.0)

            uploaded_file = ai_client.files.upload(file=voice_path)
            gemini_response = ai_client.models.generate_content(
                model="gemini-3.6-pro",
                contents=[uploaded_file, "Transcribe exactamente el contenido de este audio en español."]
            )
            user_input_text = gemini_response.text.strip()
            print(f"[Transcripción Gemini 3.6 Pro]: {user_input_text}")

        except Exception as e:
            logger.error(f"Error procesando/descargando audio en Telegram: {e}")
            await status_msg.edit_text("❌ Hubo un problema de conexión al descargar la nota de voz. Por favor, reenvíala.")
            if os.path.exists(voice_path):
                os.remove(voice_path)
            return
        finally:
            if os.path.exists(voice_path):
                os.remove(voice_path)
            await status_msg.delete()
    
    elif update.message.text:
        user_input_text = update.message.text.strip()
        print(f"\n[Telegram] 💬 Texto recibido: '{user_input_text}'")

    if not user_input_text:
        return

    processing_msg = await update.message.reply_text(f"⚙️ {current_name} evaluando contexto...")
    agent_response = await execute_agent_prompt(user_input_text)
    await processing_msg.delete()

    current_name = get_assistant_name()

    try:
        await update.message.reply_text(agent_response, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(agent_response)

    is_sos_alert = "Protocolo SOS" in agent_response or "meltdown" in user_input_text.lower()
    try:
        audio_out_path = f"response_{update.message.message_id}.ogg"
        await text_to_speech(agent_response, audio_out_path, is_sos=is_sos_alert)
        
        with open(audio_out_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file, caption=f"Voz de {current_name}")
        
        if os.path.exists(audio_out_path):
            os.remove(audio_out_path)
    except Exception as e:
        logger.error(f"Error en síntesis de voz: {e}")

def main():
    request_config = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=60.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request_config).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.TEXT, handle_voice_or_text))
    print(f"🤖 Bot iniciado (Motor GenAI Directo / Nombre activo: {get_assistant_name()})...")
    app.run_polling()

if __name__ == "__main__":
    main()
