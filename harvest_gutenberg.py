import os
import re
import time
import zipfile
import io
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURAÇÕES ---
START_URL = "https://www.gutenberg.org/robot/harvest?filetypes[]=html"
OUTPUT_DIR = "data/gutenberg_html"
DELAY_SECONDS = 2.0  # Pausa obrigatória exigida pelas regras do Gutenberg

HEADERS = {
    "User-Agent": (
        "FURB-PLN-AcademicProject/2.0 "
        "(academic research; contact: jectrevisol@furb.br, mrharbs@furb.br, moplgalvao@furb.br)"
    )
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_zip_links_and_next_page(url: str):
    """
    Lê a página de harvest e retorna uma tupla: (lista_de_links_zip, url_proxima_pagina)
    """
    logging.info(f"Acessando harvest: {url}")
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    
    zip_links = []
    next_page_url = None

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        text = anchor.get_text(strip=True)

        # Captura links de arquivos .zip
        if href.endswith(".zip"):
            zip_links.append(href)
        # Captura a próxima página de resultados
        elif "Next Page" in text or "offset=" in href:
            next_page_url = urljoin("https://www.gutenberg.org/robot/", href)

    return zip_links, next_page_url


def download_and_extract_books(max_books: int = 20):
    """
    Baixa os arquivos .zip e extrai os HTMLs para a pasta local.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    current_url = START_URL
    downloaded_count = 0

    while current_url and downloaded_count < max_books:
        zip_links, next_url = get_zip_links_and_next_page(current_url)

        for zip_url in zip_links:
            if downloaded_count >= max_books:
                break

            # Define o nome do arquivo final baseado no ID (ex: 10084-h.zip -> 10084-h.html)
            zip_filename = zip_url.split("/")[-1]
            base_name = zip_filename.replace(".zip", "")
            target_html_path = os.path.join(OUTPUT_DIR, f"{base_name}.html")

            # Evita re-download se o HTML já estiver extraído
            if os.path.exists(target_html_path):
                logging.info(f"[CACHE LOCAL] Arquivo já extraído: {base_name}.html")
                continue

            try:
                logging.info(f"Baixando ({downloaded_count + 1}/{max_books}): {zip_url}")
                res = requests.get(zip_url, headers=HEADERS, timeout=30)
                
                if res.status_code == 200:
                    # Descompacta diretamente em memória sem precisar salvar o .zip temporário
                    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                        # Procura pelo arquivo HTML principal dentro do zip
                        html_files = [f for f in z.namelist() if f.endswith(('.html', '.htm'))]
                        
                        if html_files:
                            extracted_content = z.read(html_files[0])
                            with open(target_html_path, "wb") as f_out:
                                f_out.write(extracted_content)
                            
                            logging.info(f" -> Extraído com sucesso: {target_html_path}")
                            downloaded_count += 1
                        else:
                            logging.warning(f" -> Nenhum arquivo HTML encontrado dentro de {zip_filename}")
                else:
                    logging.warning(f" -> Falha no download (Status HTTP: {res.status_code})")

            except Exception as e:
                logging.error(f"Erro ao processar {zip_url}: {e}")

            # PAUSA OBRIGATÓRIA CONFORME A POLÍTICA DE ROBÔS (2s)
            time.sleep(DELAY_SECONDS)

        # Avança para a próxima página de harvest caso não tenha atingido a cota
        current_url = next_url

    logging.info(f"\nProcesso concluído! Total de livros HTML baixados e extraídos: {downloaded_count}")


if __name__ == "__main__":
    # Ajuste 'max_books' conforme a quantidade necessária para o dataset de PLN
    download_and_extract_books(max_books=20)