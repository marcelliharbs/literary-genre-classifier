"""Resultados já obtidos nos notebooks do projeto, exibidos na aba "Resultados".

Os números abaixo foram **copiados das saídas dos notebooks** (não são recalculados
pela aplicação). Cada bloco informa o notebook de origem. A aba também permite
recalcular a avaliação por gênero com o CSV carregado.
"""
from __future__ import annotations

from typing import Any, Dict


class ResultadosRegistrados:
    """Tabelas e exemplos de execução registrados nos notebooks."""

    # recomendacao_livros.ipynb, seção 4 (218 livros com gênero conhecido)
    RECOMENDACAO_POR_GENERO = {
        "fonte": "recomendacao_livros.ipynb — seção 4 (Precision@k e MRR por gênero)",
        "criterio": "Um resultado é relevante quando tem o mesmo gênero do livro de referência (rótulo por regras sobre 'subjects').",
        "colunas": ["modelo", "n_consultas", "P@3", "P@5", "MRR"],
        "linhas": [
            {"modelo": "bow", "n_consultas": 218, "P@3": 0.382, "P@5": 0.325, "MRR": 0.543},
            {"modelo": "tfidf", "n_consultas": 218, "P@3": 0.375, "P@5": 0.352, "MRR": 0.541},
            {"modelo": "word2vec", "n_consultas": 218, "P@3": 0.255, "P@5": 0.238, "MRR": 0.396},
            {"modelo": "bert", "n_consultas": 218, "P@3": 0.408, "P@5": 0.369, "MRR": 0.556},
            {"modelo": "tfidf+bert", "n_consultas": 218, "P@3": 0.442, "P@5": 0.400, "MRR": 0.598},
            {"modelo": "bow+tfidf+word2vec+bert", "n_consultas": 218, "P@3": 0.416, "P@5": 0.382, "MRR": 0.587},
            {"modelo": "acaso (baseline)", "n_consultas": 218, "P@3": 0.111, "P@5": 0.111, "MRR": None},
        ],
    }

    # comparacao_modelos.ipynb, seção "Classificação por modelo"
    CLASSIFICACAO_GENERO = {
        "fonte": "comparacao_modelos.ipynb — Classificação por modelo",
        "detalhes": "Regressão logística (class_weight='balanced'), 18 gêneros, 163 livros de treino e 55 de teste (divisão estratificada, semente 42).",
        "colunas": ["modelo", "acuracia", "f1_macro"],
        "linhas": [
            {"modelo": "TF-IDF", "acuracia": 0.618, "f1_macro": 0.405},
            {"modelo": "BERT", "acuracia": 0.473, "f1_macro": 0.322},
            {"modelo": "BoW", "acuracia": 0.582, "f1_macro": 0.301},
            {"modelo": "Word2Vec", "acuracia": 0.036, "f1_macro": 0.012},
        ],
    }

    # analise_busca_top3_top5.md
    AVALIACAO_MANUAL = {
        "fonte": "analise_busca_top3_top5.md — consulta 'war politics' (notebook comparacao_modelos.ipynb)",
        "escala": {
            "2": "relevância direta: conecta guerra/conflito militar e dimensão político-estratégica",
            "1": "relevância parcial: apenas uma das dimensões, ou conexão indireta",
            "0": "irrelevante",
        },
        "modelos": [
            {"modelo": "BoW", "itens": [
                ("The Red Badge of Courage", 0.232845, 1), ("The Zeppelin's Passenger", 0.226455, 2),
                ("A Farewell to Arms", 0.196116, 1), ("War and Peace", 0.184115, 2),
                ("Under the Red Dragon", 0.173785, 1)]},
            {"modelo": "TF-IDF", "itens": [
                ("The Zeppelin's Passenger", 0.151105, 2), ("The Red Badge of Courage", 0.148307, 1),
                ("A Farewell to Arms", 0.126183, 1), ("War and Peace", 0.113040, 2),
                ("Under the Red Dragon", 0.111778, 1)]},
            {"modelo": "Word2Vec", "itens": [
                ("A Farewell to Arms", 0.935101, 1), ("Mrs Dalloway", 0.917591, 1),
                ("Middlemarch", 0.908960, 1), ("The Treasure of Pearls", 0.905214, 0),
                ("The Raft", 0.902937, 0)]},
            {"modelo": "BERT / MiniLM", "itens": [
                ("The War of the Worlds", 0.336141, 1), ("Terminal Compromise", 0.306676, 2),
                ("War and Peace", 0.296046, 2), ("Under the Red Dragon", 0.252160, 1),
                ("The Candidate: A Political Romance", 0.246063, 1)]},
        ],
        "resumo": {
            "colunas": ["modelo", "direta_top3", "direta_top5", "media_top3", "media_top5"],
            "linhas": [
                {"modelo": "BoW", "direta_top3": "1/3", "direta_top5": "2/5", "media_top3": 0.67, "media_top5": 0.70},
                {"modelo": "TF-IDF", "direta_top3": "1/3", "direta_top5": "2/5", "media_top3": 0.67, "media_top5": 0.70},
                {"modelo": "Word2Vec", "direta_top3": "0/3", "direta_top5": "0/5", "media_top3": 0.50, "media_top5": 0.30},
                {"modelo": "BERT / MiniLM", "direta_top3": "2/3", "direta_top5": "2/5", "media_top3": 0.83, "media_top5": 0.70},
            ],
        },
        "ressalva": "Uma única consulta e notas manuais de uma só pessoa: serve como estudo de caso, não como prova de que um modelo seja sempre melhor.",
    }

    # recomendacao_livros.ipynb, seções 1 e 2
    EXEMPLOS = [
        {
            "titulo": "Consulta: war politics",
            "fonte": "recomendacao_livros.ipynb — seção 1",
            "entrada": "war politics",
            "colunas": [
                {"modelo": "BoW", "itens": ["The Red Badge of Courage", "The Zeppelin's Passenger", "A Farewell to Arms", "War and Peace", "Under the Red Dragon"]},
                {"modelo": "TF-IDF", "itens": ["The Zeppelin's Passenger", "The Red Badge of Courage", "A Farewell to Arms", "War and Peace", "Under the Red Dragon"]},
                {"modelo": "Word2Vec", "itens": ["A Farewell to Arms", "The Raft", "Love and Life: An Old Story…", "The Treasure of Pearls", "Torchy and Vee"]},
                {"modelo": "BERT", "itens": ["War and Peace", "The War of the Worlds", "The Candidate: A Political Romance", "Terminal Compromise", "The Girl Philippa"]},
                {"modelo": "Híbrido (TF-IDF + BERT)", "itens": ["War and Peace", "Under the Red Dragon", "A Farewell to Arms", "The Red Badge of Courage", "The Girl Philippa"]},
            ],
            "observacao": "BoW e TF-IDF devolvem os mesmos cinco livros em ordem diferente. No Word2Vec, os resultados depois do primeiro não têm relação evidente com o tema (The Raft e The Treasure of Pearls receberam nota 0 na avaliação manual). O híbrido coloca War and Peace em primeiro.",
        },
        {
            "titulo": "Livro parecido: Dracula",
            "fonte": "recomendacao_livros.ipynb — seção 2",
            "entrada": "Dracula",
            "colunas": [
                {"modelo": "TF-IDF", "itens": ["Carmilla", "The Strange Case of Dr. Jekyll and Mr. Hyde", "Frankenstein", "Northanger Abbey", "Wuthering Heights"]},
                {"modelo": "BERT", "itens": ["Carmilla", "The House on the Borderland", "Frankenstein", "The Mysteries of London, v. 4/4", "The Hand in the Dark"]},
                {"modelo": "Híbrido (TF-IDF + BERT)", "itens": ["Carmilla", "Frankenstein", "The House on the Borderland", "The Monk", "The Mysteries of Udolpho"]},
            ],
            "observacao": "Carmilla (vampiros, literatura gótica) é o primeiro em TF-IDF, BERT e híbrido.",
        },
        {
            "titulo": "Perfil: Dracula, Frankenstein e Jekyll",
            "fonte": "recomendacao_livros.ipynb — seção 3",
            "entrada": "gostei de Dracula, Frankenstein e Jekyll",
            "colunas": [
                {"modelo": "TF-IDF", "itens": ["Carmilla", "The Turn of the Screw", "The Monk", "The House on the Borderland", "The Mysteries of Udolpho"]},
                {"modelo": "BERT", "itens": ["The House on the Borderland", "A Study in Scarlet", "Unnatural Death", "Carmilla", "Metamorphosis"]},
                {"modelo": "Híbrido (TF-IDF + BERT)", "itens": ["The House on the Borderland", "Carmilla", "The Mysteries of Udolpho", "The Turn of the Screw", "The Monk"]},
            ],
            "observacao": "O perfil é a média dos vetores dos três livros. O BERT puro se afasta para romances policiais; o híbrido mantém o foco em terror e gótico.",
        },
    ]

    CONVERSA = {
        "fonte": "chatbot_livros.ipynb — seção 6",
        "mensagens": [
            {"autor": "pessoa", "texto": "oi"},
            {"autor": "bot", "texto": "Olá! Sou o chatbot de livros do Project Gutenberg. Me conte um tema, um gênero ou livros que você gostou. ('ajuda' mostra exemplos)"},
            {"autor": "pessoa", "texto": "quero um livro sobre guerra e política"},
            {"autor": "bot", "texto": "Sugestões (gênero: Guerra): 1. War and Peace — Leo Tolstoy · 2. The Red Badge of Courage — Stephen Crane · 3. The Zeppelin's Passenger — E. Phillips Oppenheim · 4. A Farewell to Arms — Ernest Hemingway · 5. The Girl Philippa"},
        ],
    }

    @classmethod
    def como_dict(cls) -> Dict[str, Any]:
        """Estrutura única enviada ao navegador."""
        manual = dict(cls.AVALIACAO_MANUAL)
        manual["modelos"] = [
            {"modelo": m["modelo"],
             "itens": [{"titulo": t, "similaridade": s, "nota": n} for t, s, n in m["itens"]]}
            for m in cls.AVALIACAO_MANUAL["modelos"]
        ]
        return {
            "recomendacao_por_genero": cls.RECOMENDACAO_POR_GENERO,
            "classificacao_genero": cls.CLASSIFICACAO_GENERO,
            "avaliacao_manual": manual,
            "exemplos": cls.EXEMPLOS,
            "conversa": cls.CONVERSA,
        }