# Nivel1/data_source/clima.py
import requests

def get_data():
    """
    Tenta obter dados de temperatura e umidade da API Open-Meteo.
    Retorna um dicionário com os dados ou None em caso de falha.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-22.9056&longitude=-47.0608&current=temperature_2m,relative_humidity_2m"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'temperatura': float(data['current']['temperature_2m']),
            'umidade': float(data['current']['relative_humidity_2m'])
        }
    except Exception as e:
        print(f"[Fonte de Dados: clima.py] AVISO: Falha na API. Erro: {e}")
        return None
