# simulation_models.py
import math
from explanation_windows import FSLExplanationWindow, LogDistanceExplanationWindow

# --- Funções de Cálculo para cada Modelo ---

def calculate_fspl_rssi(node_tx, node_rx, params):
    """ 
    Calcula o RSSI usando o Espaço Livre.
    Aceita um dicionário 'params' para consistência.
    """
    distance_m = params['d_m']
    freq_mhz = params['freq_mhz']
    
    if distance_m <= 0 or freq_mhz <= 0:
        return -math.inf, math.inf
    
    # Fórmula de Perda de Percurso (Path Loss) para Espaço Livre
    path_loss = 20 * math.log10(distance_m) + 20 * math.log10(freq_mhz) - 27.55
    rssi = node_tx['power_dbm'] + node_tx['gain_dbi'] + node_rx['gain_dbi'] - path_loss
    
    return rssi, path_loss

def calculate_log_distance_rssi(node_tx, node_rx, params):
    """ 
    Calcula o RSSI usando o modelo Log-Distância.
    Usa os parâmetros beta (n) e d0.
    """
    distance_m = params['d_m']
    freq_mhz = params['freq_mhz']
    d0 = params['d0']   # Distância de Referência
    beta = params['beta'] # Coeficiente Beta (Expoente n)

    if distance_m <= 0 or freq_mhz <= 0 or d0 <= 0:
        return -math.inf, math.inf

    # 1. Calcula a Perda de Percurso na referência (PL0)
    #    Usa a fórmula do Espaço Livre para a distância d0
    pl_0 = 20 * math.log10(d0) + 20 * math.log10(freq_mhz) - 27.55
    
    # 2. Calcula a Perda de Percurso (Path Loss) total
    if distance_m <= d0:
        # Se estiver mais perto que a referência, a perda é a de referência
        path_loss = pl_0
    else:
        # Se estiver mais longe, aplica o Coeficiente Beta
        path_loss = pl_0 + 10 * beta * math.log10(distance_m / d0)

    # 3. Calcula o RSSI
    rssi = node_tx['power_dbm'] + node_tx['gain_dbi'] + node_rx['gain_dbi'] - path_loss
    
    return rssi, path_loss

# --- REGISTRO CENTRAL DE MODELOS ---
MODELS = {
    "Espaço Livre": {
        "calculator": calculate_fspl_rssi,
        "explanation_class": FSLExplanationWindow,
        "params": [] # Este modelo não tem parâmetros extras
    },
    "Log-Distância": {
        "calculator": calculate_log_distance_rssi,
        "explanation_class": LogDistanceExplanationWindow, 
        "params": ["d0", "beta"] # Parâmetros que este modelo requer
    },
}

