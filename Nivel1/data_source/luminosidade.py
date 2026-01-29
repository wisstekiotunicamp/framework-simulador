# Nivel1/data_source/luminosidade.py
import random

def get_data():
    """
    Gera um dado aleatório de luminosidade (em Lux) para simulação.
    Retorna um dicionário com o dado.
    """
    return {'luminosidade_lux': random.randint(100, 2000)}
