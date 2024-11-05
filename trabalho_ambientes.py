import requests
import typer
import json

app = typer.Typer()

# Função para obter os trabalhos mais recentes
def get_recent_jobs(n: int):
    url = "https://www.itjobs.pt/api/docs/jobs"  # Substituir com a rota correta conforme documentação da API
    params = {"limit": n}  # Parâmetro para limitar o número de trabalhos
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()  # Retorna os dados em formato JSON
    else:
        typer.echo("Erro ao acessar a API")
        return None

# CLI command to list recent jobs
@app.command()
def list_recent_jobs(n: int):
    """
    Lista os N trabalhos mais recentes.
    """
    jobs = get_recent_jobs(n)
    if jobs:
        typer.echo(json.dumps(jobs, indent=4))  # Saída formatada em JSON

if __name__ == "__main__":
    app()
