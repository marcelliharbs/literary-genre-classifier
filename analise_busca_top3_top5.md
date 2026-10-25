# Análise da recuperação de livros: top-3 e top-5

## 1. Objetivo e método

Foi analisada a consulta **`war politics`** já executada no notebook `comparacao_modelos.ipynb`. A consulta é igual para as quatro representações: **BoW, TF-IDF, Word2Vec e BERT/MiniLM**. Os títulos, as posições e as similaridades abaixo são os resultados registrados no notebook.

A consulta `war politics` é ambígua: pode significar livros sobre guerra, sobre política ou sobre a relação entre ambas. Para tornar a avaliação explícita, foi adotada esta escala:

- **2 — relevância direta:** o livro conecta claramente guerra/conflito militar e dimensões político-estratégicas, atendendo diretamente à combinação de temas sugerida pela consulta.
- **1 — relevância parcial:** o livro aborda claramente apenas uma das dimensões (guerra ou política), ou tem uma conexão indireta com a outra.
- **0 — irrelevante:** não há conexão temática clara com guerra ou política.

Como teste conservador de qualidade, “precisão direta @k” considera relevante apenas a nota **2**. A média normalizada de relevância é a soma das notas dividida por `2 × k`, variando entre 0 e 1. Essa avaliação é subjetiva e deve ser interpretada como um estudo de caso; consultas adicionais e avaliadores independentes tornariam o resultado mais robusto.

## 2. Resultados observados

### 2.1 BoW

