import pandas as pd


class AvaliadorPorGenero:
    def __init__(self, recomendador) -> None:
        self.recomendador = recomendador

    def avaliar(self) -> pd.DataFrame:
        linhas = []
        for modelo in (*self.recomendador.modelos, "hibrido"):
            linhas.append({
                "modelo": modelo,
                "n_consultas": len(self.recomendador.catalogo),
                "P@3": None,
                "P@5": None,
                "MRR": None,
                "observacao": "Avaliação registrada no notebook; recalcular o resultado completo requer o conjunto de consultas original.",
            })
        return pd.DataFrame(linhas)
