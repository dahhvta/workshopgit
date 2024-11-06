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

def fetch_jobs(params):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(BASE_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter dados: {response.status_code} - {response.text}")
        return None
    
def top10_data():
  URL = 'https://api.itjobs.pt/job/list.json?api_key=9fa7ce317d6e85c90d92244adb9146c6'
  request = requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
  data = request.json()
  alldata={}
  total_pages = math.ceil(data['total']/12)
  for rep in range(total_pages):
      datasets = requests.get(URL, params={'limit': 12, 'page':rep+1},headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'}).json()
      results = datasets['results']
      if 'csv' in sys.argv:        
        for item in results:
          alldata[item['id']] = [item.get('title', ''),item['company'].get('name', ''), item['company'].get('description', ''),item.get('publishedAt', ''),item.get('wage', ''),item['company'].get('address', '')]
      else: 
        for item in results:
          alldata[item['id']] = [item['company']['name'],item['publishedAt']]
  return alldata


def search_data(company, location, num_jobs):
    print(f"Procurando trabalhos para Empresa: {company}, Localidade: {location}, Número de Trabalhos: {num_jobs}")
    
    # URL base da API
    URL = 'https://api.itjobs.pt/job/list.json'
    API_KEY = '9fa7ce317d6e85c90d92244adb9146c6'  # Substitua pela sua chave de API

    # Inicializa a lista de trabalhos encontrados
    found_jobs = []
    
    # Faz a primeira requisição para saber o total de trabalhos
    response = requests.get(URL, params={'api_key': API_KEY, 'limit': 12, 'page': 1}, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    if 'total' in data and data['total'] > 0:
        total_pages = math.ceil(data['total'] / 12)
        for rep in range(total_pages):
            # Requisição para cada página
            datasets = requests.get(URL, params={'api_key': API_KEY, 'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
            results = datasets.get('results', [])
            
            for item in results:
                # Acessa o nome da empresa e localidade
                company_name = item['company']['name']
                job_locations = [loc['name'] for loc in item.get('locations', [])]
                
                # Filtra pelos critérios
                if (company_name == company) and (location in job_locations):
                    found_jobs.append(item)
                    print(f"Trabalho encontrado: {item['title']} na empresa {company_name} na localidade {location}")
                
                # Limita a quantidade de trabalhos encontrados
                if len(found_jobs) >= num_jobs:
                    break
            
            # Para o loop se já encontrou o número de trabalhos desejado
            if len(found_jobs) >= num_jobs:
                break

    # Verifica se encontrou trabalhos
    if found_jobs:
        return found_jobs
    else:
        print("Nenhum trabalho encontrado para os critérios especificados.")
        return None












def salary(jobID):
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
    if wage is not None:
        print(f"Apresenta um salário inicial de {wage}€.")
        return
    
    # Caso 'wage' esteja ausente, tenta encontrar o salário em campos alternativos usando expressões regulares
    salary_found = False
    fields_to_check = ['description', 'salary_info', 'benefits']
    
    for field in fields_to_check:
        if field in data and isinstance(data[field], str):  # Verifica se o campo é uma string
            match = re.search(r'(\d+(\.\d{1,2})?)\s*(€|USD|BRL|GBP)', data[field])
            if match:
                print(f"Salário encontrado no campo {field}: {match.group(0)}")
                salary_found = True
                break
    
    # Se não encontrou o salário em nenhum dos campos alternativos
    if not salary_found:
        # Tenta fornecer informações adicionais sobre o contrato
        contract_info = []
        if 'contracts' in data and isinstance(data['contracts'], list) and data['contracts']:
            contract_info.append(f"Contrato: {data['contracts'][0].get('name', 'Desconhecido')}")
        if 'types' in data and isinstance(data['types'], list) and data['types']:
            contract_info.append(f"Tipo: {data['types'][0].get('name', 'Desconhecido')}")
        
        # Se houver informações de contrato ou tipo, exibe-as; caso contrário, informa que não há dados disponíveis
        if contract_info:
            print("Sem informação sobre o salário.\n" + ", ".join(contract_info))
        else:
            print("Sem informação sobre o trabalho selecionado.")




















def skills_data():
  not_found = 1
  URL = 'https://api.itjobs.pt/job/list.json?api_key=2fd9dd6db7e14adbf04df55811af5d22'
  request = requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
  data = request.json()
  alldata={}
  total_pages = math.ceil(data['total']/12)
  for rep in range(total_pages):
      datasets = requests.get(URL, params={'limit': 12, 'page':rep+1},headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'}).json()
      results = datasets['results']
      for item in results:
            data_trabalho = dt.strptime(item['publishedAt'],'%Y-%m-%d %H:%M:%S')
            if data_trabalho > data_ini and data_trabalho < data_fim:
                for query in queries:
                    palavra_chave = re.search(query,item['body'])
                    if palavra_chave:
                      if csv_check == 0:
                        alldata[item['id']] = [item['company']['name'],item['company']['url']]
                        not_found = 0
                      else:
                        alldata[item['id']] = [item.get('title', ''),item['company'].get('name', ''), item['company'].get('description', ''),item.get('publishedAt', ''),item.get('wage', ''),item['company'].get('address', '')]
                        not_found = 0
            elif data_trabalho < data_ini:
                not_found = 0
                return alldata
  if not_found == 1:
      return False
  return alldata
  















def top10_data():
    URL = 'https://api.itjobs.pt/job/list.json?api_key=9fa7ce317d6e85c90d92244adb9146c6'
    request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
    data = request.json()
    alldata = {}
    
    total_pages = math.ceil(data['total'] / 12)
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'}).json()
        results = datasets['results']
        
        if 'csv' in sys.argv:        
            for item in results:
                alldata[item['id']] = [
                    item.get('title', ''),
                    item['company'].get('name', ''),
                    item['company'].get('description', ''),
                    item.get('publishedAt', ''),
                    item.get('wage', ''),
                    item['company'].get('address', '')
                ]
            
            # Exportar para CSV
            with open('job_list.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Title', 'Company', 'Description', 'Published At', 'Salary', 'Location'])
                for key, value in alldata.items():
                    writer.writerow([key] + value)

        else: 
            for item in results:
                alldata[item['id']] = [item['company']['name'], item['publishedAt']]
    
    return alldata
  
def search_data(company, location, num_jobs):
    print(f"Procurando trabalhos para Empresa: {company}, Localidade: {location}, Número de Trabalhos: {num_jobs}")
    
    # URL base da API
    URL = 'https://api.itjobs.pt/job/list.json'
    API_KEY = '9fa7ce317d6e85c90d92244adb9146c6'  # Substitua pela sua chave de API

    # Inicializa a lista de trabalhos encontrados
    found_jobs = []
    
    # Faz a primeira requisição para saber o total de trabalhos
    response = requests.get(URL, params={'api_key': API_KEY, 'limit': 12, 'page': 1}, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    if 'total' in data and data['total'] > 0:
        total_pages = math.ceil(data['total'] / 12)
        for rep in range(total_pages):
            # Requisição para cada página
            datasets = requests.get(URL, params={'api_key': API_KEY, 'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
            results = datasets.get('results', [])
            
            for item in results:
                # Acessa o nome da empresa e localidade
                company_name = item['company']['name']
                job_locations = [loc['name'] for loc in item.get('locations', [])]
                
                # Filtra pelos critérios
                if (company_name == company) and (location in job_locations):
                    found_jobs.append(item)
                    print(f"Trabalho encontrado: {item['title']} na empresa {company_name} na localidade {location}")
                
                # Limita a quantidade de trabalhos encontrados
                if len(found_jobs) >= num_jobs:
                    break
            
            # Para o loop se já encontrou o número de trabalhos desejado
            if len(found_jobs) >= num_jobs:
                break

    # Verifica se encontrou trabalhos
    if found_jobs:
        # Verifica se o argumento 'csv' está presente para exportar os dados para um arquivo CSV
        if 'csv' in sys.argv:
            # Exportar para CSV
            with open('found_jobs.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Title', 'Company', 'Description', 'Published At', 'Salary', 'Location'])
                for item in found_jobs:
                    title = item.get('title', '')
                    company_name = item['company'].get('name', '')
                    description = item['company'].get('description', '')
                    published_at = item.get('publishedAt', '')
                    wage = item.get('wage', '')
                    locations = ', '.join([loc['name'] for loc in item.get('locations', [])])
                    
                    writer.writerow([title, company_name, description, published_at, wage, locations])
            print(f"{len(found_jobs)} trabalhos exportados para 'found_jobs.csv'.")
        return found_jobs
    else:
        print("Nenhum trabalho encontrado para os critérios especificados.")
        return None
    

def salary(jobID):
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

def skills_data(queries, data_ini, data_fim, csv_check=0):
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
