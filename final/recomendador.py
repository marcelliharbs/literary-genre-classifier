from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .catalogo import CatalogoLivros


class _Representacao:
    def __init__(self, nome: str, rotulo: str, descricao: str, matrix,
                 vectorizer=None) -> None:
        self.nome = nome
        self.rotulo = rotulo
        self.descricao = descricao
        self.matrix = matrix
        self.vectorizer = vectorizer
        self.tamanho_vocabulario = len(vectorizer.vocabulary_) if vectorizer else 0

    def palavras_parecidas(self, palavra: str, n: int = 8):
        return []


class _RRF:
    def __init__(self, k: int = 60) -> None:
        self.k = k


class _ExplicadorConsulta:
    STOPWORDS = {
        "a", "an", "and", "ao", "as", "com", "da", "de", "do", "dos",
        "e", "em", "for", "from", "in", "is", "na", "no", "of", "or",
        "os", "para", "the", "um", "uma",
    }

    def limpar_consulta(self, consulta: str) -> str:
        tokens = []
        for token in consulta.lower().replace(",", " ").replace(";", " ").split():
            token = token.strip(".,!?;:()[]{}")
            if len(token) > 1 and token not in self.STOPWORDS:
                tokens.append(token)
        return " ".join(tokens)


class RecomendadorLivros:
    ROTULOS = {
        "bow": "BoW",
        "tfidf": "TF-IDF",
        "hibrido": "Híbrido (BoW + TF-IDF)",
    }

    def __init__(self, catalogo: CatalogoLivros, modelos: Sequence[str] = ("bow", "tfidf"),
                 hibrido: Sequence[str] = ("bow", "tfidf"), rrf_k: int = 60,
                 nome_modelo_bert: str = "", encoder_bert=None,
                 diretorio_cache: str = "") -> None:
        self.catalogo = catalogo
        self.hibrido = tuple(hibrido)
        self.fusao = _RRF(rrf_k)
        self.explicador = _ExplicadorConsulta()
        self.avisos = []

        textos = catalogo.df["texto_recomendacao"].fillna("").astype(str)
        bow_vectorizer = CountVectorizer(stop_words="english", max_features=10000)
        bow_matrix = bow_vectorizer.fit_transform(textos)
        tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=10000)
        tfidf_matrix = tfidf_vectorizer.fit_transform(textos)

        self.representacoes = OrderedDict({
            "bow": _Representacao("bow", "BoW", "Contagem de palavras", bow_matrix, bow_vectorizer),
            "tfidf": _Representacao("tfidf", "TF-IDF", "Peso relativo das palavras", tfidf_matrix, tfidf_vectorizer),
        })
        self.modelos = tuple(self.representacoes)

    def descrever_modelos(self):
        return {
            nome: {"rotulo": r.rotulo, "descricao": r.descricao}
            for nome, r in self.representacoes.items()
        }

    def rotulo_modelo(self, modelo: str) -> str:
        return self.ROTULOS.get(modelo, modelo)

    def resolver_modelos(self, modelo: str) -> Tuple[str, ...]:
        if modelo == "hibrido":
            return tuple(m for m in self.hibrido if m in self.representacoes)
        if modelo == "todos":
            return tuple(self.representacoes)
        return (modelo,) if modelo in self.representacoes else ()

    def termos_desconhecidos(self, consulta: str) -> list[str]:
        tokens = consulta.lower().replace("?", " ").split()
        vocab = set()
        for rep in self.representacoes.values():
            if rep.vectorizer:
                vocab.update(rep.vectorizer.vocabulary_)
        return [t.strip(".,;!") for t in tokens if len(t) > 2 and t.strip(".,;!") not in vocab][:10]

    def _filtrar_genero(self, indices: np.ndarray, genero: Optional[str]) -> np.ndarray:
        if not genero:
            return indices
        generos = self.catalogo.df.iloc[indices]["genero"].to_numpy()
        return indices[generos == genero]

    def recomendar_por_consulta(self, consulta: str, n: int = 5, modelo: str = "hibrido",
                                genero: Optional[str] = None) -> pd.DataFrame:
        if modelo == "todos":
            modelo = "hibrido"
        modelos = self.resolver_modelos(modelo)
        if not modelos:
            return pd.DataFrame()
        rankings = []
        for nome in modelos:
            rep = self.representacoes[nome]
            vetor = rep.vectorizer.transform([consulta])
            scores = cosine_similarity(vetor, rep.matrix).ravel()
            indices = np.argsort(scores)[::-1]
            indices = self._filtrar_genero(indices, genero)
            rankings.append([(int(i), float(scores[i])) for i in indices[:max(n + 20, n)] if scores[i] > 0])
        return self._combinar_rankings(rankings, n)

    def recomendar_similares(self, livro: str, n: int = 5, modelo: str = "hibrido",
                             genero: Optional[str] = None) -> pd.DataFrame:
        indices = [self.catalogo.localizar(livro)]
        return self.recomendar_por_perfil_indices(indices, n, modelo, genero, excluir=indices)

    def recomendar_por_perfil(self, livros: Sequence[str], n: int = 5, modelo: str = "hibrido",
                              genero: Optional[str] = None) -> pd.DataFrame:
        indices = [self.catalogo.localizar(livro) for livro in livros]
        return self.recomendar_por_perfil_indices(indices, n, modelo, genero, excluir=indices)

    def recomendar_por_perfil_indices(self, indices: Sequence[int], n: int, modelo: str,
                                      genero: Optional[str], excluir: Sequence[int]) -> pd.DataFrame:
        modelos = self.resolver_modelos(modelo)
        rankings = []
        for nome in modelos:
            rep = self.representacoes[nome]
            vetores = rep.matrix[list(indices)]
            perfil = np.asarray(vetores.mean(axis=0)).ravel() if len(indices) > 1 else np.asarray(vetores.toarray()).ravel()
            scores = cosine_similarity(perfil.reshape(1, -1), rep.matrix).ravel()
            scores[list(excluir)] = -1
            ranked = np.argsort(scores)[::-1]
            ranked = self._filtrar_genero(ranked, genero)
            rankings.append([(int(i), float(scores[i])) for i in ranked[:n + 20] if scores[i] >= 0])
        return self._combinar_rankings(rankings, n)

    def comparar_modelos(self, consulta: str, n: int = 5, genero: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        tabelas = OrderedDict()
        for nome in self.modelos:
            tabelas[nome] = self.recomendar_por_consulta(consulta, n, nome, genero)
        tabelas["hibrido"] = self.recomendar_por_consulta(consulta, n, "hibrido", genero)
        return tabelas

    def _combinar_rankings(self, rankings: Iterable[list], n: int) -> pd.DataFrame:
        rankings = list(rankings)
        if not rankings:
            return pd.DataFrame()
        if len(rankings) == 1:
            lista = rankings[0][:n]
            scores = {i: s for i, s in lista}
        else:
            scores = {}
            for ranking in rankings:
                for pos, (i, original) in enumerate(ranking, 1):
                    scores[i] = scores.get(i, 0.0) + 1.0 / (self.fusao.k + pos)
            lista = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:n]
            scores = dict(lista)
        indices = [i for i, _ in lista]
        if not indices:
            return pd.DataFrame()
        df = self.catalogo.df.iloc[indices].copy()
        df["score"] = [scores[i] for i in indices]
        df["termos"] = df["title"].apply(lambda title: [])
        return df[["book_id", "title", "author", "autor_legivel", "genero", "score", "termos"]].reset_index(drop=True)
