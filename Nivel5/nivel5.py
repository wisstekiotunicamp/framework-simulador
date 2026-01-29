# Nivel5/analise.py

import os
import time
import csv
from datetime import datetime

print("--- [NÍVEL 5 - ANÁLISE] Iniciando Script de Análise de Dados ---")

# --- 1. Configurações ---
CONFIG = {
    # Intervalo em segundos entre cada ciclo de análise.
    'INTERVALO_ANALISE_S': 10,
    
    # Número de 'N' últimas amostras para calcular a média móvel.
    'JANELA_MEDIA_MOVEL': 5,

    # Nomes dos arquivos de entrada (gerados pela base).
    'ARQUIVO_DADOS_REDE': 'dados_brutos_rede.csv',
    'ARQUIVO_DADOS_APP': 'dados_brutos_aplicacao.csv',

    # Nomes dos arquivos de saída (com as estatísticas).
    'ARQUIVO_STATS_REDE': 'estatisticas_rede.csv',
    'ARQUIVO_STATS_APP': 'estatisticas_aplicacao.csv'
}

# --- 2. Definição dos Caminhos (Paths) ---
PASTA_NIVEL4 = os.path.join(os.path.dirname(__file__), '..', 'Nivel4')
PASTA_ENTRADA = os.path.join(PASTA_NIVEL4, 'Tempo_Real')
PASTA_SAIDA = os.path.join(PASTA_NIVEL4, 'Tempo_Nao_Real')
os.makedirs(PASTA_SAIDA, exist_ok=True)

CAMINHO_DADOS_REDE = os.path.join(PASTA_ENTRADA, CONFIG['ARQUIVO_DADOS_REDE'])
CAMINHO_DADOS_APP = os.path.join(PASTA_ENTRADA, CONFIG['ARQUIVO_DADOS_APP'])
CAMINHO_STATS_REDE = os.path.join(PASTA_SAIDA, CONFIG['ARQUIVO_STATS_REDE'])
CAMINHO_STATS_APP = os.path.join(PASTA_SAIDA, CONFIG['ARQUIVO_STATS_APP'])

print(f"[NÍVEL 5 - ANÁLISE] Lendo dados de: {PASTA_ENTRADA}")
print(f"[NÍVEL 5 - ANÁLISE] Salvando estatísticas em: {PASTA_SAIDA}")
print(f"[NÍVEL 5 - ANÁLISE] Janela de análise (N): {CONFIG['JANELA_MEDIA_MOVEL']} amostras")
print(f"[NÍVEL 5 - ANÁLISE] Intervalo entre análises: {CONFIG['INTERVALO_ANALISE_S']} segundos")

