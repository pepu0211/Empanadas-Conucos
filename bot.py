import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from google import genai
from google.genai import types

from datos import empanadas_conucos

load_dotenv()

cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MARCADOR_MENU = "[[ENVIAR_MENU]]"
MARCADOR_PEDIDO_COMPLETO = "[[PEDIDO_COMPLETO]]"
MARCADOR_TRANSFERIR_HUMANO = "[[TRANSFERIR_HUMANO]]"
PATRON_DATOS_CLIENTE = re.compile(r"\[\[DATOS_CLIENTE:\s*nombre=(.*?);\s*telefono=(.*?)\]\]")
FRASES_REACTIVACION = ["nuevo pedido", "otro pedido"]
TIEMPO_PAUSA = timedelta(hours=2)
TIEMPO_RESENA = timedelta(hours=1)

RUTA_RESENAS = os.path.join(os.path.dirname(__file__), "resenas.txt")

sesiones = {}
pausados = {}
esperando_resena = {}


def _construir_instruccion_sistema():
    menu = empanadas_conucos["menu"]

    trigo = menu["empanadas_de_trigo"]
    lista_trigo = "\n".join(
        f"- {sabor} ({desc}): ${trigo['precio']}"
        for sabor, desc in trigo["sabores"].items()
    )

    especiales = "\n".join(
        f"- {nombre} ({datos['descripcion']}): ${datos['precio']}"
        for nombre, datos in menu["especiales"].items()
    )

    flautas = "\n".join(f"- {nombre}: ${precio}" for nombre, precio in menu["flautas"].items())

    conuquitos = menu["conuquitos"]
    lista_conuquitos = "\n".join(
        f"- {sabor} ({desc})" for sabor, desc in conuquitos["sabores"].items()
    )

    caldos = "\n".join(
        f"- {nombre}: ${precio}" for nombre, precio in menu["caldos_y_arepas"].items()
    )

    congelados = menu["congelados"]

    bebidas = "\n".join(f"- {nombre}: ${precio}" for nombre, precio in menu["bebidas"].items())

    sedes = "\n".join(
        f"- {s['nombre']}: {s['direccion']}, tel: {s['telefono']}"
        + (f", whatsapp: {s['whatsapp']}" if s["whatsapp"] else "")
        for s in empanadas_conucos["sedes"]
    )

    horario = "\n".join(
        f"- {dia.capitalize()}: {' y '.join(rangos)}"
        for dia, rangos in empanadas_conucos["horario"].items()
    )

    return f"""Eres el asistente virtual de {empanadas_conucos['nombre']}, una empanadería en Bucaramanga, Colombia.
Tu único trabajo es tomar pedidos para domicilio, NO confirmarlos ni cobrar. Basate únicamente en la información de este mensaje, no inventes datos.

SEDES:
{sedes}

HORARIO:
{horario}

MENU - Empanadas de trigo (${trigo['precio']} cada una):
{lista_trigo}

MENU - Especiales:
{especiales}

MENU - Flautas:
{flautas}

MENU - Conuquitos (presentación pequeña, unidad ${conuquitos['precio_unidad']}, combo x3 ${conuquitos['precio_combo_x3']}):
{lista_conuquitos}

MENU - Caldos y arepas:
{caldos}

MENU - Congelados: {congelados['descripcion']} - ${congelados['precio']}. Sabores disponibles: {', '.join(congelados['sabores_disponibles'])}

MENU - Bebidas:
{bebidas}

REGLAS DE COMPORTAMIENTO:
1. Tu objetivo es recolectar, de forma conversacional, el pedido completo (productos y cantidades), el nombre del cliente, su teléfono, la dirección de entrega y el método de pago.
2. Si el cliente pide ver el menú o la carta, responde brevemente confirmando que se lo envías y agrega en una línea aparte, exactamente y sin nada más: {MARCADOR_MENU}
3. Si preguntan por los ingredientes de un producto específico, respóndelo tú mismo con la información de este mensaje, aunque ya hayas enviado la foto del menú antes.
4. NUNCA des el precio del domicilio ni un total final con envío incluido. Si preguntan por eso, responde amablemente que un empleado les dará ese valor al momento de pagar.
5. NUNCA confirmes el pedido en firme ni digas que ya quedó confirmado — eso lo hace un empleado.
6. Cuando ya tengas TODOS los datos (pedido, nombre, teléfono, dirección y método de pago), confirma que ya tienes todo y que un empleado va a confirmar el pedido y el valor del domicilio. Luego agrega, cada una en su propia línea, exactamente y sin nada más:
{MARCADOR_PEDIDO_COMPLETO}
[[DATOS_CLIENTE: nombre=<nombre del cliente>; telefono=<telefono del cliente>]]
(reemplaza <nombre del cliente> y <telefono del cliente> por los datos reales que te dio, sin los símbolos < >)
7. Si el cliente pide hablar con una persona real o dice que no quiere hablar con un chatbot, respeta su solicitud, dile que ya lo comunicas con un empleado, y agrega en una línea aparte, exactamente y sin nada más: {MARCADOR_TRANSFERIR_HUMANO}
8. Sé breve, amable y cercano, como un empleado colombiano de una empanadería."""


