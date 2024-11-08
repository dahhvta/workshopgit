import requests
import math
import re
from datetime import datetime as dt
import json
import os
import typer
import csv

app = typer.Typer()

# Variável global para armazenar dados já carregados
API_KEY = "9fa7ce317d6e85c90d92244adb9146c6" # Chave de API para autenticação na API
BASE_URL = "https://api.itjobs.pt/job/list.json" # URL base para a API de vagas
general_results = [] # Lista global para armazenar os dados das vagas

CACHE_FILE = "cache_vagas.json"  # Caminho do arquivo de cache

########## HELP! #############
#> python {file_name} help   # 
##############################

def save_to_csv(data, filename):
    """
    Função para salvar os dados em um arquivo CSV.
    """
    keys = ['id', 'job_title', 'company', 'company_description', 'published_at', 'salary', 'location']
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()  # Escreve o cabeçalho
        for item in data:
            # Garantir que as descrições de empresa que contenham quebras de linha sejam tratadas como texto literal
            item['company_description'] = item['company_description'].replace("\n", " ").replace("\r", " ")
            
            # Escreve as linhas com os dados
            writer.writerow(item)  # Cada item é uma linha no arquivo CSV
    print(f"Resultados salvos em {filename}")
    
def load_cache():
    """Carrega o cache do arquivo se ele existir"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        print("Arquivo de cache não encontrado.")
        return(getdata(force_reload=True))

def fetch_from_api():
    """Busca as vagas de emprego diretamente da API e retorna os dados"""
    URL = f'{BASE_URL}?api_key={API_KEY}'
    try:
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        request.raise_for_status()  # Levanta um erro se o status não for 2xx (OK)
        
        # Processa a resposta da API
        response_data = request.json()
        total_vagas = response_data.get('total', 0)
        
        if total_vagas == 0:
            print("Nenhuma vaga encontrada.")
            return []

        # Calcula o número total de páginas
        total_pages = math.ceil(total_vagas / 12)
        all_jobs = []
        
        for rep in range(total_pages):
            print(f"Carregando página {rep + 1} de {total_pages}...")
            datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
            all_jobs.extend(datasets.get('results', []))
        
        """Salva os dados de vagas no cache"""
        with open(CACHE_FILE, 'w', encoding='utf-8') as file:
            json.dump(all_jobs, file, ensure_ascii=False, indent=4)
        print("Cache salvo no arquivo.")
    
        return all_jobs
    
    except requests.RequestException as e:
        print(f"Erro ao acessar a API: {e}")
        return []

def getdata(force_reload: bool = False):
    """
    Função para buscar dados das vagas de emprego. Se `force_reload` for True, 
    recarrega os dados da API e salva no cache. Caso contrário, usa o cache.
    """
    global general_results
    
    if force_reload:
        # Se for forçado o reload, buscamos da API e salvamos no cache
        print("Carregando dados da API...")
        general_results = fetch_from_api()
    else:
        # Caso contrário, carregamos do ficheiro 'cache_vagas.json'
        general_results = load_cache()

    return general_results

def vaga_json_format(item):
    """
    Função para formatar os dados de uma vaga em formato JSON com as informações selecionadas.
    """
    return {
        'id': item.get('id', 'N/A'),  # Caso 'id' não exista, retorna 'N/A'
        'job_title': item.get('title', 'N/A'),  # Caso 'title' não exista, retorna 'N/A'
        'company': item['company'].get('name', 'N/A') if 'company' in item else 'N/A',
        'company_description': item['company'].get('description', 'N/A') if 'company' in item else 'N/A', 
        'published_at': item.get('publishedAt', 'N/A'),  # Caso 'publishedAt' não exista, retorna 'N/A'
        'salary': item.get('wage', 'N/A'),  # Caso 'wage' não exista, retorna 'N/A'
        'location': item['locations'][0]['name'] if item.get('locations') and len(item['locations']) > 0 else 'N/A',  # Verifica se 'locations' existe e tem elementos
    }
            #'url': item.get('company', {}).get('url', 'N/A'),
            #'employment_type': item.get('types', [{}])[0].get('name', 'N/A'),

@app.command()
def top(n: int, save: bool = False):
    """
    Função para mostrar as 'n' vagas mais recentes.
    Exibe algumas informações selecionadas sobre as vagas.
    """
    general_data = getdata()  # Obtém dados da API ou cache
    found_jobs = [vaga_json_format(item) for item in general_data[0:n]] # Exibe os dados das 'n' vagas mais recentes    
    
    # Se 'save_csv' for True, salva os dados em CSV
    if save:
        save_to_csv(found_jobs, "top_vagas.csv")

    return print(json.dumps(found_jobs,indent=4))  # Altera para formato JSON as vagas encontradas e exibe os resultados

@app.command()
def search(company: str, location: str, num_jobs: int, save: bool = False):
    """
    Função para procurar vagas de emprego de uma empresa específica em uma localidade e que seja full time,
    limitando o número de vagas retornadas.
    """
    ## EXEMPLO DE USO ##
    # "altar.io" "Braga" 3
    
    print(f"Procurando trabalhos para Empresa: {company}, Localidade: {location}, Número de Trabalhos: {num_jobs}")
    
    general_data = getdata() # Obtém dados da API ou cache
    found_jobs = [] # Inicializa / reseta a lista de trabalhos encontrados
    
    for item in general_data:
        company_name = item['company']['name'] # Obtém o nome da empresa
        job_locations = [loc['name'] for loc in item.get('locations', [])] # Obtém as localizações das vagas
        job_type = [job['name'].lower() for job in item.get('types', [])] # Checa o tipo de trabalho (full-time, part-time, etc.)
        
        # Verifica se a vaga corresponde ao nome da empresa e se a localização está na lista
        if (company_name.lower() == company.lower() and any(location.lower() in loc.lower() for loc in job_locations) and 'full-time' in job_type):
            found_jobs.append(vaga_json_format(item)) # Adiciona o trabalho encontrado à lista
            print(f"\nTrabalho encontrado: {item['title']} na empresa {company_name} na localidade {location}")
        
        if len(found_jobs) >= num_jobs: # Se o número de vagas encontrado atingir o limite, saímos do loop
            break
    
    # Se 'save_csv' for True, salva os dados em CSV
    if save and found_jobs:
        save_to_csv(found_jobs, "search_vagas.csv")
    
    if found_jobs: # Exibe o resultado no formato JSON ou uma mensagem caso não encontre resultados
        return print(json.dumps(found_jobs,indent=4))
    else:
        return print("Nenhum trabalho encontrado para os critérios especificados.")

@app.command()
def salary(job_id: int):
    """
    Função para extrair e exibir o salário de uma vaga a partir de seu job_id.
    Caso o salário não esteja disponível, achar com expressoes regulares.
    """
    ## EXEMPLO DE USO ##
    # Id com wage != null para testar
    # 491881, 491763, 491690, 491671, 491626, 490686, 491483, 491458
    
    general_data = getdata()  # Obtém dados da API ou cache
    
    # Expressões regulares para encontrar salários no corpo da descrição
    salary_patterns = [
        r"(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s?(?:euros|€|bruto|neto|por mês|mensal))",  # Ex: 3000€, 3000 euros, 2500 por mês
        r"(\d+\s?k\s?€)",# Ex: 2.5k €
    ]
    
    for item in general_data:
        if item['id'] == job_id:
            salary = item.get('wage') # Tenta obter o salário diretamente
            
            if not salary: # Se salario não existir entao tentar buscar salario no 'body'
                salary = [re.search(pattern, item.get('body'), re.IGNORECASE).group(0) for pattern in salary_patterns if re.search(pattern, item.get('body'), re.IGNORECASE)] 
                if not salary:
                    salary = "salario não encontrado."

            locations = (', '.join([location['name'] for location in item.get('locations', [])])) # Obtém a(s) localização(ões) da vaga
            
            # Exibe as informações da vaga e o salário
            return print(f"Id: {job_id} - {item['title']}, {item['company']['name']} ({locations}): {salary}")
            
    print(f"Vaga com o id {job_id} não encontrada.") # Caso não encontre a vaga com o job_id
        
@app.command()
def skills(skills:str, data_ini:str, data_fim:str, save: bool = False):
    """
    Função para buscar dados de vagas de emprego com base nas skills e no intervalo de datas.
    A saída é no formato JSON, com os dados das vagas que atendem aos critérios.
    """
    ## EXEMPLO DE USO ##
    # skills "inteligencia artificial" "2024-1-1" "2024-12-31"
    # skills "Data" "2024-1-1" "2024-12-31"  
    # skills "inteligencia artificial, Python" "2024-1-1" "2024-12-31"
    
    data_ini = dt.strptime(data_ini, '%Y-%m-%d') # Converte as datas para o formato correto
    data_fim = dt.strptime(data_fim, '%Y-%m-%d') # Converte as datas para o formato correto
    
    general_results = getdata() # Obtém dados da API ou cache
    
    # Skills para lista de strings "python,react" -> ['python','react']
    skills_list = [skill.strip() for skill in skills.split(",")] 
    
    found_jobs = [] # Inicializa / reseta a lista de trabalhos encontrados
    
    for item in general_results:
        data_trabalho = dt.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S') # Converte a data de publicação para o formato correto
        
        # Verifica se a vaga está dentro do intervalo de datas e contém todas as skills desejadas
        if data_ini <= data_trabalho <= data_fim and all(re.search(criar_regex_sem_acentos(skill), item['body'], re.IGNORECASE) for skill in skills_list):
            found_jobs.append(vaga_json_format(item)) # Adiciona à lista de vagas encontradas
    
    # Se 'save_csv' for True, salva os dados em CSV
    if save and found_jobs:
        save_to_csv(found_jobs, "skills_vagas.csv")
        
    # Exibe o resultado em JSON ou uma mensagem caso nenhuma vaga seja encontrada
    if found_jobs:
        return print(json.dumps(found_jobs, indent=4))
    else:
        return print("Nenhuma vaga encontrada para os critérios informados.")

def criar_regex_sem_acentos(palavra):
    """
    Esta função cria uma expressão regular que ignora os acentos em uma palavra
    para que a busca seja insensível a acentos (exemplo: 'inteligência' será igual a 'inteligencia').
    """
    # Inteligência -> Intelig[eéèê]ncia

    # Mapa de caracteres com acento para suas versões sem acento
    mapa_acentos = {
        'a': '[aáàãâ]',
        'e': '[eéèê]',
        'i': '[iíìî]',
        'o': '[oóòôõ]',
        'u': '[uúùû]',
        'c': '[cç]',
        'n': '[nñ]'
    }
    # Substitui cada letra com acento por sua versão com acento, tornando a busca flexível
    palavra_regex = ''
    for char in palavra:
        if char.lower() in mapa_acentos:
            palavra_regex += mapa_acentos[char.lower()] # Adiciona os caracteres com alterações
        else:
            palavra_regex += char # Adiciona o caractere sem alteração
            
    return palavra_regex # Retorna a expressão regular criada

@app.command()
def reloadapi():
    """Regarrega o ficheiro json com dados da API"""
    getdata(force_reload=True)
    
@app.command()
def help():
    """
    Ajuda com os comandos
    """
    print("""
