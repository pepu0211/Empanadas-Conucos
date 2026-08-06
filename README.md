# Empanadas Conucos — Chatbot y página web de pedidos

Proyecto de chatbot con IA y página web de pedidos para **Empanadas Conucos**, una empanadería con varias sedes en Bucaramanga, Colombia.

## Qué incluye

**Bot de Telegram** (`telegram_bot.py` + `bot.py`)
- Toma pedidos de forma conversacional usando la API de Gemini: recolecta el pedido, nombre, teléfono, dirección y método de pago.
- Envía el menú como foto cuando el cliente lo pide, y responde preguntas sobre ingredientes.
- Nunca cotiza el valor del domicilio ni confirma el pedido en firme — eso lo hace un empleado.
- Se "apaga" automáticamente cuando el pedido queda completo o el cliente pide hablar con una persona, y se reactiva con frases como "nuevo pedido" o pasadas 2 horas.
- Una hora después de un pedido completo, le pregunta al cliente cómo le fue y guarda la respuesta en `resenas.txt`.

**Página web** (`app.py` + `templates/index.html`)
- Detecta la ubicación del cliente (o la deja elegir manualmente) y calcula la sede más cercana.
- Si la sede no tiene WhatsApp, ofrece un botón para llamar directamente.
- Si la sede sí tiene WhatsApp, habilita un carrito con el menú completo y, al finalizar, arma un mensaje de WhatsApp precargado con el pedido y los datos del cliente.

## Stack

- Python, Flask
- [Google Gemini API](https://ai.google.dev/) (`google-genai`) para el bot
- `python-telegram-bot` (con `JobQueue`/APScheduler para el seguimiento post-pedido)
- HTML/CSS/JS sin frameworks para el front

## Instalación

```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz con:

```
GEMINI_API_KEY=tu_api_key_de_google_ai_studio
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
```

## Uso

```bash
python telegram_bot.py   # corre el bot de Telegram
python app.py             # corre la página web en http://localhost:5000
```

## Estructura

```
datos.py          # menú, precios, sedes y horario del negocio
bot.py             # lógica conversacional del bot (Gemini)
telegram_bot.py     # integración con Telegram
app.py              # servidor web + generación del catálogo para el carrito
templates/index.html # página web (carrito, geolocalización, checkout)
static/             # logo y foto de portada
assets/menu.jpg      # foto del menú que envía el bot
```

## Estado

WhatsApp (el canal real que usan los negocios en Colombia) está planeado pero no integrado todavía — se usa Telegram como canal de pruebas mientras se resuelven trámites de verificación de negocio con Meta/Twilio.
