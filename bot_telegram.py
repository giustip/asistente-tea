from dotenv import load_dotenv
import os
import sys
import json
import asyncio
import subprocess
import logging
import shlex
import re
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from google import genai
import edge_tts

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Gestión persistente del nombre del asistente
NAME_FILE = "assistant_name.txt"

def get_assistant_name() -> str:
    if os.path.exists(NAME_FILE):
        with open(NAME_FILE, "r") as f:
            return f.read().strip() or "Catalina"
    return "Catalina"

def set_assistant_name(new_name: str):
    with open(NAME_FILE, "w") as f:
        f.write(new_name)

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
            elif hours_left < 24:
                return f"\n\n⚠️ **Recordatorio OAuth:** La sesión de Google expira en {int(hours_left)} horas."
    except Exception as e:
        logger.warning(f"Error verificando OAuth: {e}")
    return ""

async def execute_agy_prompt(user_prompt: str) -> str:
    current_name = get_assistant_name()
    
    # Detección de cambio de nombre
    match_name = re.search(r'(?:ahora te llamas|tu nombre es|llámate|quiero que te llames|puedo llamarte)\s+([A-Za-zÁéíóúÁÉÍÓÚñÑ]+)', user_prompt, re.IGNORECASE)
    if match_name:
        current_name = match_name.group(1).capitalize()
        set_assistant_name(current_name)

    try:
        contextualized_prompt = f"[Contexto de Sistema: Tu nombre asignado por la familia es '{current_name}'. Eres únicamente el Asistente Familiar TEA. PROHIBIDO ofrecer videojuegos o temas de código.] Usuario dice: {user_prompt}"
        safe_prompt = shlex.quote(contextualized_prompt)
        cmd = f"echo {safe_prompt} | agy run --config agy.config.json"
        
        process = await asyncio.create_subprocess_exec(
            "bash", "-c", cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=40.0)
        
        output = stdout.decode("utf-8").strip()
        error_output = stderr.decode("utf-8").strip()

        base_response = output or error_output or f"Soy {current_name}. ¿En qué te ayudo?"
        oauth_warning = check_oauth_expiration_warning()
        return base_response + oauth_warning

    except asyncio.TimeoutError:
        logger.error("agy CLI superó el tiempo límite.")
        return "⏱️ Tardé un poco más de lo esperado en procesar la consulta."
    except Exception as e:
        logger.error(f"Error ejecutando agy CLI: {str(e)}")
        return f"Error ejecutando agy CLI: {str(e)}"

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
        print("\n[Telegram] 🎙️ Transcribiendo audio con gemini-3.6-flash...")
        status_msg = await update.message.reply_text("🎙️ Transcribiendo audio...")
        file_obj = await (update.message.voice or update.message.audio).get_file()
        voice_path = f"temp_{update.message.message_id}.ogg"
        await file_obj.download_to_drive(voice_path)

        try:
            uploaded_file = ai_client.files.upload(file=voice_path)
            gemini_response = ai_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[uploaded_file, "Transcribe exactamente el contenido de este audio en español."]
            )
            user_input_text = gemini_response.text.strip()
            print(f"[Transcripción Gemini 3.6 Flash]: {user_input_text}")
        except Exception as e:
            logger.error(f"Error procesando audio en Gemini: {e}")
            await status_msg.edit_text("❌ Error al procesar la nota de voz.")
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
    agent_response = await execute_agy_prompt(user_input_text)
    await processing_msg.delete()

    current_name = get_assistant_name()  # Recargar por si cambió durante la ejecución

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
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.TEXT, handle_voice_or_text))
    print(f"🤖 Bot iniciado (Nombre activo: {get_assistant_name()})...")
    app.run_polling()

if __name__ == "__main__":
    main()