####  HELP  #############################################################################################################################################
# python {path} help : Exibe ajuda com todos os comandos.                                                                                               #
# python {path} top <n> [--save] : Mostra as 'n' vagas mais recentes. Se '--save' for fornecido, salva os resultados em um arquivo CSV chamado          #
#                                "top_vagas.csv".                                                                                                       #
#        Exemplo: python {path} top 5 --save                                                                                                            #
#               Mostra as 5 vagas mais recentes e salva os resultados em "top_vagas.csv".                                                               #
#                                                                                                                                                       #
# python {path} search <empresa> <localidade> <n> [--save] : Procura vagas para uma empresa específica em uma localidade específica (full-time).        #
#               Limita a quantidade de resultados para 'n'. Se '--save' for fornecido, salva os resultados em um arquivo CSV chamado "search_vagas.csv".#
#        Exemplo: python {path} search "altar.io" "Braga" 3 --save                                                                                      #
#               Busca 3 vagas da empresa "altar.io" em "Braga" e salva os resultados em "search_vagas.csv".                                             # 
#                                                                                                                                                       #
# python {path} salary <id> : Exibe o salário de acordo com o ID da vaga.                                                                               #
#        Exemplo: python {path} salary 491881                                                                                                           #
#               Exibe o salário da vaga com ID 491881.                                                                                                  #
#                                                                                                                                                       #
# python {path} skills <skills> <data_ini> <data_fim> [--save] : Procura vagas que exigem habilidades específicas dentro de um intervalo de datas.      #
#               O parâmetro 'skills' pode ser uma lista de habilidades separadas por vírgula. Se '--save' for fornecido, salva os resultados em um      #
#               arquivo CSV chamado "skills_vagas.csv".                                                                                                 #
#        Exemplo: python {path} skills "Python, Data Science" "2024-01-01" "2024-12-31" --save                                                          #
#               Busca vagas que exigem "Python" e "Data Science" no intervalo de 01/01/2024 a 31/12/2024 e salva os resultados em "skills_vagas.csv".   #
#                                                                                                                                                       #
# python {path} reloadapi : Força o recarregamento dos dados da API, ignorando o cache.                                                                 #
#        Exemplo: python {path} reloadapi                                                                                                               #
#               Atualiza o cache com os dados mais recentes da API.                                                                                     #
#########################################################################################################################################################
""")
    
# Inicializa o aplicativo Typer
if __name__ == "__main__":
    app()