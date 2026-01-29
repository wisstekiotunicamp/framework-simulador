# nivel2/simulador_Conectividade.py

"""
Simulador Nível 2 - Conectividade
Este script simula o Nível 2 do Framework TpM - Conectividade.

O fluxo de trabalho foi MODIFICADO para integrar com o Simulador Gráfico:
1. Fica monitorando a chegada de pacotes da Base (Downlink) ou do Sensor (Uplink).
2. A cada ciclo, ele lê um arquivo de configuração ('canal_config.yml') para obter uma
   tabela com os valores de RSSI para CADA SENSOR, calculados pelo Simulador Gráfico.
3. Ao receber um pacote, ele lê seu conteúdo para DESCOBRIR o ID do sensor de origem/destino.
4. Com o ID, ele CONSULTA na tabela o valor de RSSI correto para aquele link específico.
5. "Injeta" esse valor de RSSI nos bytes apropriados do cabeçalho do pacote.
6. Escreve o pacote modificado em um novo arquivo, para que o destinatário final o leia.
"""

# --- Importação de Bibliotecas ---
import os
import time
from datetime import datetime
import yaml

print("--- [NÍVEL 2 - Conectividade] Iniciando Script.")

# --- 1. Mapeamento dos Arquivos de Comunicação ---
PASTA_ATUAL = os.path.dirname(__file__)
CAMINHO_PACOTE_DL_ENTRADA = os.path.join(PASTA_ATUAL, 'pacote_downlink_entrada')
CAMINHO_PACOTE_DL_SAIDA = os.path.join(PASTA_ATUAL, 'pacote_downlink_saida')
CAMINHO_PACOTE_UL_ENTRADA = os.path.join(PASTA_ATUAL, 'pacote_uplink_entrada')
CAMINHO_PACOTE_UL_SAIDA = os.path.join(PASTA_ATUAL, 'pacote_uplink_saida')

# Caminho para o arquivo de configuração que será escrito pelo Simulador Gráfico.
CAMINHO_CONFIG_CANAL = os.path.join(PASTA_ATUAL, 'canal_config.yml')

# --- Função Auxiliar para Ler a Configuração ---
def ler_config_canal():
    """
    Esta função lê o arquivo de configuração do canal (canal_config.yml).
    - Ela é "segura": se o arquivo não existir ou der um erro na leitura,
      ela retorna uma estrutura vazia para o simulador não travar.
    """
    try:
        if os.path.exists(CAMINHO_CONFIG_CANAL):
            with open(CAMINHO_CONFIG_CANAL, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
    except Exception as e:
        print(f"AVISO: Não foi possível ler o arquivo de configuração do canal. Usando valores padrão. Erro: {e}")
    return {'links': {}}

print(f"[NÍVEL 2 - Conectividade] Monitorando arquivos de entrada em: {PASTA_ATUAL}")
print(f"[NÍVEL 2 - Conectividade] Lendo configurações do canal de: {CAMINHO_CONFIG_CANAL}")

try:
    while True:
        # --- Leitura da Configuração a cada Ciclo ---
        config_canal_atual = ler_config_canal()
        tabela_de_links = config_canal_atual.get('links', {})

        # --- FLUXO 1: DOWNLINK (Base -> Sensor) ---
        if os.path.exists(CAMINHO_PACOTE_DL_ENTRADA):
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [NÍVEL 2 - Conectividade] Pacote DOWNLINK (da Base) detectado.")
            
            f_in = open(CAMINHO_PACOTE_DL_ENTRADA, 'rb')
            Pacote_DL_Bytes = f_in.read()
            f_in.close()
            
            Pacote_DL = bytearray(Pacote_DL_Bytes)

            # --- LÓGICA INTELIGENTE: Descobrir para quem é o pacote ---
            id_sensor_destino = str(Pacote_DL[8])
            
            link_especifico = tabela_de_links.get(id_sensor_destino, {})
            rssi_downlink_dbm = link_especifico.get('rssi_downlink_dbm', -120.0)
            
            rssi_int = int(rssi_downlink_dbm)
            print(f"[NÍVEL 2 - Conectividade] Pacote para Sensor ID {id_sensor_destino}. Injetando RSSI de Downlink: {rssi_downlink_dbm:.1f} dBm.")

            Pacote_DL[0] = rssi_int & 0xFF

            f_out = open(CAMINHO_PACOTE_DL_SAIDA, 'wb')
            f_out.write(Pacote_DL)
            f_out.close()
            
            os.remove(CAMINHO_PACOTE_DL_ENTRADA)
            print("[NÍVEL 2 - Conectividade] Pacote de Downlink repassado para o Nível 1 (Nó Sensor).")

        # --- FLUXO 2: UPLINK (Nó Sensor -> Borda) ---
        if os.path.exists(CAMINHO_PACOTE_UL_ENTRADA):
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [NÍVEL 2 - Conectividade] Pacote Uplink (do Nó Sensor) detectado.")
            
            f_in = open(CAMINHO_PACOTE_UL_ENTRADA, 'rb')
            Pacote_UL_Bytes = f_in.read()
            f_in.close()
            
            Pacote_UL = bytearray(Pacote_UL_Bytes)

            # --- LÓGICA INTELIGENTE: Descobrir de quem veio o pacote ---
            id_sensor_origem = str(Pacote_UL[10])
            
            link_especifico = tabela_de_links.get(id_sensor_origem, {})
            rssi_uplink_dbm = link_especifico.get('rssi_uplink_dbm', -120.0)

            rssi_int = int(rssi_uplink_dbm)
            print(f"[NÍVEL 2 - Conectividade] Pacote do Sensor ID {id_sensor_origem}. Injetando RSSI de Uplink: {rssi_uplink_dbm:.1f} dBm.")
            
            Pacote_UL[2] = rssi_int & 0xFF

            f_out = open(CAMINHO_PACOTE_UL_SAIDA, 'wb')
            f_out.write(Pacote_UL)
            f_out.close()
            
            os.remove(CAMINHO_PACOTE_UL_ENTRADA)
            print("[NÍVEL 2 - Conectividade] Pacote de Uplink repassado para o Nível 3 (Base).")

        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n[NÍVEL 2 - Conectividade] Simulador encerrado pelo usuário.")
