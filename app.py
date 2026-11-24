from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from final.configuracao import ConfiguracaoApp
from final.resultados_registrados import ResultadosRegistrados
from final.servico import ConsultaInvalidaError, ServicoLivros


app = Flask(__name__)
CORS(app)

config = ConfiguracaoApp.padrao()
print("Construindo o protótipo...", flush=True)
servico = ServicoLivros.construir(config)
print("Protótipo pronto.", flush=True)


def erro(error):
    return jsonify({"erro": str(error)}), 400


@app.errorhandler(ConsultaInvalidaError)
def tratar_consulta(error):
    return erro(error)


@app.errorhandler(Exception)
def tratar_erro(error):
    app.logger.exception("Erro na aplicação")
    return jsonify({"erro": "Ocorreu um erro interno.", "detalhe": str(error)}), 500


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify(servico.status())


@app.get("/api/sugestoes")
def sugestoes():
    return jsonify(servico.sugerir_titulos(request.args.get("trecho", "")))


@app.post("/api/buscar")
def buscar():
    dados = request.get_json(silent=True) or request.form
    return jsonify(servico.buscar(
        dados.get("consulta", ""),
        dados.get("modelo", "hibrido"),
        dados.get("n", 5),
        dados.get("genero"),
    ))


@app.post("/api/comparar")
def comparar():
    dados = request.get_json(silent=True) or request.form
    return jsonify(servico.comparar(
        dados.get("consulta", ""), dados.get("n", 5), dados.get("genero")
    ))


@app.post("/api/similares")
def similares():
    dados = request.get_json(silent=True) or request.form
    return jsonify(servico.similares(
        dados.get("livro", ""), dados.get("modelo", "hibrido"),
        dados.get("n", 5), dados.get("genero")
    ))


@app.post("/api/perfil")
def perfil():
    dados = request.get_json(silent=True) or request.form
    livros = dados.get("livros", [])
    if isinstance(livros, str):
        livros = [item.strip() for item in livros.split(",") if item.strip()]
    return jsonify(servico.perfil(
        livros, dados.get("modelo", "hibrido"),
        dados.get("n", 5), dados.get("genero")
    ))


@app.post("/api/chat")
def chat():
    dados = request.get_json(silent=True) or request.form
    return jsonify(servico.chat(dados.get("mensagem", ""), dados.get("estado")))


@app.get("/api/resultados")
def resultados():
    return jsonify({
        "recomendacao_por_genero": ResultadosRegistrados.RECOMENDACAO_POR_GENERO,
        "classificacao_genero": ResultadosRegistrados.CLASSIFICACAO_GENERO,
        "avaliacao_manual": ResultadosRegistrados.AVALIACAO_MANUAL,
        "exemplos": ResultadosRegistrados.EXEMPLOS,
        "conversa": ResultadosRegistrados.CONVERSA,
        "avaliacao_calculada": servico.avaliar(recalcular=False),
    })


@app.get("/api/mapa")
def mapa():
    return jsonify(servico.mapa(
        request.args.get("modelo", "tfidf"),
        request.args.get("consulta"),
        request.args.get("n", 5),
    ))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
