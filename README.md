# Asistente Familiar TEA 🧩 | ASD Family Assistant

* Espacios de lectura / Table of Contents:
* [Español 🇪🇸](https://www.google.com/search?q=%23espa%C3%B1ol)
* [English 🇬🇧](https://www.google.com/search?q=%23english)



---

## 🇪🇸 Español

### Descripción del Proyecto

El **Asistente Familiar TEA** es un sistema agéntico desarrollado en Python y alimentado por **Gemini 3.6 Flash (con razonamiento extendido)** a través del **Antigravity Python SDK (`google-antigravity`)**. Diseñado específicamente para familias con integrantes dentro del Espectro Autista (TEA), el asistente actúa como un orquestador de rutinas cotidianas, mediador cognitivo y soporte de autorregulación sensorial en tiempo real.

El sistema interactúa de forma bidireccional mediante voz y texto a través de **Telegram**, ejecutando decisiones agénticas autónomas sobre la agenda de **Google Calendar** (integración directa con la API v3) y sintetizando respuestas habladas mediante **edge-tts**.

### Características Principales

* 🧠 **Decodificador Pragmático y Social:** Traduce metáforas, sarcasmos e ironías que el usuario no comprende en entornos escolares o sociales, explicando la intención real y sugiriendo respuestas asertivas.
* 📱 **Regulación Agéntica de Pantallas por Edad:** Acota de forma autónoma el tiempo recreativo de pantallas (máx. 40-45 min para 7 años) e inserta automáticamente un evento de *Aviso de Transición (Faltan 5 min)* en Google Calendar para prevenir colapsos por cambio brusco de actividad.
* 🎨 **Ocio Offline (Cero Digital):** Ante reportes de aburrimiento, bloquea sugerencias de videojuegos o navegación web y despliega alternativas del mundo real (juegos de rol narrativos, manualidades plásticas, juegos motores y cuentos participativos).
* 🚨 **Protocolo SOS de Autorregulación:** Detecta estados de crisis (*meltdowns*) o sobrecarga sensorial, despeja inmediatamente tareas cognitivas/pantallas de la tarde en Google Calendar, bloquea 2 horas de descompresión ambiental y guía a los cuidadores con voz pausada.
* 🥗 **Filtro Nutricional SGSC:** Recomienda menús excluyendo estrictamente gluten, lácteos/caseína y colorantes artificiales (Tartrazina, Rojo 40).
* 👤 **Memoria de Identidad Persistente:** Mantiene de forma consistente el nombre asignado por la familia (ej. *Catalina*) entre reinicios del sistema mediante almacenamiento local.

---

### Arquitectura del Sistema

```text
[ Telegram Client (Audio/Texto) ]
               │
               ▼
   [ bot_telegram.py (Python) ] ──► (Lee knowledge/*.md + memory.md)
      │         │         │
      │         │         └── calendar_client.py ──► Google Calendar API v3
      │         │
      │         └── (Audio .ogg) ──► Google GenAI SDK (STT) ──► Transcripción
      │
      ▼
[ Antigravity Python SDK ]
 (gemini-3.6-flash via OAuth)
      │
      ▼
   [ Respuesta + [📅 OP] + [🧠 MEMORIA] ] ──► bot parsea ops ──► Calendar / memory.md
      │
      ▼
   [ edge-tts Cloud ] ──► [ Salida Telegram (Audio + Texto) ]

```

---

### Requisitos Previos

* Sistema Operativo: Linux (probado en Debian Trixie / Ubuntu), macOS o WSL2 en Windows.
* Python 3.10 o superior y el paquete `python3-venv`.
* Antigravity CLI (`agy`) instalado globalmente.
* Cuenta de Telegram y un Bot creado con [@BotFather](https://www.google.com/search?q=https://t.me/BotFather).
* Clave de API de Google AI Studio / Google AI Pro (`GEMINI_API_KEY`).
* Credenciales de Google Cloud OAuth 2.0 para el servidor MCP de Google Calendar (`credentials.json`).

---

### Instalación Paso a Paso

1. **Clonar el repositorio:**
```bash
git clone https://github.com/giustip/asistente-tea.git
cd asistente-tea

```


2. **Crear y activar el entorno virtual (PEP 668 compliant):**
```bash
python3 -m venv venv
source venv/bin/activate

```


3. **Instalar dependencias de Python:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install python-telegram-bot google-genai edge-tts python-dotenv google-antigravity

```


4. **Configurar el archivo de variables de entorno (`.env`):**
Crea un archivo `.env` en la raíz del proyecto:
```env
TELEGRAM_BOT_TOKEN="tu_token_de_telegram_aqui"
GEMINI_API_KEY="tu_clave_api_gemini_aqui"
GOOGLE_APPLICATION_CREDENTIALS="credentials.json"
GOOGLE_CALENDAR_EMAIL="tu_correo@gmail.com"

```


5. **Configurar Google Cloud y autorizar Google Calendar:**

   **5a. Crear credenciales OAuth en Google Cloud Console:**
   - Ir a [console.cloud.google.com](https://console.cloud.google.com) y crear o seleccionar un proyecto.
   - Habilitar la **Google Calendar API**: APIs y servicios → Biblioteca → buscar "Google Calendar API" → Habilitar.
   - Crear credenciales: APIs y servicios → Credenciales → Crear credenciales → **ID de cliente OAuth 2.0** → Tipo: **Aplicación de escritorio**.
   - Descargar el JSON y renombrarlo como `credentials.json` en la raíz del proyecto.

   **5b. Agregar tu cuenta como usuario de prueba:**
   - En Google Cloud Console → APIs y servicios → **Pantalla de consentimiento de OAuth**.
   - Sección **"Usuarios de prueba"** → **+ Agregar usuarios** → introducir tu cuenta de Gmail → Guardar.

   > ⚠️ **Importante:** Si omites este paso, recibirás el error `403: access_denied` al intentar autorizar.

   **5c. Ejecutar la autorización inicial (una sola vez):**
   ```bash
   source venv/bin/activate
   python3 tools/authorize_calendar.py
   ```
   Se abrirá el navegador → inicia sesión con tu cuenta de Gmail → acepta los permisos de Google Calendar → se genera el archivo `token.json` localmente.

---

### Estructura del Proyecto

```text
asistente-tea/
├── .agents/
│   ├── mcp_config.json
│   └── skills/
├── knowledge/
├── tools/
│   ├── calendar_client.py        # Módulo central de interacción con Calendar
│   ├── google_calendar_mcp.py
│   └── authorize_calendar.py
├── assistant_name.txt
├── memory.md                     # Memoria persistente a largo plazo
├── agy.config.json
├── requirements.txt
├── system_prompt.md
├── bot_telegram.py
└── .env

```

---

### Modo de Uso

1. **Iniciar el Bot:**
```bash
source venv/bin/activate
python bot_telegram.py

```


2. **Ejemplos de Interacción en Telegram:**
* **Decodificación & Pantallas:** *"Un compañero dijo '¡Qué rápido eres!' cuando llegué de último. Además, organízame 2 horas de tablet a las 17:00."*
* **Ocio Offline:** *"Estoy aburrido, ¿qué podemos jugar?"*
* **Alerta SOS:** *"agy, el niño está teniendo un meltdown muy fuerte en este momento."*





---

---

## 🇬🇧 English

### Project Overview

The **ASD Family Assistant** is an agentic system built in Python and powered by **Gemini 3.6 Flash (with extended reasoning)** via the **Antigravity Python SDK (`google-antigravity`)**. Specifically designed for families with members on the Autism Spectrum (ASD), it acts as a daily routine orchestrator, cognitive mediator, and real-time sensory self-regulation support.

The system interacts bidirectionally via **Telegram**, using **Gemini 3.6 Flash** for agentic decision-making, while executing operations on **Google Calendar** via a dedicated client and synthesizing speech with **edge-tts**.

### Key Features

* 🧠 **Pragmatic & Social Decoder:** Translates metaphors and sarcasm, explaining real intent and suggesting assertive responses.
* 📱 **Agentic Screen Control:** Limits recreational time and manages transition alerts in Google Calendar to prevent meltdowns.
* 🎨 **Offline Play (Zero Digital):** Replaces digital suggestions with real-world alternatives when boredom is reported.
* 🚨 **SOS Self-Regulation Protocol:** Detects crises, clears cognitive tasks from the agenda, blocks decompression time, and guides caregivers.
* 🥗 **GFCF Nutritional Filter:** Recommends meal plans excluding gluten, dairy, and artificial dyes.
* 👤 **Persistent Identity Memory:** Maintains the user's name (e.g., *Catalina*) via local storage.

---

### System Architecture

```text
[ Telegram Client (Audio/Text) ]
               │
               ▼
   [ bot_telegram.py (Python) ] ──► (Reads knowledge/*.md + memory.md)
      │         │         │
      │         │         └── calendar_client.py ──► Google Calendar API v3
      │         │
      │         └── (Audio .ogg) ──► Google GenAI SDK (STT) ──► Transcription
      │
      ▼
[ Antigravity Python SDK ]
 (gemini-3.6-flash via OAuth)
      │
      ▼
   [ Response + [📅 OP] + [🧠 MEMORIA] ] ──► bot parses ops ──► Calendar / memory.md
      │
      ▼
   [ edge-tts Cloud ] ──► [ Telegram Output (Audio + Text) ]

```

---

### Prerequisites

* OS: Linux, macOS, or WSL2.
* Python 3.10+.
* Antigravity CLI (`agy`) installed.
* Telegram Account and Bot created via [@BotFather](https://www.google.com/search?q=https://t.me/BotFather).
* Google AI Studio API Key (`GEMINI_API_KEY`).
* Google Cloud OAuth 2.0 Credentials (`credentials.json`).

---

### Step-by-Step Installation

1. **Clone the repository:**
```bash
git clone https://github.com/giustip/asistente-tea.git
cd asistente-tea

```


2. **Create and activate virtual environment (PEP 668 compliant):**
```bash
python3 -m venv venv
source venv/bin/activate

```


3. **Install Python dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install python-telegram-bot google-genai edge-tts python-dotenv google-antigravity

```


4. **Configure Environment Variables (`.env`):**
Create a `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
GEMINI_API_KEY="your_gemini_api_key_here"
GOOGLE_APPLICATION_CREDENTIALS="credentials.json"
GOOGLE_CALENDAR_EMAIL="your_email@gmail.com"

```


5. **Configure Google Cloud and authorize Google Calendar:**

   **5a. Create OAuth credentials in Google Cloud Console:**
   - Enable the **Google Calendar API**: APIs & Services → Library → search "Google Calendar API" → Enable.
   - Create credentials: APIs & Services → Credentials → Create Credentials → **OAuth 2.0 Client ID** → Application type: **Desktop app**.
   - Download the JSON and rename it to `credentials.json` in the project root.

   **5b. Add your account as a test user:**
   - In Google Cloud Console → APIs & Services → **OAuth consent screen**.
   - Under **"Test users"** → **+ Add Users** → enter your Gmail account → Save.

   > ⚠️ **Important:** Skipping this step will result in a `403: access_denied` error during authorization.

   **5c. Run the one-time authorization (run once only):**
   ```bash
   source venv/bin/activate
   python3 tools/authorize_calendar.py
   ```
   A browser window will open → sign in with your Gmail account → grant Google Calendar permissions → `token.json` is generated locally. From this point, the system works autonomously and refreshes the token automatically.

---

### Project Structure

```text
asistente-tea/
├── .agents/
│   ├── mcp_config.json          # Google Calendar MCP server configuration
│   └── skills/                   # Advanced agentic skills
│       ├── decodificador-pragmatico/
│       ├── regulacion-pantallas/
│       ├── alternativas-sin-pantalla/
│       └── protocolo-sos/
├── knowledge/                    # Markdown knowledge base
│   ├── pantallas_y_rutinas.md
│   ├── nutricion_sgsc.md
│   ├── protocolo_sos.md
│   └── decodificador_pragmatico.md
├── tools/
│   ├── calendar_client.py        # Direct Google Calendar API v3 client (used by the bot)
│   ├── google_calendar_mcp.py    # Stdio MCP server (for interactive agy usage)
│   └── authorize_calendar.py     # One-time OAuth2 authorization script
├── assistant_name.txt            # Persistent agent identity storage
├── memory.md                     # Long-term persistent memory
├── agy.config.json               # Main agy CLI configuration
├── requirements.txt              # Python dependencies (Google Calendar API)
├── system_prompt.md              # Master system prompt
├── bot_telegram.py               # Executable entry point
└── .env                          # Secret environment variables (includes GOOGLE_CALENDAR_EMAIL)

```

---

### Usage

1. **Run the Bot:**
```bash
source venv/bin/activate
python bot_telegram.py

```


2. **Telegram Interaction Examples:**
* **Pragmatic Decoding & Screen Control:** Send a voice note or text:
> *"A classmate at school told me 'Oh, you are so fast!' when I finished last in the race. Also, schedule 2 hours of tablet time at 17:00."*


* **Offline Play:** Send the text message:
> *"I'm bored, what can we play?"*


* **SOS Alert:** Send a voice note or text reporting a crisis:
> *"agy, the child is having a severe meltdown right now, threw the tablet, and is crying hysterically."*





---

### License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