# --- 3. Loop Principal de Análise ---
try:
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [NÍVEL 5 - ANÁLISE] Novo ciclo de análise...")
        
        # ======================================================================
        # ETAPA A: Análise de Aplicação (Temperatura e Umidade)
        # ======================================================================
        print(" > Processando dados de APLICAÇÃO...")
        media_temp = 0.0
        media_umid = 0.0
        
        try:
            if os.path.exists(CAMINHO_DADOS_APP):
                with open(CAMINHO_DADOS_APP, 'r', newline='', encoding='utf-8') as f:
                    leitor = csv.DictReader(f, delimiter=';')
                    todos_os_dados = list(leitor)
                
                ultimas_n_linhas = todos_os_dados[-CONFIG['JANELA_MEDIA_MOVEL']:]

                if ultimas_n_linhas:
                    soma_temp, contagem_temp = 0.0, 0
                    soma_umid, contagem_umid = 0.0, 0
                    
                    for linha in ultimas_n_linhas:
                        try:
                            temp_str = linha.get('Temperatura (C)', '').strip()
                            if temp_str:
                                soma_temp += float(temp_str)
                                contagem_temp += 1
                        except (ValueError, TypeError): continue
                        
                        try:
                            umid_str = linha.get('Umidade (%)', '').strip()
                            if umid_str:
                                soma_umid += float(umid_str)
                                contagem_umid += 1
                        except (ValueError, TypeError): continue

                    if contagem_temp > 0: media_temp = round(soma_temp / contagem_temp, 2)
                    if contagem_umid > 0: media_umid = round(soma_umid / contagem_umid, 2)
        except Exception as e:
            print(f"   - ERRO ao processar arquivo de aplicação: {e}")

        print(f"   - Média de Temperatura (últimas {CONFIG['JANELA_MEDIA_MOVEL']}): {media_temp:.2f}°C")
        print(f"   - Média de Umidade (últimas {CONFIG['JANELA_MEDIA_MOVEL']}): {media_umid:.2f}%")

        if not os.path.exists(CAMINHO_STATS_APP):
            with open(CAMINHO_STATS_APP, 'w', newline='', encoding='utf-8') as f:
                escritor = csv.writer(f, delimiter=';')
                escritor.writerow(['Timestamp', 'Media_Temperatura_C', 'Media_Umidade_pct'])
        
        with open(CAMINHO_STATS_APP, 'a', newline='', encoding='utf-8') as f:
            escritor = csv.writer(f, delimiter=';')
            timestamp_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            escritor.writerow([timestamp_atual, f"{media_temp:.2f}", f"{media_umid:.2f}"])
        
        print("   - Estatísticas de aplicação salvas.")

        # ======================================================================
        # ETAPA B: Análise de Rede (RSSI)
        # ======================================================================
        print(" > Processando dados de REDE...")
        media_rssi_up = 0.0
        media_rssi_down = 0.0

        try:
            if os.path.exists(CAMINHO_DADOS_REDE):
                with open(CAMINHO_DADOS_REDE, 'r', newline='', encoding='utf-8') as f:
                    leitor = csv.DictReader(f, delimiter=';')
                    todos_os_dados_rede = list(leitor)

                ultimas_n_linhas_rede = todos_os_dados_rede[-CONFIG['JANELA_MEDIA_MOVEL']:]

                if ultimas_n_linhas_rede:
                    soma_up, contagem_up = 0.0, 0
                    soma_down, contagem_down = 0.0, 0

                    for linha in ultimas_n_linhas_rede:
                        try:
                            up_str = linha.get('RSSI_Uplink_dBm', '').strip()
                            if up_str:
                                soma_up += float(up_str)
                                contagem_up += 1
                        except (ValueError, TypeError): continue

                        try:
                            down_str = linha.get('RSSI_Downlink_dBm', '').strip()
                            if down_str:
                                soma_down += float(down_str)
                                contagem_down += 1
                        except (ValueError, TypeError): continue
                    
                    if contagem_up > 0: media_rssi_up = round(soma_up / contagem_up, 2)
                    if contagem_down > 0: media_rssi_down = round(soma_down / contagem_down, 2)
        except Exception as e:
            print(f"   - ERRO ao processar arquivo de rede: {e}")

        print(f"   - Média de RSSI Uplink (últimas {CONFIG['JANELA_MEDIA_MOVEL']}): {media_rssi_up:.2f} dBm")
        print(f"   - Média de RSSI Downlink (últimas {CONFIG['JANELA_MEDIA_MOVEL']}): {media_rssi_down:.2f} dBm")

        if not os.path.exists(CAMINHO_STATS_REDE):
            with open(CAMINHO_STATS_REDE, 'w', newline='', encoding='utf-8') as f:
                escritor = csv.writer(f, delimiter=';')
                escritor.writerow(['Timestamp', 'Media_RSSI_Uplink_dBm', 'Media_RSSI_Downlink_dBm'])

        with open(CAMINHO_STATS_REDE, 'a', newline='', encoding='utf-8') as f:
            escritor = csv.writer(f, delimiter=';')
            timestamp_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            escritor.writerow([timestamp_atual, f"{media_rssi_up:.2f}", f"{media_rssi_down:.2f}"])

        print("   - Estatísticas de rede salvas.")

        # ======================================================================
        # ETAPA C: Aguardar para o próximo ciclo
        # ======================================================================
        intervalo = CONFIG['INTERVALO_ANALISE_S']
        print(f"[NÍVEL 5 - ANÁLISE] Aguardando {intervalo} segundos para o próximo ciclo...")
        time.sleep(intervalo)

except KeyboardInterrupt:
    print("\n\n[NÍVEL 5 - ANÁLISE] Programa interrompido pelo usuário.")
finally:
    print("[NÍVEL 5 - ANÁLISE] Análise encerrada.")