INSTRUCCION_SISTEMA = _construir_instruccion_sistema()


def _tiene_frase_reactivacion(mensaje):
    mensaje = mensaje.lower()
    return any(frase in mensaje for frase in FRASES_REACTIVACION)


def _obtener_sesion(chat_id):
    if chat_id not in sesiones:
        sesiones[chat_id] = cliente.chats.create(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=INSTRUCCION_SISTEMA),
        )
    return sesiones[chat_id]


def responder(chat_id, mensaje_usuario):
    ahora = datetime.now()

    if chat_id in pausados:
        pausado_desde = pausados[chat_id]
        if ahora - pausado_desde < TIEMPO_PAUSA and not _tiene_frase_reactivacion(mensaje_usuario):
            return None
        del pausados[chat_id]
        sesiones.pop(chat_id, None)

    es_primera_vez = chat_id not in sesiones
    sesion = _obtener_sesion(chat_id)

    respuesta = sesion.send_message(mensaje_usuario)
    texto = respuesta.text

    enviar_menu = MARCADOR_MENU in texto
    pedido_completo = MARCADOR_PEDIDO_COMPLETO in texto
    transferir_humano = MARCADOR_TRANSFERIR_HUMANO in texto

    cliente_pedido = None
    coincidencia = PATRON_DATOS_CLIENTE.search(texto)
    if pedido_completo and coincidencia:
        cliente_pedido = {
            "nombre": coincidencia.group(1).strip(),
            "telefono": coincidencia.group(2).strip(),
        }

    texto_limpio = PATRON_DATOS_CLIENTE.sub("", texto)
    texto_limpio = (
        texto_limpio.replace(MARCADOR_MENU, "")
        .replace(MARCADOR_PEDIDO_COMPLETO, "")
        .replace(MARCADOR_TRANSFERIR_HUMANO, "")
        .strip()
    )

    if pedido_completo or transferir_humano:
        pausados[chat_id] = ahora

    if es_primera_vez:
        texto_limpio = f"Hola, soy el asistente virtual de {empanadas_conucos['nombre']} 🤖.\n\n{texto_limpio}"

    return {
        "texto": texto_limpio,
        "enviar_menu": enviar_menu,
        "pausado": pedido_completo or transferir_humano,
        "cliente": cliente_pedido,
    }


def marcar_esperando_resena(chat_id, nombre, telefono):
    esperando_resena[chat_id] = {"nombre": nombre, "telefono": telefono}


def registrar_resena(chat_id, texto):
    if chat_id not in esperando_resena:
        return None

    datos_cliente = esperando_resena.pop(chat_id)
    linea = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"{datos_cliente['nombre']} | {datos_cliente['telefono']} | {texto}\n"
    )
    with open(RUTA_RESENAS, "a", encoding="utf-8") as archivo:
        archivo.write(linea)

    return "¡Muchas gracias por contarnos! Tu comentario nos ayuda mucho a mejorar 🙏"
