from flask import Flask, render_template, redirect, url_for, session
import random
import os
import math
import json
import time
import datetime

app = Flask(__name__)
app.secret_key = "segredo"

VIDA_MAX = 100
ENERGIA_MAX = 100
DIRECOES = ["norte", "sul", "leste", "oeste"]
BAU_SECRETO = random.choice(DIRECOES)

itens = {
    "fruta": {"vida": 10, "energia": 15},
    "erva": {"vida": 5, "energia": 5},
    "corda": {"vida": 0, "energia": 0},
    "carne": {"vida": 20, "energia": 20}
}

animais = {
    "onca": {"dano": 20},
    "cobra": {"dano": 10, "veneno": True},
    "macaco": {"dano": 5}
}

@app.route("/")
def index():
    if "vida" not in session:
        iniciar_jogo()
    return render_template("index.html", status=estado())

@app.route("/acao/<acao>")
def acao(acao):
    acoes = {
        "comida": buscar_comida,
        "explorar": explorar_geral,
        "curar": curar,
        "descansar": descansar,
        "abrigo": construir_abrigo,
        "plantar": plantar,
        "colher": colher,
        "cacar": cacar,
        "comer": comer_carne
    }
    if acao in acoes:
        acoes[acao]()
    elif acao in DIRECOES:
        explorar_direcao(acao)

    if session.get("veneno", False):
        aplicar_veneno()

    if session["vida"] <= 0 or session["energia"] <= 0:
        salvar_status()
        session["mensagem"] = "Fim de jogo."
        return redirect("/fim")
    elif session["pontuacao"] >= 100:
        salvar_status()
        session["mensagem"] = "Você venceu!"
        return redirect("/fim")
    return redirect("/")

@app.route("/fim")
def fim():
    return render_template("fim.html", status=estado())

@app.route("/reiniciar")
def reiniciar():
    iniciar_jogo()
    return redirect("/")

def iniciar_jogo():
    session["vida"] = VIDA_MAX
    session["energia"] = ENERGIA_MAX
    session["mochila"] = []
    session["pontuacao"] = 0
    session["veneno"] = False
    session["abrigo"] = False
    session["plantado"] = False
    session["log"] = ["Você está na floresta."]

def estado():
    return {
        "vida": session["vida"],
        "energia": session["energia"],
        "mochila": session["mochila"],
        "pontuacao": session["pontuacao"],
        "veneno": session["veneno"],
        "mensagem": session.get("mensagem", ""),
        "log": session.get("log", [])
    }

def registrar(msg):
    session["log"] = [msg] + session.get("log", [])[:2]

def buscar_comida():
    item = random.choice(list(itens.keys()))
    session["mochila"].append(item)
    session["vida"] = min(session["vida"] + itens[item]["vida"], VIDA_MAX)
    session["energia"] = min(session["energia"] + itens[item]["energia"], ENERGIA_MAX)
    session["pontuacao"] += 5
    registrar(f"Item encontrado: {item}.")

def explorar_geral():
    explorar_direcao("geral")

def explorar_direcao(zona):
    chances = {"geral": 0.4, "norte": 0.3, "sul": 0.5, "leste": 0.2, "oeste": 0.8}
    if zona == BAU_SECRETO:
        session["pontuacao"] = 100
        registrar(f"O baú foi encontrado na direção {zona}.")
        return
    session["energia"] -= 10
    if random.random() < chances.get(zona, 0.4):
        animal = random.choice(list(animais.keys()))
        session["vida"] -= animais[animal]["dano"]
        if animal == "cobra":
            session["veneno"] = True
        registrar(f"Ataque de {animal}.")
    else:
        session["pontuacao"] += 5
        registrar(f"Exploração segura em {zona}.")

def curar():
    if "erva" in session["mochila"]:
        session["mochila"].remove("erva")
        session["veneno"] = False
        session["vida"] += 5
        registrar("Você se curou com erva.")
    else:
        registrar("Nenhuma erva disponível.")

def descansar():
    session["vida"] = min(session["vida"] + 10, VIDA_MAX)
    session["energia"] = min(session["energia"] + 20, ENERGIA_MAX)
    registrar("Você descansou.")

def construir_abrigo():
    if not session["abrigo"]:
        session["energia"] = min(session["energia"] + 30, ENERGIA_MAX)
        session["pontuacao"] += 10
        session["abrigo"] = True
        registrar("Abrigo construído.")
    else:
        registrar("Você já construiu um abrigo.")

def plantar():
    if not session["plantado"]:
        session["plantado"] = True
        registrar("Erva plantada.")
    else:
        registrar("Aguardando a colheita.")

def colher():
    if session["plantado"]:
        session["mochila"].append("erva")
        session["plantado"] = False
        registrar("Erva colhida.")
    else:
        registrar("Nada foi plantado.")

def cacar():
    if random.random() < 0.5:
        session["mochila"].append("carne")
        session["pontuacao"] += 5
        registrar("Animal caçado com sucesso.")
    else:
        registrar("A caçada falhou.")

def comer_carne():
    if "carne" in session["mochila"]:
        session["mochila"].remove("carne")
        session["vida"] = min(session["vida"] + 20, VIDA_MAX)
        session["energia"] = min(session["energia"] + 20, ENERGIA_MAX)
        registrar("Você comeu carne.")
    else:
        registrar("Você não tem carne.")

def aplicar_veneno():
    session["vida"] -= 3
    registrar("Dano de veneno aplicado.")

def salvar_status():
    with open("status_final.txt", "w") as f:
        json.dump({
            "vida": session["vida"],
            "energia": session["energia"],
            "pontuacao": session["pontuacao"],
            "mochila": session["mochila"],
            "tempo": datetime.datetime.now().isoformat()
        }, f, indent=2)
if __name__ == "__main__":
    app.run(debug=True)