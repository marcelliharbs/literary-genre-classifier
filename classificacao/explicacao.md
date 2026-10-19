RESUMO DO NOTEBOOK:

1) Pega a coluna 'text_final', 'summary' ou 'trecho_1_clean' (considerando essa lógica de preferência, ou seja se 'text_final' não está preenchida ele pega a 'summary' e assim por diante).

2) O método 'identificar_genero(subjects)' pega a coluna 'subjects' para definir o gênero.

3) Separa uma parte dos livros pra treinamento (com gênero classificado) e outra pra teste (sem gênero classificado).

4) Usam o classificador 'LogisticRegression' que recebe:

- BOW: uma matriz com a quantidade de vezes que cada palavra aparece nos livros.

- TF-IDF: uma matriz com pesos das palavras, considerando sua importância nos textos.

- Word2Vec: um vetor que representa cada livro, calculado pela média dos vetores das palavras.

- BERT: o texto do resumo de cada livro é convertido em um vetor chamado embedding, que possui 384 valores numéricos no modelo all-MiniLM-L6-v2.

O objetivo de todos é aprender com os dados de treinamento quais padrões textuais estão associados aos gêneros.

5) Compara o gênero previsto com o rótulo de referência. No final de cada arquivo tem a acurácia (quantos acertou de todos os livros) e o F1 (se foi bem em vários gêneros ou nn).


TOP 4:

1) BOW

Acurácia: 0.737
F1 macro: 0.500

2) TF-IDF

Acurácia: 0.711
F1 macro: 0.484

3) BERT

Acurácia: 0.684
F1 macro: 0.503

4) Word2Vec:

Acurácia: 0.158
F1 macro: 0.112


OBS: SE QUISER RODAR DNV TEM Q MUDAR O CAMINHO DO ARQUIVO CSV PQ ELE N ESTÁ CONSIDERANDO A PASTA