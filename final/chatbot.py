"""Chatbot em português que traduz frases em chamadas ao :class:`RecomendadorLivros`.

O chatbot não aprende nada novo: ele **entende o pedido** (regras e expressões
regulares) e **apresenta a resposta**. Toda a recomendação continua no
recomendador. O estado da conversa viaja com cada mensagem (``Estado``), então o
servidor não precisa guardar sessões.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from .catalogo import CatalogoLivros, LivroNaoEncontradoError
from .recomendador import RecomendadorLivros
from .serializacao import SerializadorResultados


class TradutorConsulta:
    """Normaliza o texto, detecta gênero e traduz palavras PT → EN com um glossário.

    O acervo e o MiniLM são em inglês; por isso a tradução é palavra por palavra e
    limitada ao :attr:`GLOSSARIO`. Palavras fora dele seguem em português e não
    encontram correspondência no vocabulário.
    """

    GLOSSARIO = {
        "guerra": "war", "amor": "love", "casamento": "marriage", "morte": "death",
        "mar": "sea", "viagem": "journey", "futuro": "future", "espaco": "space",
        "fantasma": "ghost", "vampiro": "vampire", "monstro": "monster",
        "crime": "crime", "detetive": "detective", "assassinato": "murder",
        "familia": "family", "politica": "politics", "religiao": "religion",
        "pirata": "pirate", "navio": "ship", "ciencia": "science", "rei": "king",
        "rainha": "queen", "aventura": "adventure", "misterio": "mystery",
        "terror": "horror", "romance": "romance", "poesia": "poetry",
        "infantil": "children", "escravidao": "slavery", "sociedade": "society",
    }

    GENEROS = {
        "ficcao cientifica": "Ficção científica/fantasia", "fantasia": "Ficção científica/fantasia",
        "misterio": "Mistério/policial", "policial": "Mistério/policial", "detetive": "Mistério/policial",
        "terror": "Terror/gótico", "gotico": "Terror/gótico", "horror": "Terror/gótico",
        "romance": "Romance", "guerra": "Guerra", "aventura": "Aventura",
        "ficcao historica": "Ficção histórica", "faroeste": "Faroeste",
        "humor": "Humor", "poesia": "Poesia", "infantil": "Literatura infantil/juvenil",
        "juvenil": "Literatura infantil/juvenil",
    }

    PALAVRAS_DE_COMANDO = (
        "quero|livros?|sobre|de|do|da|com|que|tenha|me|indica|recomende|recomenda|"
        "algo|um|uma|e|ou|o|a|os|as|sugira|sugere|gosto|procuro|busco"
    )

    @staticmethod
    def normalizar(texto: str) -> str:
        """Minúsculas, sem acentos e com espaços colapsados."""
        texto = unicodedata.normalize("NFKD", texto.lower())
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", texto).strip()

    def traduzir(self, texto: str) -> str:
        """Troca cada palavra conhecida do glossário pela tradução em inglês."""
        return " ".join(self.GLOSSARIO.get(p, p) for p in self.normalizar(texto).split())

    def achar_genero(self, texto: str) -> Optional[str]:
        """Gênero citado na frase (testa as chaves da mais longa para a mais curta)."""
        norm = self.normalizar(texto)
        for chave in sorted(self.GENEROS, key=len, reverse=True):
            if re.search(rf"\b{chave}\b", norm):
                return self.GENEROS[chave]
        return None

    def consulta_em_ingles(self, texto: str) -> str:
        """Traduz e remove palavras de comando ("quero", "livro", "sobre"…)."""
        consulta = self.traduzir(texto)
        consulta = re.sub(rf"\b({self.PALAVRAS_DE_COMANDO})\b", " ", consulta)
        return re.sub(r"\s+", " ", consulta).strip()


@dataclass
class Intencao:
    """O que a pessoa pediu, depois da interpretação da mensagem."""

    tipo: str                       # vazio, sair, ajuda, saudacao, mais, porque, sem_filtro, similar, consulta
    texto: str = ""                 # mensagem original
    genero: Optional[str] = None
    livros: List[str] = field(default_factory=list)


class InterpretadorMensagem:
    """Detecta a intenção da mensagem por expressões regulares."""

    PADRAO_SAIR = r"^(sair|tchau|fim|quit|exit|ate mais)\b"
    PADRAO_AJUDA = r"^(ajuda|help|o que voce faz|como funciona|\?)$"
    PADRAO_SAUDACAO = r"^(oi|ola|bom dia|boa tarde|boa noite|e ai|hey|hi|hello)\b"
    PADRAO_MAIS = r"^(mais|mais um|outros|me mostra mais|quero mais)\b"
    PADRAO_PORQUE = r"^(por ?que|porque|pq|explica|por que esses)"
    PADRAO_SEM_FILTRO = r"^(sem filtro|sem genero|todos os generos|remover filtro)"
    PADRAO_SIMILAR = (
        r"(parecid\w+ com|similar\w* (a|ao|com)|gostei d[eoa]s?|li e gostei|curti|"
        r"recomend\w+ (algo|livros?) (como|tipo))\s+(?P<livros>.+)"
    )

    def __init__(self, tradutor: TradutorConsulta, catalogo: Optional[CatalogoLivros] = None) -> None:
        self.tradutor = tradutor
        self.catalogo = catalogo

    def separar_livros(self, trecho: str) -> List[str]:
        """Quebra "A, B e C" em títulos, sem separar títulos que contêm "and" ou "e".

        Se o trecho inteiro for parte de um título do catálogo ("War and Peace"),
        ele é mantido como um único livro.
        """
        trecho = re.sub(r"[\"“”']", "", trecho).strip(" .!?")
        if self.catalogo is not None and trecho:
            if self.catalogo.df["title"].str.contains(trecho, case=False, regex=False).any():
                return [trecho]
        partes = re.split(r"\s*(?:,|;|\be\b|\band\b)\s*", trecho)
        return [p.strip(" .!?") for p in partes if p.strip(" .!?")]

    def interpretar(self, mensagem: str) -> Intencao:
        bruto = mensagem.strip()
        msg = self.tradutor.normalizar(bruto)
        if not msg:
            return Intencao("vazio", bruto)
        if re.search(self.PADRAO_SAIR, msg):
            return Intencao("sair", bruto)
        if re.match(self.PADRAO_AJUDA, msg):
            return Intencao("ajuda", bruto)
        if re.match(self.PADRAO_SAUDACAO, msg) and len(msg.split()) <= 3:
            return Intencao("saudacao", bruto)
        if re.match(self.PADRAO_MAIS, msg):
            return Intencao("mais", bruto)
        if re.match(self.PADRAO_PORQUE, msg):
            return Intencao("porque", bruto)
        if re.match(self.PADRAO_SEM_FILTRO, msg):
            return Intencao("sem_filtro", bruto)

        m = re.search(self.PADRAO_SIMILAR, bruto, flags=re.I)
        if m:
            livros = self.separar_livros(m.group("livros"))
            genero = self.tradutor.achar_genero(bruto[: m.start("livros")])
            return Intencao("similar", bruto, genero, livros)
        return Intencao("consulta", bruto, self.tradutor.achar_genero(bruto))


@dataclass
class Estado:
    """Memória curta da conversa (serializável em JSON).

    ``ultima_chamada``  ``{"tipo", "args", "n"}`` da última recomendação, usada por "mais"
    ``itens``           resumo do último resultado mostrado, usado por "por que"
    """

    ultima_chamada: Optional[Dict[str, Any]] = None
    itens: List[Dict[str, Any]] = field(default_factory=list)
    top_n: int = 5

    TIPOS_VALIDOS = ("consulta", "similares", "perfil")

    def para_dict(self) -> Dict[str, Any]:
        return {"ultima_chamada": self.ultima_chamada, "itens": self.itens, "top_n": self.top_n}

    @classmethod
    def de_dict(cls, dados: Optional[Dict[str, Any]]) -> "Estado":
        """Reconstrói o estado enviado pelo navegador, descartando o que for inválido."""
        if not isinstance(dados, dict):
            return cls()
        estado = cls()
        chamada = dados.get("ultima_chamada")
        if isinstance(chamada, dict) and chamada.get("tipo") in cls.TIPOS_VALIDOS \
                and isinstance(chamada.get("args"), dict):
            n = chamada.get("n")
            estado.ultima_chamada = {
                "tipo": chamada["tipo"],
                "args": {k: v for k, v in chamada["args"].items() if k in {"consulta", "livro", "livros", "genero"}},
                "n": n if isinstance(n, int) and 1 <= n <= 50 else estado.top_n,
            }
        itens = dados.get("itens")
        if isinstance(itens, list):
            estado.itens = [
                {"titulo": str(i.get("titulo", "")), "termos": [str(t) for t in i.get("termos", [])][:10]}
                for i in itens[:50] if isinstance(i, dict)
            ]
        return estado


@dataclass
class RespostaChatbot:
    """Resposta estruturada: cabeçalho, livros sugeridos e rodapé."""

    tipo: str
    cabecalho: str = ""
    itens: List[Dict[str, Any]] = field(default_factory=list)
    rodape: str = ""
    avisos: List[str] = field(default_factory=list)
    estado: Dict[str, Any] = field(default_factory=dict)
    encerrar: bool = False

    @property
    def texto(self) -> str:
        """Versão em texto puro (útil no terminal e nos testes)."""
        linhas = [self.cabecalho] if self.cabecalho else []
        for item in self.itens:
            genero = f" [{item['genero']}]" if item.get("genero") else ""
            autor = f" — {item['autor']}" if item.get("autor") else ""
            termos = f": {', '.join(item['termos'])}" if self.tipo == "explicacao" and item.get("termos") else ""
            linhas.append(f"{item['posicao']}. {item['titulo']}{autor}{genero}{termos}")
        linhas.extend(f"Aviso: {a}" for a in self.avisos)
        if self.rodape:
            linhas.append(self.rodape)
        return "\n".join(linhas)


class ChatbotLivros:
    """Conversa em português e devolve recomendações do :class:`RecomendadorLivros`.

    Intenções: tema (consulta livre), gênero, livro parecido, perfil (vários livros),
    ``mais``, ``por que``, ``sem filtro``, ``ajuda`` e ``sair``.
    """

    EXEMPLOS = (
        "quero um livro sobre guerra e política",
        "romance sobre casamento",
        "terror com fantasmas",
        "parecido com Dracula",
        "gostei de Dracula, Frankenstein e Jekyll",
    )

    def __init__(self, recomendador: RecomendadorLivros, top_n: int = 5) -> None:
        self.rec = recomendador
        self.top_n = top_n
        self.tradutor = TradutorConsulta()
        self.interprete = InterpretadorMensagem(self.tradutor, recomendador.catalogo)

    # ------------------------------------------------------------------ API
    def responder(self, mensagem: str, estado: Optional[Dict[str, Any]] = None) -> RespostaChatbot:
        """Processa uma mensagem e devolve a resposta e o novo estado."""
        est = Estado.de_dict(estado)
        est.top_n = self.top_n
        intencao = self.interprete.interpretar(mensagem)

        tratadores = {
            "vazio": lambda: self._simples("vazio", "Pode me dizer o que você quer ler? Digite 'ajuda' para ver exemplos."),
            "sair": lambda: RespostaChatbot("sair", "Até a próxima leitura!", encerrar=True),
            "ajuda": lambda: self._simples("ajuda", self.ajuda()),
            "saudacao": lambda: self._simples(
                "saudacao",
                "Olá! Sou o chatbot de livros do Project Gutenberg. Me conte um tema, um gênero "
                "ou livros que você gostou. ('ajuda' mostra exemplos)"),
            "mais": lambda: self._mais(est),
            "porque": lambda: self._explicar(est),
            "sem_filtro": lambda: self._sem_filtro(est),
            "similar": lambda: self._por_livros(intencao.livros, intencao.genero, est),
            "consulta": lambda: self._por_consulta(intencao.texto, intencao.genero, est),
        }
        resposta = tratadores[intencao.tipo]()
        if not resposta.estado:
            resposta.estado = est.para_dict()
        return resposta

    # --------------------------------------------------------------- tratadores
    def _simples(self, tipo: str, texto: str) -> RespostaChatbot:
        return RespostaChatbot(tipo, cabecalho=texto)

    def _por_consulta(self, texto: str, genero: Optional[str], est: Estado) -> RespostaChatbot:
        consulta = self.tradutor.consulta_em_ingles(texto)
        if not consulta:
            return self._simples("erro", "Não entendi o tema. Tente algo como: 'quero um livro sobre guerra e política'.")

        tokens = [t for t in self.rec.explicador.limpar_consulta(consulta).split() if len(t) > 1]
        desconhecidos = self.rec.termos_desconhecidos(consulta)
        if tokens and len(desconhecidos) == len(tokens):
            exemplos = ", ".join(list(self.tradutor.GLOSSARIO)[:8])
            return self._simples(
                "erro",
                f"Não reconheci nenhuma destas palavras no vocabulário dos livros: {', '.join(desconhecidos)}. "
                f"O acervo está em inglês. Tente palavras como {exemplos}… ou escreva a consulta em inglês.",
            )
        avisos = []
        if desconhecidos:
            avisos.append(f"Estas palavras não estão no vocabulário e foram ignoradas pelo TF-IDF: {', '.join(desconhecidos)}.")
        return self._rodar("consulta", {"consulta": consulta, "genero": genero}, texto, est, avisos=avisos)

    def _por_livros(self, livros: List[str], genero: Optional[str], est: Estado) -> RespostaChatbot:
        if not livros:
            return self._simples("erro", "Qual livro? Exemplo: 'parecido com Dracula'.")
        try:
            if len(livros) == 1:
                return self._rodar("similares", {"livro": livros[0], "genero": genero}, livros[0], est)
            return self._rodar("perfil", {"livros": livros, "genero": genero}, ", ".join(livros), est)
        except LivroNaoEncontradoError as erro:
            return self._simples("erro", f"{erro} Tente o título em inglês, como está no Gutenberg.")

    def _sem_filtro(self, est: Estado) -> RespostaChatbot:
        chamada = est.ultima_chamada
        if not chamada:
            return self._simples("erro", "Ainda não recomendei nada. Me diga um tema ou um livro que você gostou.")
        if not chamada["args"].get("genero"):
            return self._simples("erro", "A última busca já estava sem filtro de gênero.")
        args = {**chamada["args"], "genero": None}
        rotulo = args.get("consulta") or args.get("livro") or ", ".join(args.get("livros", []))
        return self._rodar(chamada["tipo"], args, rotulo, est)

    def _mais(self, est: Estado) -> RespostaChatbot:
        chamada = est.ultima_chamada
        if not chamada:
            return self._simples("erro", "Ainda não recomendei nada. Me diga um tema ou um livro que você gostou.")
        n_novo = chamada["n"] + est.top_n
        try:
            tabela = self._chamar(chamada, n_novo).iloc[chamada["n"]:]
        except LivroNaoEncontradoError as erro:
            return self._simples("erro", str(erro))
        if tabela.empty:
            return self._simples("erro", "Acabaram as sugestões para essa busca.")
        chamada["n"] = n_novo
        itens = SerializadorResultados.itens(tabela)
        for i, item in enumerate(itens, start=n_novo - est.top_n + 1):
            item["posicao"] = i
        est.itens = [{"titulo": i["titulo"], "termos": i["termos"]} for i in itens]
        return RespostaChatbot(
            "mais", cabecalho="Mais sugestões:", itens=itens,
            rodape="Digite 'mais', 'por que' ou faça outra pergunta.", estado=est.para_dict(),
        )

    def _explicar(self, est: Estado) -> RespostaChatbot:
        if not est.itens:
            return self._simples("erro", "Ainda não tenho uma recomendação para explicar.")
        itens = [
            {"posicao": i, "titulo": it["titulo"], "termos": it["termos"], "genero": None, "autor": None}
            for i, it in enumerate(est.itens, start=1)
        ]
        resposta = RespostaChatbot(
            "explicacao", cabecalho="Os termos que mais pesaram no TF-IDF para cada sugestão:", itens=itens,
            rodape="Sem termos em comum, a semelhança veio do Sentence-BERT (significado), não de palavras iguais.",
        )
        return resposta

    # ---------------------------------------------------------------- núcleo
    def _modelo(self):
        return "hibrido"

    def _chamar(self, chamada: Dict[str, Any], n: int) -> pd.DataFrame:
        a = chamada["args"]
        modelo = self._modelo()
        if chamada["tipo"] == "consulta":
            return self.rec.recomendar_por_consulta(a["consulta"], n, modelo, a.get("genero"))
        if chamada["tipo"] == "similares":
            return self.rec.recomendar_similares(a["livro"], n, modelo, a.get("genero"))
        return self.rec.recomendar_por_perfil(a["livros"], n, modelo, a.get("genero"))

    def _rodar(self, tipo: str, args: Dict[str, Any], rotulo: str, est: Estado,
               avisos: Optional[List[str]] = None) -> RespostaChatbot:
        chamada = {"tipo": tipo, "args": args, "n": est.top_n}
        tabela = self._chamar(chamada, est.top_n)
        if tabela.empty:
            return self._simples("erro", "Não encontrei nada relevante. Tente outras palavras ou digite 'sem filtro'.")
        itens = SerializadorResultados.itens(tabela)
        est.ultima_chamada = chamada
        est.itens = [{"titulo": i["titulo"], "termos": i["termos"]} for i in itens]
        genero = args.get("genero")
        extra = f" (filtro de gênero: {genero})" if genero else ""
        rodape = "Digite 'mais', 'por que'" + (", 'sem filtro'" if genero else "") + " ou faça outra pergunta."
        return RespostaChatbot(
            tipo, cabecalho=f"Sugestões para “{rotulo}”{extra}:", itens=itens, rodape=rodape,
            avisos=avisos or [], estado=est.para_dict(),
        )

    @staticmethod
    def ajuda() -> str:
        return (
            "Posso recomendar de quatro formas:\n"
            "• Por tema: 'quero um livro sobre guerra e política'\n"
            "• Por gênero: 'romance sobre casamento' ou 'terror com fantasmas'\n"
            "• Por livro: 'parecido com Dracula'\n"
            "• Por perfil: 'gostei de Dracula, Frankenstein e Jekyll'\n"
            "Depois: 'mais' (próximas sugestões), 'por que' (explica), 'sem filtro' (remove o gênero), 'sair'."
        )