from flask import Flask, render_template, request, jsonify
import json, os, base64, requests

app = Flask(__name__)
CARDAPIO_FILE = "cardapio.json"

# --- Config GitHub ---
GITHUB_TOKEN = "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"  # substitua pelo seu token
GITHUB_OWNER = "vitor84579364"
GITHUB_REPO = "saborcaseiro"
GITHUB_PATH = "cardapio.json"
GITHUB_BRANCH = "main"

# --- Funções utilitárias ---
def carregar_cardapio():
    if os.path.exists(CARDAPIO_FILE):
        with open(CARDAPIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"comidas": [], "bebidas": []}

def salvar_cardapio_local(cardapio):
    with open(CARDAPIO_FILE, "w", encoding="utf-8") as f:
        json.dump(cardapio, f, ensure_ascii=False, indent=2)

def salvar_cardapio_github(cardapio):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    # Pegar o SHA atual do arquivo
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Erro ao acessar GitHub: {r.text}")
    sha = r.json()["sha"]

    # Codificar o conteúdo
    content = base64.b64encode(json.dumps(cardapio, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")

    data = {
        "message": "Atualização via painel admin",
        "content": content,
        "sha": sha,
        "branch": GITHUB_BRANCH
    }

    r = requests.put(url, headers=headers, json=data)
    if r.status_code not in [200, 201]:
        raise Exception(f"Erro ao atualizar GitHub: {r.text}")
    return r.json()

def salvar_cardapio(cardapio):
    salvar_cardapio_local(cardapio)
    salvar_cardapio_github(cardapio)

# --- Rotas ---
@app.route("/")
def index():
    return "Página inicial do Sabor Caseiro"

@app.route("/api/produtos", methods=["GET"])
def listar_produtos():
    return jsonify(carregar_cardapio())

@app.route("/api/produto", methods=["POST"])
def adicionar_produto():
    data = request.json
    cardapio = carregar_cardapio()
    tipo = data.get("tipo")  # "comidas" ou "bebidas"
    if tipo not in cardapio:
        return jsonify({"erro": "Tipo inválido"}), 400
    
    # gerar id único
    ids = [p["id"] for p in cardapio[tipo]]
    novo_id = max(ids, default=0) + 1
    data["id"] = novo_id
    cardapio[tipo].append(data)
    salvar_cardapio(cardapio)
    return jsonify({"sucesso": True, "id": novo_id})

@app.route("/api/produto/<tipo>/<int:id>", methods=["DELETE"])
def remover_produto(tipo, id):
    cardapio = carregar_cardapio()
    if tipo not in cardapio:
        return jsonify({"erro": "Tipo inválido"}), 400
    cardapio[tipo] = [p for p in cardapio[tipo] if p["id"] != id]
    salvar_cardapio(cardapio)
    return jsonify({"sucesso": True})

@app.route("/api/produto/<tipo>/<int:id>", methods=["PATCH"])
def atualizar_produto(tipo, id):
    data = request.json
    cardapio = carregar_cardapio()
    if tipo not in cardapio:
        return jsonify({"erro": "Tipo inválido"}), 400
    for p in cardapio[tipo]:
        if p["id"] == id:
            p.update(data)
            salvar_cardapio(cardapio)
            return jsonify({"sucesso": True})
    return jsonify({"erro": "Produto não encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True)
