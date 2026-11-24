from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


@dataclass
class ProjecaoMapa:
    coordenadas: np.ndarray
    clusters: np.ndarray
    variancia_explicada: float
    silhouette: Optional[float]


class ProjetorMapa:
    def __init__(self, recomendador, n_clusters: int = 8) -> None:
        self.recomendador = recomendador
        self.n_clusters = n_clusters
        self._cache = {}

    def projetar(self, modelo: str) -> ProjecaoMapa:
        if modelo in self._cache:
            return self._cache[modelo]
        rep = self.recomendador.representacoes[modelo]
        matrix = rep.matrix.toarray() if hasattr(rep.matrix, "toarray") else rep.matrix
        n_clusters = min(self.n_clusters, len(matrix))
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(matrix)
        clusters = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(matrix)
        silhouette = silhouette_score(matrix, clusters) if len(set(clusters)) > 1 and len(matrix) > n_clusters else None
        proj = ProjecaoMapa(coords, clusters, float(pca.explained_variance_ratio_.sum()), silhouette)
        self._cache[modelo] = proj
        return proj

    def posicao_consulta(self, modelo: str, consulta: str):
        rep = self.recomendador.representacoes[modelo]
        if rep.vectorizer is None:
            return None
        matrix = rep.matrix.toarray() if hasattr(rep.matrix, "toarray") else rep.matrix
        vetor = rep.vectorizer.transform([consulta]).toarray()
        if not np.any(vetor):
            return None
        pca = PCA(n_components=2, random_state=42).fit(matrix)
        coordenada = pca.transform(vetor)
        return float(coordenada[0, 0]), float(coordenada[0, 1])
