"""Gera ``amostra.csv``: um CSV pequeno **só para testes automatizados**.

As sinopses foram escritas à mão (resumos curtos de obras em domínio público) e não
são os dados reais do projeto. O arquivo imita as colunas do ``gutenberg_books.csv``
(``book_id, title, author, subjects, summary, text_final`` …).

Uso: ``python tests/fixtures/gerar_amostra.py``
"""
import re
from pathlib import Path

import pandas as pd

STOPWORDS = set(
    "a an and are as at be but by for from has have he her his in is it its of on or she that the their "
    "them they this to was were who will with after before into over while when where which whose not no "
    "can must also only one two three more most other than then there these those so such very".split()
)

# (book_id, título, autor, assuntos, resumo)
LIVROS = [
    ("1342", "Pride and Prejudice", "Austen, Jane, 1775-1817", "Love stories | Courtship -- Fiction | England -- Fiction",
     "A novel about Elizabeth Bennet, whose family faces pressure to marry well. Her prejudice against the proud Mr. Darcy slowly turns into love and marriage."),
    ("42671", "Pride and Prejudice", "Austen, Jane, 1775-1817", "Love stories | Courtship -- Fiction",
     "A novel about Elizabeth Bennet, whose family faces pressure to marry well. Her prejudice against the proud Mr. Darcy slowly turns into love and marriage."),
    ("158", "Emma", "Austen, Jane, 1775-1817", "Love stories | Matchmaking -- Fiction",
     "Emma Woodhouse enjoys matchmaking in her small English village, but her misunderstandings about love and marriage cause trouble before she finds happiness."),
    ("161", "Sense and Sensibility", "Austen, Jane, 1775-1817", "Love stories | Sisters -- Fiction",
     "Two sisters with different temperaments search for love and marriage while their family faces financial hardship after the death of their father."),
    ("345", "Dracula", "Stoker, Bram, 1847-1912", "Horror fiction | Vampires -- Fiction | Gothic fiction",
     "A gothic horror novel in which a solicitor travels to Transylvania and discovers that Count Dracula is a vampire who plans to move to England."),
    ("10007", "Carmilla", "Le Fanu, Joseph Sheridan, 1814-1873", "Vampire fiction | Gothic fiction",
     "A young woman living in an Austrian castle befriends a mysterious visitor. A gothic tale of vampires, nightmares and a strange illness."),
    ("84", "Frankenstein; or, the modern prometheus", "Shelley, Mary Wollstonecraft, 1797-1851", "Science fiction | Horror fiction | Gothic fiction",
     "A scientist creates a living being from dead matter and abandons it. The creature seeks revenge in a gothic horror novel about ambition and responsibility."),
    ("43", "The strange case of Dr. Jekyll and Mr. Hyde", "Stevenson, Robert Louis, 1850-1894", "Horror fiction | Psychological fiction | Gothic fiction",
     "A respected London doctor drinks a potion that releases a violent double. A gothic horror story about the dark side of human nature."),
    ("601", "The Monk: A Romance", "Lewis, M. G. (Matthew Gregory), 1775-1818", "Gothic fiction | Horror fiction",
     "A gothic novel about a pious monk who is tempted by a demon and falls into crime, horror and damnation inside a haunted monastery."),
    ("2600", "War and Peace", "Tolstoy, Leo, graf, 1828-1910", "War stories | Historical fiction | Napoleonic Wars, 1800-1815 -- Fiction",
     "An epic novel of the Napoleonic wars that follows Russian aristocratic families through battles, diplomacy, politics, love and the fall of empires."),
    ("73", "The Red Badge of Courage: An Episode of the American Civil War", "Crane, Stephen, 1871-1900", "War stories | United States -- History -- Civil War, 1861-1865 -- Fiction",
     "A young soldier in the American Civil War runs from his first battle, then struggles with fear, shame and courage on the battlefield."),
    ("75201", "A farewell to arms", "Hemingway, Ernest, 1899-1961", "War stories | Love stories | World War, 1914-1918 -- Fiction",
     "An American ambulance driver falls in love with a nurse during the First World War as the army retreats in Italy."),
    ("1931", "The Zeppelin's Passenger", "Oppenheim, E. Phillips (Edward Phillips), 1866-1946", "War stories | Spy stories | World War, 1914-1918 -- Fiction",
     "A spy thriller of the First World War in which a diplomat and a secret agent uncover a plot connected to a German zeppelin raid on England."),
    ("53874", "Under the Red Dragon: A Novel", "Grant, James, 1822-1887", "Historical fiction | Military fiction | Crimean War, 1853-1856 -- Fiction",
     "A military adventure set during the Crimean War, following a young officer through camp life, battle and romance."),
    ("25132", "The Candidate: A Political Romance", "Hunt, Marion", "Political fiction | Love stories",
     "A political novel about an election campaign, party intrigue, corruption and the personal cost of ambition for a candidate and his family."),
    ("79", "Terminal Compromise", "Schwartau, Winn", "Didactic fiction | Terrorism -- Fiction",
     "A thriller about cyber terrorism and national security in which hackers threaten the government and the banking system."),
    ("36", "The war of the worlds", "Wells, H. G. (Herbert George), 1866-1946", "Science fiction | War stories | Martians -- Fiction",
     "Martians invade England with giant machines and destroy cities. A science fiction novel of invasion, panic and survival."),
    ("35", "The Time Machine", "Wells, H. G. (Herbert George), 1866-1946", "Science fiction | Time travel -- Fiction | Dystopias",
     "A scientist builds a machine to travel through time and discovers a distant future where humanity has split into two strange species."),
    ("83", "From the Earth to the moon; and, round the moon", "Verne, Jules, 1828-1905", "Science fiction | Space flight to the moon -- Fiction",
     "Members of a gun club build a giant cannon to launch a projectile with travellers to the moon, in a science fiction adventure about space exploration."),
    ("18857", "A Journey to the Centre of the Earth", "Verne, Jules, 1828-1905", "Science fiction | Adventure stories | Earth -- Fiction",
     "A professor, his nephew and a guide descend into a volcano and travel to the centre of the earth, meeting prehistoric creatures underground."),
    ("50290", "Space Station 1", "Long, Frank Belknap, 1901-1994", "Science fiction | Love stories",
     "In the near future a scientist on an orbiting space station faces a conspiracy, an impostor and a dangerous experiment in physics."),
    ("1661", "The Adventures of Sherlock Holmes", "Doyle, Arthur Conan, 1859-1930", "Detective and mystery stories | Short stories",
     "A collection of short stories in which the detective Sherlock Holmes and Dr. Watson solve strange crimes and mysteries in Victorian London."),
    ("244", "A Study in Scarlet", "Doyle, Arthur Conan, 1859-1930", "Detective and mystery stories",
     "Sherlock Holmes investigates a murder in London and the case leads to a story of revenge among settlers in America."),
    ("2852", "The Hound of the Baskervilles", "Doyle, Arthur Conan, 1859-1930", "Detective and mystery stories | Mystery fiction",
     "The detective Sherlock Holmes investigates the legend of a monstrous hound that haunts a family estate on the English moors."),
    ("65238", "The Secret of Chimneys", "Christie, Agatha, 1890-1976", "Detective and mystery stories | Mystery fiction",
     "A murder at a country house, missing jewels and a political conspiracy challenge a young adventurer and Scotland Yard."),
    ("1155", "The Secret Adversary", "Christie, Agatha, 1890-1976", "Detective and mystery stories | Spy stories",
     "Two young friends become amateur detectives to solve a mystery about a missing girl, secret papers and a criminal mastermind."),
    ("120", "Treasure Island", "Stevenson, Robert Louis, 1850-1894", "Adventure stories | Pirates -- Fiction | Sea stories",
     "A boy finds a treasure map and sails with pirates to a tropical island, where mutiny, danger and a one-legged cook threaten the voyage."),
    ("2701", "Moby Dick; Or, The Whale", "Melville, Herman, 1819-1891", "Adventure stories | Sea stories | Whaling -- Fiction",
     "A sailor narrates the voyage of a whaling ship whose captain is obsessed with taking revenge on a great white whale."),
    ("215", "The Call of the Wild", "London, Jack, 1876-1916", "Adventure stories | Dogs -- Fiction",
     "A domestic dog is stolen and sold as a sled dog in the Alaskan gold rush, where he returns to wild instinct in the frozen wilderness."),
    ("1300", "Riders of the Purple Sage", "Grey, Zane, 1872-1939", "Western stories | Cowboys -- Fiction",
     "A cowboy and a woman rancher defend their land in Utah against a ruthless group of outlaws and religious leaders in the old west."),
    ("768", "Wuthering Heights", "Brontë, Emily, 1818-1848", "Romantic fiction | Revenge -- Fiction | Psychological fiction",
     "A wild and passionate love between Heathcliff and Catherine on the Yorkshire moors turns into revenge that destroys two families."),
    ("1260", "Jane Eyre: An Autobiography", "Brontë, Charlotte, 1816-1855", "Love stories | Bildungsromans | Governesses -- Fiction",
     "An orphan grows up to become a governess and falls in love with her employer, Mr. Rochester, who hides a terrible secret in his house."),
    ("145", "Middlemarch", "Eliot, George, 1819-1880", "Domestic fiction | Provincial -- Fiction",
     "A portrait of life in an English provincial town, following marriages, ambition, medicine and political reform in the years before 1832."),
    ("2554", "Crime and Punishment", "Dostoyevsky, Fyodor, 1821-1881", "Psychological fiction | Crime fiction",
     "A poor student in Saint Petersburg commits a murder and is tormented by guilt while a detective closes in. A novel about morality and religion."),
    ("514", "Little Women", "Alcott, Louisa May, 1832-1888", "Bildungsromans | Domestic fiction | Juvenile fiction",
     "Four sisters grow up in New England during the Civil War, facing poverty, family love, work, marriage and their dreams for the future."),
    ("16", "Peter Pan", "Barrie, J. M. (James Matthew), 1860-1937", "Fantasy fiction | Juvenile fiction",
     "A boy who refuses to grow up takes three children to Neverland, where they fight pirates and meet fairies and lost boys."),
    ("11", "Alice's Adventures in Wonderland", "Carroll, Lewis, 1832-1898", "Fantasy fiction | Juvenile fiction",
     "A girl falls down a rabbit hole into a strange world of talking animals, a mad tea party and a queen who shouts about cutting off heads."),
    ("500", "The Adventures of Pinocchio", "Collodi, Carlo, 1826-1890", "Fantasy fiction | Children's stories",
     "A wooden puppet comes to life and learns, through many mistakes and adventures, to be honest, brave and a good son."),
    ("46", "A Christmas Carol in Prose; Being a Ghost Story of Christmas", "Dickens, Charles, 1812-1870", "Ghost stories | Christmas stories",
     "A miserly old man is visited by three ghosts on Christmas Eve who show him his life and teach him generosity and kindness."),
    ("996", "Don Quixote", "Cervantes Saavedra, Miguel de, 1547-1616", "Humorous stories | Romances",
     "An old gentleman who has read too many books of chivalry believes he is a knight and travels with his servant Sancho Panza in comic adventures."),
    ("76", "Adventures of Huckleberry Finn", "Twain, Mark, 1835-1910", "Humorous stories | Adventure stories | Slavery -- Fiction",
     "A boy and an escaped slave float down the Mississippi river on a raft, facing con men, feuds and questions about society and freedom."),
    ("5001", "Essays on Government and Duty", "Anonymous", "Political science -- Essays",
     "Essays about government, civil duty, law and religion that argue for freedom, morality and the responsibility of citizens in politics."),
    ("5002", "Sermons on Faith and Morality", "Anonymous", "Sermons | Christian life",
     "A collection of sermons about religion, faith, moral duty and the doubts of believers in the nineteenth century."),
]


def preprocessar(texto: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", texto.lower())
    return " ".join(t for t in tokens if t not in STOPWORDS)


def main() -> None:
    linhas = []
    for book_id, titulo, autor, assuntos, resumo in LIVROS:
        linhas.append({
            "book_id": book_id, "title": titulo, "author": autor, "language": "English",
            "subjects": assuntos, "release_date": "", "ebook_url": f"https://www.gutenberg.org/ebooks/{book_id}",
            "summary": resumo, "text_final": preprocessar(f"{titulo} {autor} {resumo}"),
        })
    destino = Path(__file__).with_name("amostra.csv")
    pd.DataFrame(linhas).to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"{len(linhas)} livros gravados em {destino}")


if __name__ == "__main__":
    main()