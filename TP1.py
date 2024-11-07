import requests
import math
import re
from datetime import datetime as dt
import json
import typer

API_KEY = "9fa7ce317d6e85c90d92244adb9146c6"
BASE_URL = "https://api.itjobs.pt/job/list.json"

app = typer.Typer()

# Variável global para armazenar dados já carregados
general_results = []
cache_loaded = False

@app.command()
def getdata():
    """
    Função para buscar todos os dados das vagas de emprego da API
    e armazenar na variável 'general_results'.
    
    Retorna o valor 'general_results'
    
    Usa cache para evitar chamadas repetidas à API enquanto o programa estiver em execução.
    """
    global API_KEY, BASE_URL, general_results, cache_loaded
    
    if cache_loaded: # Verifica se já existem dados carregados
        return general_results

    URL = f'{BASE_URL}?api_key={API_KEY}'
    print("Pedindo informações à API, pode demorar um tempo...")
    
    request = requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
    total_pages = math.ceil(request.json()['total']/12)
    
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page':rep+1},headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'}).json()
        general_results.extend(datasets['results'])
    
    cache_loaded = True 
    return general_results

def vaga_json_format(item):
    return {
        'id': item.get('id', 'N/A'),  # Caso 'id' não exista, retorna 'N/A'
        'job_title': item.get('title', 'N/A'),  # Caso 'title' não exista, retorna 'N/A'
        'company': item['company'].get('name', 'N/A') if 'company' in item else 'N/A',  # Verifica se 'company' existe
        'company_description': item['company'].get('description', 'N/A') if 'company' in item else 'N/A',  # Verifica se 'company' existe
        'published_at': item.get('publishedAt', 'N/A'),  # Caso 'publishedAt' não exista, retorna 'N/A'
        'salary': item.get('wage', 'N/A'),  # Caso 'wage' não exista, retorna 'N/A'
        'location': item['locations'][0]['name'] if item.get('locations') and len(item['locations']) > 0 else 'N/A',  # Verifica se 'locations' existe e tem elementos
    }

            #'url': item.get('company', {}).get('url', 'N/A'),
            #'employment_type': item.get('types', [{}])[0].get('name', 'N/A'),

@app.command()
def top(n: int):
    """
    Função para mostrar as 'n' vagas mais recentes.
    Exibe algumas informações selecionadas sobre as vagas.
    
    Para a alinea A não é preciso fazer nenhum tipo de sort pois os primeiros valores a serem adicionados
    são os mais recentes.
    """
    general_data = getdata()  # Obtém dados da API ou cache
    data_top = [vaga_json_format(item) for item in general_data[0:n]] # Exibe os dados das 'n' vagas mais recentes    
        
    return print(json.dumps(data_top,indent=4))
    
@app.command()
def search(company: str, location: str, num_jobs: int):
    # "altar.io" "Braga" 3
    
    print(f"Procurando trabalhos para Empresa: {company}, Localidade: {location}, Número de Trabalhos: {num_jobs}")
    
    general_data = getdata() # Obtém dados da API ou cache
    
    found_jobs = [] # Inicializa / reseta a lista de trabalhos encontrados
    
    for item in general_data:
        company_name = item['company']['name']
        job_locations = [loc['name'] for loc in item.get('locations', [])]
        
        # Verifica se a vaga corresponde ao nome da empresa e se a localização está na lista
        if company_name.lower() == company.lower() and any(location.lower() in loc.lower() for loc in job_locations):
            found_jobs.append(vaga_json_format(item))
            print(f"\nTrabalho encontrado: {item['title']} na empresa {company_name} na localidade {location}")
        
        # Se o número de vagas encontrado atingir o limite, saímos do loop
        if len(found_jobs) >= num_jobs:
            break
    
    if found_jobs:
        return print(json.dumps(found_jobs,indent=4))
    
    else:
        return print("Nenhum trabalho encontrado para os critérios especificados.")

@app.command()
def salary(job_id: int):
    # Id com wage != null para testar
    # 491881, 491763, 491690, 491671, 491626, 490686, 491483, 491458

    """
    Função para extrair e exibir o salário de uma vaga a partir de seu job_id.
    Caso o salário não esteja disponível, achar com expressoes regulares.
    """
    general_data = getdata()  # Obtém dados da API ou cache

    salary_patterns = [
        r"(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s?(?:euros|€|bruto|neto|por mês|mensal))",  # Ex: 3000€, 3000 euros, 2500 por mês
        r"(\d+\s?k\s?€)",# Ex: 2.5k €
    ]
    
    for item in general_data:
        if item['id'] == job_id:
            salary = item.get('wage')
            
            if not salary: # Se salario não existir entao tentar buscar salario no 'body'
                salary = [re.search(pattern, item.get('body'), re.IGNORECASE).group(0) for pattern in salary_patterns if re.search(pattern, item.get('body'), re.IGNORECASE)] 
                if not salary:
                    salary = "salario não encontrado."

            locations = (', '.join([location['name'] for location in item.get('locations', [])]))
            
            return print(f"Id: {job_id} - {item['title']}, {item['company']['name']} ({locations}): {salary}")
            
    print(f"Vaga com o id {job_id} não encontrada.") # Caso não encontre a vaga com o job_id
        
@app.command()
def skills(skills:str, data_ini:str, data_fim:str):
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
    
    skills_list = [skill.strip() for skill in skills.split(",")] # Skills para lista de strings "python,react" -> ['python','react']
    
    found_jobs = [] # Inicializa / reseta a lista de trabalhos encontrados
    
    for item in general_results:
        data_trabalho = dt.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S')
        if data_ini <= data_trabalho <= data_fim and all(re.search(criar_regex_sem_acentos(skill), item['body'], re.IGNORECASE) for skill in skills_list):
            found_jobs.append(vaga_json_format(item))
            
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
            palavra_regex += mapa_acentos[char.lower()]
        else:
            palavra_regex += char
            
    return palavra_regex

if __name__ == "__main__":
    app()