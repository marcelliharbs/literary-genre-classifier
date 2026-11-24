from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import pandas as pd


class LivroNaoEncontradoError(ValueError):
    pass


class CatalogoLivros:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.reset_index(drop=True)

    @classmethod
    def carregar(cls, caminho_csv: str, coluna_texto: str = "text_final",
                 coluna_bert: str = "summary") -> "CatalogoLivros":
        df = pd.read_csv(caminho_csv)
        for coluna in ("book_id", "title", "author", "subjects", "summary", "text_final"):
            if coluna not in df.columns:
                raise ValueError(f"Coluna obrigatória ausente no CSV: {coluna}")

        df["book_id"] = df["book_id"].astype(str)
        df["title"] = df["title"].fillna("Sem título").astype(str)
        df["author"] = df["author"].fillna("").astype(str)
        df["subjects"] = df["subjects"].fillna("").astype(str)
        df["summary"] = df["summary"].fillna("").astype(str)
        df["text_final"] = df["text_final"].fillna(df["summary"]).astype(str)
        df["autor_legivel"] = df["author"].apply(cls._autor_legivel)
        df["genero"] = df["subjects"].apply(cls._inferir_genero)
        df["texto_recomendacao"] = df[coluna_texto].fillna(df["summary"]).astype(str)
        df[coluna_bert] = df[coluna_bert].fillna(df["summary"]).astype(str)
        df = df.drop_duplicates(subset=["title", "author"], keep="first").reset_index(drop=True)
        return cls(df)

    @staticmethod
    def _autor_legivel(author: str) -> str:
        author = str(author).strip()
        if not author:
            return ""
        partes = author.split(",", 1)
        return author if len(partes) == 1 else f"{partes[1].strip()} {partes[0].strip()}".strip()

    @staticmethod
    def _inferir_genero(subjects: str) -> str:
        s = str(subjects).lower()
        regras = (
            ("Terror/gótico", ("horror", "gothic", "vampire", "ghost")),
            ("Mistério/policial", ("detective", "mystery", "crime", "police")),
            ("Ficção científica/fantasia", ("science fiction", "fantasy", "time travel", "space")),
            ("Romance", ("love stories", "courtship", "romance")),
            ("Guerra", ("war", "military", "soldiers")),
            ("Aventura", ("adventure", "pirates", "sea")),
            ("Ficção histórica", ("historical", "napoleonic")),
            ("Literatura infantil/juvenil", ("juvenile", "children")),
            ("Poesia", ("poetry", "poems")),
            ("Humor", ("humor", "comedy")),
            ("Faroeste", ("westerns", "western")),
        )
        for genero, palavras in regras:
            if any(p in s for p in palavras):
                return genero
        return "Ficção geral"

    def __len__(self) -> int:
        return len(self.df)

    def resumo(self) -> Dict:
        return {
            "n_livros": len(self.df),
            "n_generos": len(self.contagem_por_genero()),
        }

    def contagem_por_genero(self) -> Dict[str, int]:
        return self.df["genero"].value_counts().to_dict()

    def localizar(self, texto: str) -> int:
        alvo = str(texto).strip().lower()
        if not alvo:
            raise LivroNaoEncontradoError("Livro não informado.")
        exacta = self.df.index[self.df["title"].str.lower().eq(alvo)].tolist()
        if exacta:
            return int(exacta[0])
        por_id = self.df.index[self.df["book_id"].eq(alvo)].tolist()
        if por_id:
            return int(por_id[0])
        parcial = self.df.index[self.df["title"].str.lower().str.contains(re.escape(alvo), regex=True)].tolist()
        if len(parcial) == 1:
            return int(parcial[0])
        if len(parcial) > 1:
            candidatos = self.df.iloc[parcial].copy()
            candidatos["_comprimento"] = candidatos["title"].str.len()
            candidatos = candidatos.sort_values("_comprimento")
            titulos = candidatos["title"].str.lower().tolist()
            iniciam_com_alvo = [
                int(indice) for indice in candidatos.index
                if str(candidatos.at[indice, "title"]).lower().startswith(alvo)
            ]
            if iniciam_com_alvo:
                return iniciam_com_alvo[0]
            nomes = ", ".join(candidatos["title"].head(5).tolist())
            raise LivroNaoEncontradoError(
                f"Encontrei mais de um livro parecido com '{texto}' ({nomes}). "
                "Tente o título em inglês, como está no Gutenberg."
            )
        raise LivroNaoEncontradoError(f"Não encontrei '{texto}' no catálogo.")

    def sugerir_titulos(self, trecho: str) -> List[Dict[str, str]]:
        trecho = str(trecho).strip().lower()
        if not trecho:
            return []
        mask = self.df["title"].str.lower().str.contains(re.escape(trecho), regex=True)
        return [
            {"book_id": str(r.book_id), "title": str(r.title), "author": str(r.autor_legivel)}
            for r in self.df[mask].head(8).itertuples()
        ]
