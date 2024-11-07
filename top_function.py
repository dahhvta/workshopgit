import requests
import math
import json
import typer

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
    global general_results, cache_loaded
    
    # Verifica se já existem dados carregados
    if cache_loaded:
        return general_results

    URL = 'https://api.itjobs.pt/job/list.json?api_key=9fa7ce317d6e85c90d92244adb9146c6'
    print("Pedindo informações à API, pode demorar um tempo...")
    
    request = requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
    total_pages = math.ceil(request.json()['total']/12)
    
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page':rep+1},headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'}).json()
        general_results.extend(datasets['results'])
    
    cache_loaded = True 
    return general_results

@app.command()
def top(n: int):
    """
    Função para mostrar as 'n' vagas mais recentes.
    Exibe algumas informações selecionadas sobre as vagas.
    
    Para a alinea A não é preciso fazer nenhum tipo de sort pois os primeiros valores a serem adicionados
    são os mais recentes.
    """
    general_data = getdata()  # Obtém dados da API ou cache

    data_top = {}

    # Exibe os dados das 'n' vagas mais recentes    
    for item in general_data[0:n]:  
        data_top[item['id']]={
            'job_title': item['title'],
            'company': item['company']['name'],
            'company_description': item['company']['description'],
            'published_at': item['publishedAt'],
            'salary': item.get('wage', 'N/A'),
            'location': item['locations'][0]['name'] if item.get('locations') else 'N/A',
            #'url': item.get('company', {}).get('url', 'N/A'),
            #'employment_type': item.get('types', [{}])[0].get('name', 'N/A'),
        }
        
    print(json.dumps(data_top,indent=4))

if __name__ == "__main__":
    app()