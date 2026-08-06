import re

from flask import Flask, render_template

from datos import empanadas_conucos

app = Flask(__name__)


def _slug(texto):
    texto = texto.lower()
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")


def construir_catalogo(datos):
    menu = datos["menu"]
    catalogo = []

    trigo = menu["empanadas_de_trigo"]
    for sabor, descripcion in trigo["sabores"].items():
        catalogo.append({
            "id": f"trigo-{_slug(sabor)}",
            "categoria": "Empanadas de trigo",
            "nombre": sabor.capitalize(),
            "descripcion": descripcion,
            "precio": trigo["precio"],
        })

    for nombre, info in menu["especiales"].items():
        catalogo.append({
            "id": f"especial-{_slug(nombre)}",
            "categoria": "Especiales",
            "nombre": nombre.capitalize(),
            "descripcion": info["descripcion"],
            "precio": info["precio"],
        })

    for nombre, precio in menu["flautas"].items():
        catalogo.append({
            "id": f"flauta-{_slug(nombre)}",
            "categoria": "Flautas",
            "nombre": nombre.capitalize(),
            "descripcion": "",
            "precio": precio,
        })

    conuquitos = menu["conuquitos"]
    for sabor, descripcion in conuquitos["sabores"].items():
        catalogo.append({
            "id": f"conuquito-{_slug(sabor)}",
            "categoria": "Conuquitos",
            "nombre": sabor.capitalize(),
            "descripcion": descripcion,
            "precio": conuquitos["precio_unidad"],
        })

    for nombre, precio in menu["caldos_y_arepas"].items():
        catalogo.append({
            "id": f"caldo-{_slug(nombre)}",
            "categoria": "Caldos y arepas",
            "nombre": nombre.capitalize(),
            "descripcion": "",
            "precio": precio,
        })

    congelados = menu["congelados"]
    catalogo.append({
        "id": "congelados-combo",
        "categoria": "Congelados",
        "nombre": "Combo x6 congeladas",
        "descripcion": congelados["descripcion"] + ". Indica los sabores en observaciones.",
        "precio": congelados["precio"],
    })

    for nombre, precio in menu["bebidas"].items():
        catalogo.append({
            "id": f"bebida-{_slug(nombre)}",
            "categoria": "Bebidas",
            "nombre": nombre.capitalize(),
            "descripcion": "",
            "precio": precio,
        })

    return catalogo


@app.route("/")
def index():
    return render_template(
        "index.html",
        sedes=empanadas_conucos["sedes"],
        catalogo=construir_catalogo(empanadas_conucos),
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
