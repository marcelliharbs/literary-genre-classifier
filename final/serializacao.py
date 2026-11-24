from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd


class SerializadorResultados:
    @staticmethod
    def termos(titulo: str, consulta: str = "") -> List[str]:
        stop = set("a an and are as at be but by for from has have he her his in is it its of on or she that the their them they this to was were who will with a ao as com da de do dos e em na no os uma um".split())
        texto = re.findall(r"[A-Za-zÀ-ÿ]+", f"{titulo} {consulta}".lower())
        return [t for t in texto if len(t) > 3 and t not in stop][:6]

    @classmethod
    def itens(cls, tabela: pd.DataFrame) -> List[Dict]:
        itens = []
        for pos, row in enumerate(tabela.to_dict("records"), 1):
            termos = row.get("termos")
            if not isinstance(termos, list):
                termos = cls.termos(str(row.get("title", "")))
            itens.append({
                "posicao": pos,
                "book_id": str(row.get("book_id", "")),
                "titulo": str(row.get("title", "")),
                "autor": row.get("autor_legivel") or None,
                "genero": row.get("genero") or None,
                "score": round(float(row.get("score", 0)), 5),
                "termos": termos[:10],
            })
        return itens
