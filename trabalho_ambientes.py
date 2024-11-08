import requests
import json
import re
import math
from datetime import datetime as dt
import typer
import csv 


# Resto do código...

# Constantes de Configuração
API_KEY = "9fa7ce317d6e85c90d92244adb9146c6"
BASE_URL = "https://api.itjobs.pt/job/list.json"

app = typer.Typer()

# Função para buscar vagas da API
def fetch_jobs(params):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(BASE_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter dados: {response.status_code} - {response.text}")
        return None

# Função para buscar os 10 trabalhos mais recentes
def top10():
    print("Procurando os 10 trabalhos mais recentes...")
    response = requests.get(BASE_URL, params={'api_key': API_KEY, 'limit': 10, 'page': 1}, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    if 'results' in data:
        top_10_jobs = [{'id': item['id'], 'title': item['title'], 'company_name': item['company']['name']} for item in data['results']]
        print(json.dumps(top_10_jobs, indent=4))
    else:
        print("Nenhum trabalho encontrado.")

# Função para obter empregos com filtros de localização e empresa
def get_jobs(location, company, num_jobs):
    URL = f'{BASE_URL}?api_key={API_KEY}'
    try:
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        if request.status_code != 200:
            print(f"Erro: Recebido código de status {request.status_code} da API")
            return
        
        data = request.json()
        jobs = data.get("results", [])
        print("\nEmpregos encontrados:")
        for job in jobs:
            print(f"Cargo: {job.get('title', 'N/A')}, Empresa: {job.get('company', {}).get('name', 'N/A')}")
        
        filtered_jobs = [
            job for job in jobs if (company.lower() in job.get('company', {}).get('name', '').lower())
            and any(location.lower() in loc.get("name", "").lower() for loc in job.get("locations", []))
        ][:num_jobs]
        
        if filtered_jobs:
            print("\nEmpregos filtrados:")
            print(json.dumps(filtered_jobs, ensure_ascii=False, indent=2))
        else:
            print("Nenhum trabalho encontrado para os critérios especificados.")
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")

# Função para obter o salário de um emprego específico
def salary(jobID):
    URL = 'https://api.itjobs.pt/job/get.json'
    try:
        response = requests.get(URL, params={'api_key': API_KEY, 'id': jobID}, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"Erro: Status HTTP {response.status_code}. Verifique a chave da API e o jobID.")
            return
        
        data = response.json()
        wage = data.get('wage')
        
        if wage:
            print(f"Apresenta um salário inicial de {wage}€.")
        else:
            salary_found = extract_salary_from_body(data.get('body', ''))
            if salary_found:
                print(f"Salário encontrado no corpo da descrição: {salary_found}")
            else:
                print("Sem informação sobre o salário.")
    except requests.JSONDecodeError:
        print("Erro: A resposta não está em formato JSON.")

# Função auxiliar para extrair salário usando expressões regulares
def extract_salary_from_body(body):
    salary_patterns = [
        r"(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s?(?:euros|€|bruto|neto|por mês|mensal))",
        r"(\d+\s?k\s?€)"
    ]
    for pattern in salary_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

# Função que busca e filtra os trabalhos de acordo com skills e período de tempo
def skills_data(skills, data_ini, data_fim):
    not_found = True
    URL = f'{BASE_URL}?api_key={API_KEY}'
    request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
    data = request.json()
    
    alldata = []
    total_pages = math.ceil(data['total'] / 12)
    
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
        results = datasets['results']
        
        for item in results:
            data_trabalho = dt.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S')
            
            if data_ini <= data_trabalho <= data_fim:
                if all(re.search(skill, item['body'], re.IGNORECASE) for skill in skills):
                    trabalho_info = {
                        'id': item['id'],
                        'title': item.get('title', ''),
                        'company_name': item['company'].get('name', ''),
                        'publishedAt': item.get('publishedAt', ''),
                        'wage': item.get('wage', ''),
                        'address': item['company'].get('address', '')
                    }
                    alldata.append(trabalho_info)
                    not_found = False
    
    return alldata if not not_found else False

# Função para exibir os trabalhos conforme as skills e período
def buscar_trabalhos_por_skills(skills, data_inicial, data_final):
    data_ini = dt.strptime(data_inicial, '%Y-%m-%d')
    data_fim = dt.strptime(data_final, '%Y-%m-%d')
    resultados = skills_data(skills, data_ini, data_fim)
    
    if resultados:
        return json.dumps(resultados, indent=4)
    else:
        return "Nenhum trabalho encontrado para as habilidades e período fornecidos."

# Exemplo de execução
if __name__ == "__main__":
    top10()
    get_jobs("Lisboa", "EllaLink", 5)
    print(salary(490686))  # Substitua pelo ID de trabalho real
    print(buscar_trabalhos_por_skills(["Python", "Django"], "2024-10-01", "2024-10-31"))


def top10(export_csv=False):
    print("Procurando os 10 trabalhos mais recentes...")

    URL = 'https://api.itjobs.pt/job/list.json'
    API_KEY = '9fa7ce317d6e85c90d92244adb9146c6'

    response = requests.get(URL, params={'api_key': API_KEY, 'limit': 10, 'page': 1}, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()

    if 'results' in data:
        top_10_jobs = [
            {
                'id': item['id'],
                'title': item['title'],
                'company_name': item['company']['name'],
                'description': item.get('description', 'N/A'),
                'published_at': item.get('published_at', 'N/A'),
                'salary': item.get('salary', 'N/A'),
                'location': ', '.join([loc['name'] for loc in item.get('locations', [])])
            }
            for item in data['results']
        ]

        print(json.dumps(top_10_jobs, indent=4))

        if export_csv:
            filename = f"top_10_jobs_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
            fields = ['id', 'title', 'company_name', 'description', 'published_at', 'salary', 'location']
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(top_10_jobs)
            print(f"Os 10 trabalhos mais recentes foram exportados para {filename}")
    else:
        print("Nenhum trabalho encontrado.")

# Função para exportar uma lista de trabalhos para CSV
def export_to_csv(jobs, filename="jobs.csv"):
    fieldnames = ['titulo', 'empresa', 'descricao', 'data_publicacao', 'salario', 'localizacao']
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            job_data = {
                'titulo': job.get('title', 'N/A'),
                'empresa': job.get('company', {}).get('name', 'N/A'),
                'descricao': job.get('body', 'N/A'),
                'data_publicacao': job.get('published', 'N/A'),
                'salario': job.get('wage', 'N/A'),
                'localizacao': ', '.join([location.get('name', 'N/A') for location in job.get('locations', [])])
            }
            writer.writerow(job_data)
    print(f"Dados exportados para {filename}")

# Função para buscar trabalhos com filtros de localização e empresa, com opção de exportar para CSV
def export_to_csv(jobs, filename="jobs.csv"):
    try:
        with open(filename, mode="w", newline="") as file:
            fields = ["title", "company", "location", "type", "description"]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

            for job in jobs:
                writer.writerow({
                    "title": job.get("title", "N/A"),
                    "company": job.get("company", {}).get("name", "N/A"),
                    "location": ", ".join([loc.get("name", "N/A") for loc in job.get("locations", [])]),
                    "type": job.get("type", "N/A"),
                    "description": job.get("description", "N/A"),
                })
        print(f"Dados exportados para {filename}")
    except Exception as e:
        print(f"Erro ao exportar para CSV: {e}")

# Função para buscar os trabalhos com base nos filtros fornecidos
def get_jobs(location, company, num_jobs, job_type=None, save_to_csv=False):
    URL = 'https://api.itjobs.pt/job/list.json?api_key=9fa7ce317d6e85c90d92244adb9146c6'

    try:
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        if request.status_code != 200:
            print(f"Erro: Recebido código de status {request.status_code} da API")
            return
        
        data = request.json()
        jobs = data.get("results", [])
        
        if not isinstance(jobs, list):
            print("Erro: Formato inesperado dos dados da API.")
            return

        # Filtrando os trabalhos com base em localização, empresa e tipo de trabalho (full-time ou outro)
        filtered_jobs = [
            job for job in jobs
            if company.lower() in job.get("company", {}).get("name", "").lower()
            and any(location.lower() in loc.get("name", "").lower() for loc in job.get("locations", []))
            and (job_type is None or job.get("type", "").lower() == job_type.lower())  # Filtro de tipo de trabalho (ex: "full-time")
        ][:num_jobs]

        if filtered_jobs:
            for job in filtered_jobs:
                print(f"Título: {job.get('title', 'N/A')}, Empresa: {job.get('company', {}).get('name', 'N/A')}")
            
            if save_to_csv:
                export_to_csv(filtered_jobs)
        else:
            print("Nenhum trabalho encontrado para os critérios especificados.")
    
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")

# Função para buscar trabalhos por habilidades e período, com opção de exportar para CSV
def skills_data(skills, data_ini, data_fim, export_csv=False):
    URL = 'https://api.itjobs.pt/job/list.json?api_key=2fd9dd6db7e14adbf04df55811af5d22'

    try:
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        if request.status_code != 200:
            print(f"Erro: Recebido status code {request.status_code} da API")
            return
        
        data = request.json()
        alldata = []
        total_pages = math.ceil(data['total'] / 12)

        for rep in range(total_pages):
            datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
            results = datasets['results']
            
            for item in results:
                data_trabalho = dt.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S')
                
                if data_ini <= data_trabalho <= data_fim and all(re.search(skill, item['body'], re.IGNORECASE) for skill in skills):
                    trabalho_info = {
                        'id': item['id'],
                        'title': item.get('title', ''),
                        'company_name': item['company'].get('name', ''),
                        'publishedAt': item.get('publishedAt', ''),
                        'wage': item.get('wage', ''),
                        'address': item['company'].get('address', '')
                    }
                    alldata.append(trabalho_info)

        if export_csv and alldata:
            filename = f"jobs_skills_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
            fields = ['id', 'title', 'company_name', 'publishedAt', 'wage', 'address']
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(alldata)
            print(f"Os trabalhos foram exportados para {filename}")
        return json.dumps(alldata, indent=4)
    
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")

# Função principal para escolher a funcionalidade
def main():
    print("Bem-vindo ao sistema de busca de empregos!")
    print("Escolha uma opção:")
    print("1. Buscar os 10 trabalhos mais recentes")
    print("2. Buscar trabalhos por localização e empresa")
    print("3. Buscar trabalhos por habilidades e período")
    
    choice = input("Digite o número da opção desejada: ")

    if choice == "1":
        export = input("Deseja exportar para CSV? (s/n): ").lower() == 's'
        top10(export_csv=export)
    elif choice == "2":
        location = input("Digite a localização: ")
        company = input("Digite o nome da empresa: ")
        num_jobs = int(input("Quantos trabalhos deseja listar? "))
        job_type = input("Digite o tipo de trabalho (ex: full-time) ou deixe em branco para todos: ").strip()
        
        export = input("Deseja exportar para CSV? (s/n): ").lower() == 's'

        # Se o campo job_type estiver vazio, passamos None para a função
        if not job_type:
            job_type = None
        
        get_jobs(location, company, num_jobs, job_type, save_to_csv=export)

    elif choice == "3":
        skills = input("Digite as habilidades separadas por vírgula: ").split(',')
        data_ini = dt.strptime(input("Digite a data inicial (YYYY-MM-DD): "), '%Y-%m-%d')
        data_fim = dt.strptime(input("Digite a data final (YYYY-MM-DD): "), '%Y-%m-%d')
        export = input("Deseja exportar para CSV? (s/n): ").lower() == 's'
        skills_data(skills, data_ini, data_fim, export_csv=export)
    else:
        print("Opção inválida.")

if __name__ == "__main__":
    main()