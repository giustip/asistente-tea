# Asistente Familiar TEA 🧩 | ASD Family Assistant

* Espacios de lectura / Table of Contents:
* [Español 🇪🇸](https://www.google.com/search?q=%23espa%C3%B1ol)
* [English 🇬🇧](https://www.google.com/search?q=%23english)



---

## 🇪🇸 Español

### Descripción del Proyecto

El **Asistente Familiar TEA** es un sistema agéntico desarrollado sobre **Antigravity (`agy CLI`)** y alimentado por **Gemini 3.6 Flash** a través del SDK de Google GenAI. Diseñado específicamente para familias con integrantes dentro del Espectro Autista (TEA), el asistente actúa como un orquestador de rutinas cotidianas, mediador cognitivo y soporte de autorregulación sensorial en tiempo real.

El sistema interactúa de forma bidireccional mediante voz y texto a través de **Telegram**, ejecutando decisiones agénticas autónomas sobre la agenda de **Google Calendar** (vía protocolo MCP) y sintetizando respuestas habladas mediante **edge-tts**.

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
   [ bot_telegram.py (Python) ] ── (Auditoría OAuth token.json)
               │
      ┌────────┴────────────────────────┐
      │                                 │ (Audio .ogg)
      ▼                                 ▼
[ agy CLI Engine ]             [ Google GenAI SDK ]
 (gemini-3.6-flash)             (gemini-3.6-flash STT)
      │                                 │
      ├── .agents/skills/               └──────► Transcripción a texto
      └── MCP Google Calendar
               │
               ▼
   [ Respuesta Formateada ] ──► [ edge-tts Cloud ] ──► [ Salida Telegram (Audio + Texto) ]

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
pip install python-telegram-bot google-genai edge-tts python-dotenv

```


4. **Configurar el archivo de variables de entorno (`.env`):**
Crea un archivo `.env` en la raíz del proyecto:
```env
TELEGRAM_BOT_TOKEN="tu_token_de_telegram_aqui"
GEMINI_API_KEY="tu_clave_api_gemini_aqui"
GOOGLE_APPLICATION_CREDENTIALS="credentials.json"

```


5. **Configurar Google Cloud y autorizar Google Calendar (MCP):**

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
   Se abrirá el navegador → inicia sesión con tu cuenta de Gmail → acepta los permisos de Google Calendar → se genera el archivo `token.json` localmente. A partir de ahí el sistema funciona de forma desatendida y renueva el token automáticamente.

---

### Estructura del Proyecto

```text
asistente-tea/
├── .agents/
│   ├── mcp_config.json          # Configuración del servidor MCP de Google Calendar
│   └── skills/                   # Skills agénticas avanzadas
│       ├── decodificador-pragmatico/
│       ├── regulacion-pantallas/
│       ├── alternativas-sin-pantalla/
│       └── protocolo-sos/
├── knowledge/                    # Bases de conocimiento en Markdown
│   ├── pantallas_y_rutinas.md
│   ├── nutricion_sgsc.md
│   ├── protocolo_sos.md
│   └── decodificador_pragmatico.md
├── tools/
│   ├── google_calendar_mcp.py    # Servidor MCP stdio — Google Calendar API v3 (real)
│   └── authorize_calendar.py     # Script de autorización OAuth2 (ejecutar una sola vez)
├── assistant_name.txt            # Persistencia de identidad del agente
├── agy.config.json               # Configuración principal de agy CLI
├── requirements.txt              # Dependencias de Python (Google Calendar API)
├── system_prompt.md              # Instrucciones maestras del agente
├── bot_telegram.py               # Script ejecutable principal
└── .env                          # Variables de entorno secretas

```

---

### Modo de Uso

1. **Iniciar el Bot:**
```bash
source venv/bin/activate
python bot_telegram.py

```


2. **Ejemplos de Interacción en Telegram:**
* **Decodificación Pragmática & Pantallas:** Envia una nota de voz o texto diciendo:
> *"Un compañero en la escuela me dijo '¡Qué rápido eres!' cuando llegué de último en la carrera. Además, organízame 2 horas de tablet a las 17:00."*


* **Ocio Offline:** Envía el mensaje:
> *"Estoy aburrido, ¿qué podemos jugar?"*


* **Alerta SOS:** Envía una nota de voz o texto reportando crisis:
> *"agy, el niño está teniendo un meltdown muy fuerte en este momento, tiró la tablet y hay mucho llanto."*





---

---

## 🇬🇧 English

### Project Overview

The **ASD Family Assistant** is an agentic framework built on top of **Antigravity (`agy CLI`)** and powered by **Gemini 3.6 Flash** via the Google GenAI SDK. Tailored specifically for families with members on the Autism Spectrum Disorder (ASD), the assistant operates as a daily routine orchestrator, cognitive mediator, and real-time sensory self-regulation support tool.

The system interacts bidirectionally using voice and text through **Telegram**, executing autonomous agentic decisions on **Google Calendar** (via the MCP protocol) and synthesizing spoken responses via **edge-tts**.

### Key Features

* 🧠 **Pragmatic & Social Decoder:** Translates metaphors, sarcasm, and irony that the user fails to understand in school or social environments, explaining real intentions and suggesting assertive responses.
* 📱 **Age-Based Agentic Screen Control:** Autonomously limits recreational screen time (max 40-45 min for a 7-year-old) and automatically schedules a *Transition Alert (5 min left)* event in Google Calendar to prevent melt-downs due to abrupt transitions.
* 🎨 **Offline Play (Zero Digital):** When boredom is reported, it blocks all digital/video game suggestions and deploys real-world alternatives (narrative role-playing, arts and crafts, motor games, and interactive storytelling).
* 🚨 **SOS Self-Regulation Protocol:** Detects meltdown states or sensory overload, immediately clears afternoon cognitive tasks/screens from Google Calendar, blocks 2 hours of environmental decompression, and guides caregivers in a slow, calming voice.
* 🥗 **GFCF Nutritional Filter:** Recommends meal plans while strictly excluding gluten, casein/dairy, and artificial food dyes (Tartrazine, Red 40).
* 👤 **Persistent Identity Memory:** Consistently maintains the family-assigned name (e.g., *Catalina*) across system restarts via local storage.

---

### System Architecture

```text
[ Telegram Client (Audio/Text) ]
               │
               ▼
   [ bot_telegram.py (Python) ] ── (OAuth token.json Audit)
               │
      ┌────────┴────────────────────────┐
      │                                 │ (.ogg Audio)
      ▼                                 ▼
[ agy CLI Engine ]             [ Google GenAI SDK ]
 (gemini-3.6-flash)             (gemini-3.6-flash STT)
      │                                 │
      ├── .agents/skills/               └──────► Speech-to-Text
      └── MCP Google Calendar
               │
               ▼
   [ Formatted Response ] ──► [ edge-tts Cloud ] ──► [ Telegram Output (Audio + Text) ]

```

---

### Prerequisites

* Operating System: Linux (tested on Debian Trixie / Ubuntu), macOS, or WSL2 on Windows.
* Python 3.10+ and `python3-venv`.
* Antigravity CLI (`agy`) installed globally.
* A Telegram Account and a Bot created via [@BotFather](https://www.google.com/search?q=https://t.me/BotFather).
* Google AI Studio / Google AI Pro API Key (`GEMINI_API_KEY`).
* Google Cloud OAuth 2.0 Credentials for Google Calendar MCP Server (`credentials.json`).

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
pip install python-telegram-bot google-genai edge-tts python-dotenv

```


4. **Configure Environment Variables (`.env`):**
Create a `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
GEMINI_API_KEY="your_gemini_api_key_here"
GOOGLE_APPLICATION_CREDENTIALS="credentials.json"

```


5. **Configure Google Cloud and authorize Google Calendar (MCP):**

   **5a. Create OAuth credentials in Google Cloud Console:**
   - Go to [console.cloud.google.com](https://console.cloud.google.com) and create or select a project.
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
│   ├── google_calendar_mcp.py    # Stdio MCP server — Google Calendar API v3 (live)
│   └── authorize_calendar.py     # One-time OAuth2 authorization script
├── assistant_name.txt            # Persistent agent identity storage
├── agy.config.json               # Main agy CLI configuration
├── requirements.txt              # Python dependencies (Google Calendar API)
├── system_prompt.md              # Master system prompt
├── bot_telegram.py               # Executable entry point
└── .env                          # Secret environment variables

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
