from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass
class ConfiguracaoApp:
    caminho_csv: str
    coluna_texto: str = "text_final"
    coluna_bert: str = "summary"
    modelos: Tuple[str, ...] = ("bow", "tfidf")
    hibrido: Tuple[str, ...] = ("bow", "tfidf")
    rrf_k: int = 60
    nome_modelo_bert: str = "sentence-transformers/all-MiniLM-L6-v2"
    diretorio_cache: str = "model_cache"
    n_clusters: int = 8

    @classmethod
    def padrao(cls) -> "ConfiguracaoApp":
        raiz = Path(__file__).resolve().parent.parent
        return cls(caminho_csv=str(raiz / "gutenberg_books.csv"))