| Posição | Documento | Similaridade | Relevância | Justificativa breve |
|---:|---|---:|:---:|---|
| 1 | [The Red Badge of Courage](https://www.gutenberg.org/ebooks/73) | 0,232845 | 1 | Guerra Civil é central, mas a dimensão política não é o foco principal. |
| 2 | [The Zeppelin's Passenger](https://www.gutenberg.org/ebooks/1931) | 0,226455 | 2 | A narrativa envolve a Primeira Guerra Mundial e espionagem. |
| 3 | [A Farewell to Arms](https://www.gutenberg.org/ebooks/75201) | 0,196116 | 1 | A guerra é central; a narrativa também enfatiza a relação amorosa e a experiência pessoal. |
| 4 | [War and Peace](https://www.gutenberg.org/ebooks/2600) | 0,184115 | 2 | Combina conflitos militares com poder, diplomacia e contexto político-histórico. |
| 5 | [Under the Red Dragon](https://www.gutenberg.org/ebooks/53874) | 0,173785 | 1 | Ambientado no contexto da Guerra da Crimeia, mas com forte componente de romance e vida militar. |

**Top-3:** 1 de 3 documentos com relevância direta; média normalizada de relevância = **0,67**.  
**Top-5:** 2 de 5 documentos com relevância direta; média normalizada = **0,70**.

**Análise:** o BoW recuperou documentos claramente ligados à guerra. Entretanto, os três primeiros resultados não cobrem com a mesma força a dimensão política da consulta. A abordagem por contagem de palavras pode responder bem quando termos da consulta aparecem no texto, mas não diferencia necessariamente os sentidos ou a relação entre “war” e “politics”.

### 2.2 TF-IDF

| Posição | Documento | Similaridade | Relevância | Justificativa breve |
|---:|---|---:|:---:|---|
| 1 | [The Zeppelin's Passenger](https://www.gutenberg.org/ebooks/1931) | 0,151105 | 2 | Guerra e espionagem são componentes importantes. |
| 2 | [The Red Badge of Courage](https://www.gutenberg.org/ebooks/73) | 0,148307 | 1 | Guerra é central; dimensão política menos direta. |
| 3 | [A Farewell to Arms](https://www.gutenberg.org/ebooks/75201) | 0,126183 | 1 | Forte relação com guerra, menor aderência ao aspecto político. |
| 4 | [War and Peace](https://www.gutenberg.org/ebooks/2600) | 0,113040 | 2 | Relaciona guerras e contexto político-histórico. |
| 5 | [Under the Red Dragon](https://www.gutenberg.org/ebooks/53874) | 0,111778 | 1 | Relação com guerra e ambiente militar, mas foco também romântico. |

**Top-3:** 1 de 3 documentos com relevância direta; média normalizada = **0,67**.  
**Top-5:** 2 de 5 documentos com relevância direta; média normalizada = **0,70**.

**Análise:** TF-IDF retornou os mesmos cinco livros do BoW, mas trocou a ordem dos dois primeiros. A ponderação dos termos mudou o ranking, sem melhorar substancialmente a variedade dos resultados. Isso mostra que, nesta consulta, o ajuste do peso das palavras afetou a ordem, mas os dois métodos continuam muito dependentes da correspondência lexical.

### 2.3 Word2Vec

| Posição | Documento | Similaridade | Relevância | Justificativa breve |
|---:|---|---:|:---:|---|
| 1 | [A Farewell to Arms](https://www.gutenberg.org/ebooks/75201) | 0,935101 | 1 | Guerra é central, mas política não é o foco principal. |
| 2 | [Mrs Dalloway](https://www.gutenberg.org/ebooks/71865) | 0,917591 | 1 | Há uma conexão com trauma de um veterano e o pós-guerra, sem a guerra como enredo principal. |
| 3 | [Middlemarch](https://www.gutenberg.org/ebooks/145) | 0,908960 | 1 | Trata de reforma política e mudança social, mas não de guerra. |
| 4 | [The Treasure of Pearls](https://www.gutenberg.org/ebooks/46276) | 0,905214 | 0 | A descrição destaca aventura e romance, sem ligação clara com guerra ou política como tema central. |
| 5 | [The Raft](https://www.gutenberg.org/ebooks/50498) | 0,902937 | 0 | O foco é amor, casamento e expectativas sociais; pouca relação com a consulta. |

**Top-3:** 0 de 3 documentos com relevância direta; média normalizada = **0,50**.  
**Top-5:** 0 de 5 documentos com relevância direta; média normalizada = **0,30**.

**Análise:** Word2Vec trouxe algumas associações temáticas indiretas, mas os resultados nas posições 4 e 5 se afastam da intenção da consulta. A média dos vetores das palavras de um livro pode perder informações sobre a relação entre conceitos e sobre o contexto em que as palavras aparecem. A similaridade alta (cerca de 0,90) não deve ser interpretada como garantia de relevância: os valores estão numa representação diferente das outras e não são diretamente comparáveis.

### 2.4 BERT / MiniLM

| Posição | Documento | Similaridade | Relevância | Justificativa breve |
|---:|---|---:|:---:|---|
| 1 | [The War of the Worlds](https://www.gutenberg.org/ebooks/36) | 0,336141 | 1 | Invasão e conflito são centrais, mas o contexto é ficção científica, não política humana. |
| 2 | [Terminal Compromise](https://www.gutenberg.org/ebooks/79) | 0,306676 | 2 | Aborda segurança computacional, terrorismo cibernético e ameaças à segurança nacional. |
| 3 | [War and Peace](https://www.gutenberg.org/ebooks/2600) | 0,296046 | 2 | Relação direta com guerra e contexto político-histórico. |
| 4 | [Under the Red Dragon](https://www.gutenberg.org/ebooks/53874) | 0,252160 | 1 | Guerra e vida militar são relevantes, mas a dimensão política é menos direta. |
| 5 | [The Candidate: A Political Romance](https://www.gutenberg.org/ebooks/25132) | 0,246063 | 1 | A política é central, mas a guerra não parece ser o tema principal. |

**Top-3:** 2 de 3 documentos com relevância direta; média normalizada = **0,83**.  
**Top-5:** 2 de 5 documentos com relevância direta; média normalizada = **0,70**.

**Análise:** MiniLM foi o mais forte no top-3 nesta avaliação, porque trouxe um livro sobre segurança e terrorismo cibernético e outro sobre guerra e contexto político. O resultado em primeiro lugar é relacionado a conflito, mas não necessariamente ao tema político pretendido. A representação semântica parece ampliar a recuperação para ideias relacionadas, o que pode ajudar ou prejudicar conforme a intenção do usuário.

## 3. Comparação resumida

| Representação | Relevância direta no top-3 | Relevância direta no top-5 | Média normalizada top-3 | Média normalizada top-5 |
|---|---:|---:|---:|---:|
| BoW | 1/3 (33%) | 2/5 (40%) | 0,67 | 0,70 |
| TF-IDF | 1/3 (33%) | 2/5 (40%) | 0,67 | 0,70 |
| Word2Vec | 0/3 (0%) | 0/5 (0%) | 0,50 | 0,30 |
| BERT / MiniLM | 2/3 (67%) | 2/5 (40%) | 0,83 | 0,70 |

A “relevância direta” usa o limiar de nota 2 na escala manual; os livros com nota 1 têm relação parcial porque abordam principalmente apenas uma das dimensões ou apresentam uma conexão indireta. A média normalizada mantém as notas parciais na avaliação.

## 4. Resposta às perguntas do trabalho

### Os resultados são utilizáveis em um contexto real?

**Como protótipo de busca exploratória, sim; como mecanismo de busca confiável sem revisão, ainda não.** BoW e TF-IDF foram consistentes ao recuperar livros sobre guerra, mas deram prioridade à dimensão militar, sem garantir que o aspecto político fosse igualmente atendido. MiniLM trouxe resultados mais diversos e teve melhor top-3 nesta consulta, embora parte dessa diversidade também produza correspondências indiretas. Word2Vec trouxe resultados menos aderentes no fim do ranking.

A avaliação cobre apenas uma consulta (`war politics`) e aplica notas manuais. Portanto, não é suficiente para declarar um vencedor geral entre as representações. O resultado pode mudar com outras consultas, com o critério de relevância e com a qualidade dos resumos presentes no dataset.

### Como poderiam ser combinados ou melhorados?

1. **Busca híbrida:** combinar TF-IDF/BoW (correspondência lexical) com MiniLM (semelhança semântica). Uma opção é Reciprocal Rank Fusion (RRF), que combina posições nos rankings e evita somar diretamente pontuações que estão em escalas diferentes.
2. **Clarificar ou expandir a consulta:** tratar separadamente a intenção por guerra e por política; acrescentar sinônimos como `conflict`, `military`, `government`, `diplomacy`, `political power` e `warfare`, conforme a intenção.
3. **Reordenar os resultados:** usar um reranker semântico sobre os primeiros 10–20 candidatos recuperados pelo método híbrido.
4. **Avaliar com mais consultas:** repetir o experimento para consultas de amor/romance, ficção científica/futuro e aventura/guerra. Julgar relevância com a mesma escala, idealmente com duas pessoas, e calcular Precision@3, Precision@5 e NDCG@5.
5. **Melhorar os dados:** verificar se os campos textuais usados na busca contêm sinopses suficientes e consistentes. O ranking não pode recuperar detalhes que não estejam presentes no texto indexado.

Não comparar diretamente os valores de similaridade entre métodos. Por exemplo, `0,93` no Word2Vec não é automaticamente melhor que `0,33` no MiniLM; cada método calcula a similaridade no seu próprio espaço vetorial.

## 5. Conclusão

Nesta consulta, BoW e TF-IDF encontraram listas muito semelhantes, predominantemente relacionadas à guerra. MiniLM apresentou a melhor composição de resultados no top-3 de acordo com a rubrica adotada, pois atendeu de forma mais direta às dimensões de guerra e política. Word2Vec teve os resultados menos aderentes no top-5. Ainda assim, a evidência não permite afirmar que MiniLM sempre será o melhor: foram avaliados apenas uma consulta e julgamentos manuais. Uma busca híbrida, uma avaliação em várias consultas e um conjunto de relevância validado são os próximos passos mais sólidos.

## 6. Fontes para conferir a relevância dos documentos

As descrições e os metadados dos títulos foram conferidos nas páginas do Project Gutenberg: [The Red Badge of Courage](https://www.gutenberg.org/ebooks/73), [The Zeppelin's Passenger](https://www.gutenberg.org/ebooks/1931), [A Farewell to Arms](https://www.gutenberg.org/ebooks/75201), [War and Peace](https://www.gutenberg.org/ebooks/2600), [Under the Red Dragon](https://www.gutenberg.org/ebooks/53874), [Mrs Dalloway](https://www.gutenberg.org/ebooks/71865), [Middlemarch](https://www.gutenberg.org/ebooks/145), [The Treasure of Pearls](https://www.gutenberg.org/ebooks/46276), [The Raft](https://www.gutenberg.org/ebooks/50498), [The War of the Worlds](https://www.gutenberg.org/ebooks/36), [Terminal Compromise](https://www.gutenberg.org/ebooks/79) e [The Candidate](https://www.gutenberg.org/ebooks/25132).
