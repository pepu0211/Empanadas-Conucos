import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from bot import responder, registrar_resena, marcar_esperando_resena, TIEMPO_RESENA

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RUTA_MENU = os.path.join(os.path.dirname(__file__), "assets", "menu.jpg")


async def _procesar(update: Update, context: ContextTypes.DEFAULT_TYPE, texto: str):
    chat_id = update.effective_chat.id
    resultado = responder(chat_id, texto)

    if resultado is None:
        return

    if resultado["texto"]:
        await update.message.reply_text(resultado["texto"])

    if resultado["enviar_menu"]:
        with open(RUTA_MENU, "rb") as foto:
            await update.message.reply_photo(foto)

    if resultado["cliente"]:
        context.job_queue.run_once(
            enviar_encuesta,
            when=TIEMPO_RESENA,
            chat_id=chat_id,
            data=resultado["cliente"],
        )


async def enviar_encuesta(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    nombre = context.job.data["nombre"]
    telefono = context.job.data["telefono"]

    marcar_esperando_resena(chat_id, nombre, telefono)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"¡Hola {nombre}! ¿Cómo te fue con tu pedido? Cualquier comentario, sugerencia o queja nos ayuda mucho 🙂",
    )


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _procesar(update, context, "Hola")


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto = update.message.text

    confirmacion_resena = registrar_resena(chat_id, texto)
    if confirmacion_resena:
        await update.message.reply_text(confirmacion_resena)
        return

    await _procesar(update, context, texto)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    print("Bot de Empanadas Conucos corriendo (polling). Ctrl+C para detener.")
    app.run_polling()


if __name__ == "__main__":
    main()
