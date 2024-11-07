import requests
import json
from datetime import datetime
import typer
import math
import re
import sys
import csv

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
            'id': item['id'],
            'job_title': item['title'],
            'company': item['company']['name'],
            'company_description': item['company']['description'],
            'published_at': item['publishedAt'],
            'salary': item.get('wage', 'N/A'),
            'location': item['locations'][0]['name'] if item.get('locations') else 'N/A',
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
    
    print(f"Procurando trabalhos para Empresa: {company}, Localidade: {location}, Número de Trabalhos: {num_jobs}")
    
    general_data = getdata() # Obtém dados da API ou cache
    
    found_jobs = [] # Inicializa/ reseta a lista de trabalhos encontrados
    
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

    for item in general_data:
        if item['id'] == job_id:
            salary = item.get('wage', 'Salário não informado')  # IMPLEMENTAR EXPRESSOES REGULARES!
            locations = (', '.join([location['name'] for location in item.get('locations', [])]))
            return print(f"Id: {job_id} - {item['title']}, {item['company']['name']} ({locations}): {salary}")
            
    print(f"Vaga com o id {job_id} não encontrada.") # Caso não encontre a vaga com o job_id


""" def salary(jobID):
    URL = 'https://api.itjobs.pt/job/get.json'
    api_key = '9fa7ce317d6e85c90d92244adb9146c6'
    
    try:
        # Realiza a requisição para obter informações sobre o trabalho
        response = requests.get(URL, params={'api_key': api_key, 'id': jobID}, 
                                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
        
        # Verifica o código de status da resposta
        if response.status_code != 200:
            print(f"Erro: Status HTTP {response.status_code}. Verifique a chave da API e o jobID.")
            return
        
        # Tenta carregar o conteúdo JSON da resposta
        data = response.json()
        
    except requests.JSONDecodeError:
        print("Erro: A resposta não está em formato JSON. Verifique a URL e os parâmetros.")
        return

    # Verifica se a resposta contém o campo 'error' indicando que o jobID não foi encontrado
    if 'error' in data:
        print(f"Erro: {data['error'].get('message', 'Erro desconhecido')}")
        return

    # Tenta extrair o salário do campo 'wage' se presente
    wage = data.get('wage')
    salary_found = False

    # Se o salário for encontrado, imprime e grava no CSV
    if wage is not None:
        print(f"Apresenta um salário inicial de {wage}€.")
        salary_found = True
    else:
        # Caso 'wage' esteja ausente, tenta encontrar o salário em campos alternativos usando expressões regulares
        fields_to_check = ['description', 'salary_info', 'benefits']
        
        for field in fields_to_check:
            if field in data and isinstance(data[field], str):  # Verifica se o campo é uma string
                match = re.search(r'(\d+(\.\d{1,2})?)\s*(€|USD|BRL|GBP)', data[field])
                if match:
                    print(f"Salário encontrado no campo {field}: {match.group(0)}")
                    salary_found = True
                    break

    # Se o salário não for encontrado em nenhum campo
    if not salary_found:
        print("Não foi possível encontrar o salário para este trabalho.")
    
    # Coleta as informações principais do trabalho
    title = data.get('title', '')
    company_name = data['company'].get('name', '')
    description = data['company'].get('description', '')
    published_at = data.get('publishedAt', '')
    locations = ', '.join([loc['name'] for loc in data.get('locations', [])])
    
    # Se a opção 'csv' for passada nos argumentos, exporta para CSV
    if 'csv' in sys.argv:
        with open(f'{jobID}_job_salary.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Company', 'Description', 'Published At', 'Salary', 'Location'])
            
            # Escreve os dados no CSV
            writer.writerow([title, company_name, description, published_at, wage if wage else 'Não disponível', locations])
        
        print(f"Informações exportadas para o arquivo {jobID}_job_salary.csv.")
"""
"""def skills_data(queries, data_ini, data_fim, csv_check=0):
    not_found = 1
    URL = 'https://api.itjobs.pt/job/list.json?api_key=2fd9dd6db7e14adbf04df55811af5d22'
    
    # Realiza a requisição para obter a lista de trabalhos
    request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
    data = request.json()

    alldata = {}
    total_pages = math.ceil(data['total'] / 12)
    
    # Itera pelas páginas dos trabalhos
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, 
                                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'}).json()
        results = datasets['results']
        
        # Verifica os trabalhos para cada item
        for item in results:
            data_trabalho = dt.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S')
            
            # Verifica se o trabalho está dentro do intervalo de datas
            if data_trabalho > data_ini and data_trabalho < data_fim:
                for query in queries:
                    palavra_chave = re.search(query, item['body'])
                    if palavra_chave:
                        if csv_check == 0:
                            # Adiciona dados para não CSV
                            alldata[item['id']] = [item['company']['name'], item['company']['url']]
                            not_found = 0
                        else:
                            # Adiciona dados para exportação em CSV
                            alldata[item['id']] = [
                                item.get('title', ''),
                                item['company'].get('name', ''),
                                item['company'].get('description', ''),
                                item.get('publishedAt', ''),
                                item.get('wage', ''),
                                item['company'].get('address', '')
                            ]
                            not_found = 0
            
            # Se a data de publicação for anterior à data inicial, já podemos parar a busca
            elif data_trabalho < data_ini:
                not_found = 0
                return alldata

    if not_found == 1:
        return False

    # Se o parâmetro 'csv' for passado nos argumentos, exporta para CSV
    if 'csv' in sys.argv and csv_check == 1:
        with open('skills_data.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Company', 'Description', 'Published At', 'Salary', 'Location'])

            # Escreve os dados no CSV
            for job_id, job_data in alldata.items():
                writer.writerow(job_data)
        
        print(f"Informações exportadas para o arquivo skills_data.csv.")

    return alldata
"""
if __name__ == "__main__":
    app()