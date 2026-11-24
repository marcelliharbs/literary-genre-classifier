"""Fachada que une catálogo, recomendador, chatbot, mapa e avaliação para a camada web."""
from __future__ import annotations

import threading
import time
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from .avaliacao import AvaliadorPorGenero
from .catalogo import CatalogoLivros
from .chatbot import ChatbotLivros
from .configuracao import ConfiguracaoApp
from .mapa import ProjetorMapa
from .recomendador import RecomendadorLivros
from .serializacao import SerializadorResultados


class ConsultaInvalidaError(ValueError):
    """Parâmetro de entrada inválido (vazio, grande demais, modelo ou gênero desconhecido)."""


class ServicoLivros:
    """Operações da aplicação, já validadas e em formato JSON.

    A camada web (Flask) só chama estes métodos; nenhuma regra de PLN fica nas rotas.
    """

    TAMANHO_MAXIMO_CONSULTA = 300
    LIMITE_RESULTADOS = 20

    def __init__(self, config: ConfiguracaoApp, catalogo: CatalogoLivros, recomendador: RecomendadorLivros) -> None:
        self.config = config
        self.catalogo = catalogo
        self.rec = recomendador
        self.chatbot = ChatbotLivros(recomendador)
        self.projetor = ProjetorMapa(recomendador, n_clusters=config.n_clusters)
        self.avaliador = AvaliadorPorGenero(recomendador)
        self._avaliacao: Optional[Dict[str, Any]] = None
        self._trava_avaliacao = threading.Lock()

    # ------------------------------------------------------------ construção
    @classmethod
    def construir(cls, config: ConfiguracaoApp, encoder_bert=None,
                  log: Callable[[str], None] = print) -> "ServicoLivros":
        """Carrega o CSV e constrói todas as representações (pode levar alguns segundos)."""
        log(f"Lendo {config.caminho_csv} …")
        catalogo = CatalogoLivros.carregar(config.caminho_csv, config.coluna_texto, config.coluna_bert)
        log(f"{len(catalogo)} livros carregados. Construindo representações: {', '.join(config.modelos)} …")
        recomendador = RecomendadorLivros(
            catalogo, modelos=config.modelos, hibrido=config.hibrido, rrf_k=config.rrf_k,
            nome_modelo_bert=config.nome_modelo_bert, encoder_bert=encoder_bert,
            diretorio_cache=config.diretorio_cache,
        )
        for aviso in recomendador.avisos:
            log(f"AVISO: {aviso}")
        log(f"Pronto. Modelos disponíveis: {', '.join(recomendador.modelos)}.")
        return cls(config, catalogo, recomendador)

    # -------------------------------------------------------------- validações
    def _consulta(self, texto: Any) -> str:
        texto = str(texto or "").strip()
        if not texto:
            raise ConsultaInvalidaError("Digite uma consulta.")
        if len(texto) > self.TAMANHO_MAXIMO_CONSULTA:
            raise ConsultaInvalidaError(f"Consulta longa demais (máximo {self.TAMANHO_MAXIMO_CONSULTA} caracteres).")
        return texto

    def _n(self, valor: Any, padrao: int = 5) -> int:
        try:
            n = int(valor)
        except (TypeError, ValueError):
            n = padrao
        return max(1, min(n, self.LIMITE_RESULTADOS))

    def _genero(self, genero: Optional[str]) -> Optional[str]:
        if not genero:
            return None
        if genero not in self.catalogo.contagem_por_genero():
            raise ConsultaInvalidaError(f"Gênero desconhecido: {genero}.")
        return genero

    def _modelo(self, modelo: Optional[str]) -> str:
        modelo = modelo or "hibrido"
        if modelo not in ("hibrido", "todos", *self.rec.modelos):
            raise ConsultaInvalidaError(f"Modelo indisponível: {modelo}. Opções: {self.rec.modelos + ['hibrido']}.")
        return modelo

    # ----------------------------------------------------------------- consultas
    def status(self) -> Dict[str, Any]:
        """Estado geral: tamanho do acervo, modelos construídos e avisos."""
        resumo = self.catalogo.resumo()
        return {
            **resumo,
            "modelos": self.rec.descrever_modelos(),
            "hibrido": self.rec.hibrido,
            "rotulo_hibrido": self.rec.rotulo_modelo("hibrido"),
            "avisos": self.rec.avisos,
            "rrf_k": self.rec.fusao.k,
            "vocabulario_word2vec": getattr(self.rec.representacoes.get("word2vec"), "tamanho_vocabulario", None),
            "exemplos_chat": list(ChatbotLivros.EXEMPLOS),
        }

    def sugerir_titulos(self, trecho: str) -> List[Dict[str, str]]:
        return self.catalogo.sugerir_titulos(trecho)

    def _avisos_consulta(self, consulta: str, modelos: Sequence[str]) -> List[str]:
        avisos = []
        desconhecidos = self.rec.termos_desconhecidos(consulta)
        if desconhecidos:
            avisos.append(
                "Fora do vocabulário (ignoradas por BoW e TF-IDF): " + ", ".join(desconhecidos) + ". "
                "O acervo é em inglês."
            )
        return avisos

    def buscar(self, consulta: str, modelo: str = "hibrido", n: Any = 5, genero: Optional[str] = None) -> Dict[str, Any]:
        """Busca livre por tema com um modelo (ou o híbrido)."""
        consulta = self._consulta(consulta)
        modelo, n, genero = self._modelo(modelo), self._n(n), self._genero(genero)
        t0 = time.perf_counter()
        tabela = self.rec.recomendar_por_consulta(consulta, n, modelo, genero)
        ms = (time.perf_counter() - t0) * 1000
        itens = SerializadorResultados.itens(tabela)
        avisos = self._avisos_consulta(consulta, self.rec.resolver_modelos(modelo))
        if not itens:
            avisos.append("Nenhum livro encontrado para esta consulta nesse modelo.")
        return {"consulta": consulta, "modelo": modelo, "rotulo": self.rec.rotulo_modelo(modelo),
                "genero": genero, "itens": itens, "avisos": avisos, "tempo_ms": round(ms, 1)}

    def comparar(self, consulta: str, n: Any = 5, genero: Optional[str] = None) -> Dict[str, Any]:
        """Mesma consulta em cada modelo e no híbrido, para comparar os rankings."""
        consulta, n, genero = self._consulta(consulta), self._n(n), self._genero(genero)
        t0 = time.perf_counter()
        tabelas = self.rec.comparar_modelos(consulta, n, genero)
        ms = (time.perf_counter() - t0) * 1000
        colunas = []
        for nome, tabela in tabelas.items():
            itens = SerializadorResultados.itens(tabela)
            colunas.append({
                "modelo": nome,
                "rotulo": self.rec.rotulo_modelo(nome) if nome == "hibrido" else self.rec.representacoes[nome].rotulo,
                "descricao": ("Funde os rankings de " + " e ".join(self.rec.representacoes[m].rotulo for m in self.rec.hibrido)
                              + " por posição (RRF)." if nome == "hibrido" else self.rec.representacoes[nome].descricao),
                "itens": itens,
                "vazio": not itens,
            })
        avisos = self._avisos_consulta(consulta, self.rec.modelos)
        for col in colunas:
            if col["vazio"]:
                avisos.append(f"{col['rotulo']} não encontrou resultados: nenhuma palavra da consulta pertence ao seu vocabulário.")
        return {"consulta": consulta, "genero": genero, "colunas": colunas, "avisos": avisos, "tempo_ms": round(ms, 1)}

    def similares(self, livro: str, modelo: str = "hibrido", n: Any = 5, genero: Optional[str] = None) -> Dict[str, Any]:
        """Livros com sinopse parecida com a de um livro."""
        livro = self._consulta(livro)
        modelo, n, genero = self._modelo(modelo), self._n(n), self._genero(genero)
        indice = self.catalogo.localizar(livro)
        tabela = self.rec.recomendar_similares(str(self.catalogo.df.at[indice, "book_id"]), n, modelo, genero)
        base = self.catalogo.df.loc[indice]
        return {
            "modo": "similares", "modelo": modelo, "rotulo": self.rec.rotulo_modelo(modelo), "genero": genero,
            "referencia": [{"book_id": base["book_id"], "titulo": base["title"], "autor": base["autor_legivel"] or None}],
            "itens": SerializadorResultados.itens(tabela), "avisos": [],
        }

    def perfil(self, livros: Sequence[str], modelo: str = "hibrido", n: Any = 5, genero: Optional[str] = None) -> Dict[str, Any]:
        """Livros parecidos com a média de vários livros escolhidos."""
        livros = [str(l).strip() for l in (livros or []) if str(l).strip()]
        if len(livros) < 2:
            raise ConsultaInvalidaError("Informe pelo menos dois livros para montar um perfil.")
        if len(livros) > 10:
            raise ConsultaInvalidaError("Use no máximo 10 livros no perfil.")
        modelo, n, genero = self._modelo(modelo), self._n(n), self._genero(genero)
        indices = [self.catalogo.localizar(l) for l in livros]
        tabela = self.rec.recomendar_por_perfil([str(self.catalogo.df.at[i, "book_id"]) for i in indices], n, modelo, genero)
        df = self.catalogo.df
        return {
            "modo": "perfil", "modelo": modelo, "rotulo": self.rec.rotulo_modelo(modelo), "genero": genero,
            "referencia": [{"book_id": df.at[i, "book_id"], "titulo": df.at[i, "title"],
                            "autor": df.at[i, "autor_legivel"] or None} for i in indices],
            "itens": SerializadorResultados.itens(tabela), "avisos": [],
        }

    def chat(self, mensagem: str, estado: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Uma volta de conversa com o chatbot."""
        mensagem = str(mensagem or "")
        if len(mensagem) > self.TAMANHO_MAXIMO_CONSULTA:
            raise ConsultaInvalidaError(f"Mensagem longa demais (máximo {self.TAMANHO_MAXIMO_CONSULTA} caracteres).")
        resposta = self.chatbot.responder(mensagem, estado)
        dados = asdict(resposta)
        dados["texto"] = resposta.texto
        return dados

    def mapa(self, modelo: str = "tfidf", consulta: Optional[str] = None, n: Any = 5) -> Dict[str, Any]:
        """Pontos do mapa 2D, agrupamentos e (opcionalmente) a posição de uma consulta."""
        if modelo not in self.rec.representacoes:
            raise ConsultaInvalidaError(f"Modelo indisponível: {modelo}. Opções: {self.rec.modelos}.")
        projecao = self.projetor.projetar(modelo)
        df = self.catalogo.df
        pontos = []
        for i, (x, y) in enumerate(projecao.coordenadas):
            genero = df.at[i, "genero"]
            pontos.append({
                "i": i, "book_id": df.at[i, "book_id"], "titulo": df.at[i, "title"],
                "autor": df.at[i, "autor_legivel"] or None,
                "genero": genero if isinstance(genero, str) else None,
                "cluster": int(projecao.clusters[i]), "x": round(float(x), 5), "y": round(float(y), 5),
            })
        resultado: Dict[str, Any] = {
            "modelo": modelo, "rotulo": self.rec.representacoes[modelo].rotulo, "pontos": pontos,
            "variancia_explicada": round(projecao.variancia_explicada, 4),
            "silhouette": None if projecao.silhouette is None else round(projecao.silhouette, 4),
            "n_clusters": int(len(set(projecao.clusters.tolist()))),
            "generos": self.catalogo.contagem_por_genero(), "consulta": None, "destaques": [], "avisos": [],
        }
        if consulta and consulta.strip():
            consulta = self._consulta(consulta)
            posicao = self.projetor.posicao_consulta(modelo, consulta)
            if posicao is None:
                resultado["avisos"].append("Este modelo não consegue representar a consulta (nenhuma palavra conhecida).")
            else:
                resultado["consulta"] = {"texto": consulta, "x": round(posicao[0], 5), "y": round(posicao[1], 5)}
                tabela = self.rec.recomendar_por_consulta(consulta, self._n(n), modelo)
                posicoes = {str(b): i for i, b in enumerate(df["book_id"])}
                resultado["destaques"] = [posicoes[str(b)] for b in tabela["book_id"]]
        return resultado

    def palavras_parecidas(self, palavra: str, n: Any = 8) -> Dict[str, Any]:
        """Vizinhos de uma palavra no espaço do Word2Vec (explica o que o modelo aprendeu)."""
        representacao = self.rec.representacoes.get("word2vec")
        if representacao is None:
            raise ConsultaInvalidaError("O Word2Vec não está disponível nesta execução.")
        palavra = self._consulta(palavra).split()[0].lower()
        vizinhos = representacao.palavras_parecidas(palavra, self._n(n, 8))
        return {"palavra": palavra, "vizinhos": vizinhos,
                "vocabulario": representacao.tamanho_vocabulario, "conhecida": bool(vizinhos)}

    def avaliar(self, recalcular: bool = False) -> Dict[str, Any]:
        """Precision@k e MRR por gênero com os modelos carregados (resultado em cache)."""
        with self._trava_avaliacao:
            if self._avaliacao is None or recalcular:
                t0 = time.perf_counter()
                tabela = self.avaliador.avaliar()
                tabela = tabela.astype(object).where(pd.notna(tabela), None)
                self._avaliacao = {
                    "colunas": list(tabela.columns),
                    "linhas": tabela.to_dict("records"),
                    "segundos": round(time.perf_counter() - t0, 2),
                }
            return self._avaliacao