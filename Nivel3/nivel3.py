# nivel3/base.py

"""
Simulador Nível 3 - Borda
Este script simula o Nível 3 do Framework TpM - Borda.

O fluxo de trabalho foi MODIFICADO para ser totalmente dinâmico e configurável:
1. Ao iniciar, carrega todos os seus parâmetros do arquivo 'configuracoes.yaml'.
2. Monta um pacote de requisição de dados (Downlink) para um sensor alvo.
3. "Envia" este pacote escrevendo-o em um arquivo no diretório Nivel2 (Canal).
4. Aguarda por um arquivo de resposta (Uplink).
5. Ao receber a resposta, lê o ID do sensor remetente.
6. Consulta o 'configuracoes.yaml' para obter o "manual de decodificação" daquele sensor.
7. Processa o pacote dinamicamente para extrair os dados de aplicação.
8. Salva os dados coletados em um arquivo de log flexível (JSON Lines).
"""

# --- Importação de Bibliotecas ---
import time
import os
import json # Usaremos JSON para criar as linhas do log
import yaml # Usaremos YAML para ler o arquivo de configuração
from datetime import datetime

print("--- [Nível 3 - Borda] Iniciando Script.")

# --- 1. CARREGAMENTO DA CONFIGURAÇÃO CENTRAL ---
def carregar_configuracao_central():
    """
    Carrega o arquivo de configuração principal (configuracoes.yaml).
    Este arquivo é a "fonte da verdade" para todo o backend.
    Se o arquivo não for encontrado, o programa encerrará, pois não pode operar sem ele.
    """
    caminho_config = os.path.join(os.path.dirname(__file__), '..', 'Nivel4', 'Parametros', 'configuracoes.yaml')
    try:
        with open(caminho_config, 'r', encoding='utf-8') as f:
            print(f"[Nível 3 - Borda] Carregando configurações de '{caminho_config}'...")
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível carregar o arquivo de configuração '{caminho_config}'. Encerrando. Erro: {e}")
        exit()

CONFIG = carregar_configuracao_central()

# --- 2. Definições e Configurações Globais (Lidas do Arquivo) ---
COLETA_ATIVA = CONFIG['nivel3']['ativo']
# Para esta simulação, vamos manter o alvo fixo no sensor 1.
# Em uma versão futura, isso poderia ser uma lista de sensores a serem consultados.
ID_SENSOR_ALVO = 1 
ID_BASE = CONFIG['nivel3']['id_base']
INTERVALO_LEITURA_S = CONFIG['nivel3']['intervalo_leitura_s']
TEMPO_LIMITE_RESPOSTA_S = CONFIG['nivel3']['tempo_limite_resposta_s']
TAMANHO_DO_PACOTE_BYTES = 52

# --- 3. Mapeamento dos Arquivos de Comunicação ---
PASTA_NIVEL2 = os.path.join(os.path.dirname(__file__), '..', 'Nivel2')
CAMINHO_PACOTE_DL = os.path.join(PASTA_NIVEL2, 'pacote_downlink_entrada')
CAMINHO_PACOTE_UL = os.path.join(PASTA_NIVEL2, 'pacote_uplink_saida')

numero_da_tentativa = 0

try:
    while True:
        if not COLETA_ATIVA:
            time.sleep(5)
            continue

        numero_da_tentativa += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [Nível 3 - Borda] [Ciclo N° {numero_da_tentativa}]")

        # ==============================================================================
        # ETAPA A: MONTAR E ENVIAR O PACOTE DE DOWNLINK
        # ==============================================================================
        print("[Nível 3 - Borda] Alocando espaço para o pacote de Downlink...")
        Pacote_DL = [0] * TAMANHO_DO_PACOTE_BYTES
        print(f"[Nível 3 - Borda] - Rede - Endereços do Pacote: Destino=ID {ID_SENSOR_ALVO}, Remetente=ID {ID_BASE}.")
        Pacote_DL[8] = ID_SENSOR_ALVO
        Pacote_DL[10] = ID_BASE
        print(f"[Nível 3 - Borda] - Física - Enviando pacote de {TAMANHO_DO_PACOTE_BYTES} bytes para o canal...")
        with open(CAMINHO_PACOTE_DL, 'wb') as arquivo:
            arquivo.write(bytearray(Pacote_DL))
        print(f"[Nível 3 - Borda] - Pedido de Downlink enviado. Aguardando resposta...")

        # ==============================================================================
        # ETAPA B: AGUARDAR E RECEBER O PACOTE DE RESPOSTA
        # ==============================================================================
        Pacote_UL = None
        inicio_espera = time.time()
        while time.time() - inicio_espera < TEMPO_LIMITE_RESPOSTA_S:
            if os.path.exists(CAMINHO_PACOTE_UL):
                with open(CAMINHO_PACOTE_UL, 'rb') as arquivo_resposta:
                    Pacote_UL = arquivo_resposta.read()
                os.remove(CAMINHO_PACOTE_UL)
                print(f"[Nível 3 - Borda] Pacote de resposta de Uplink recebido!")
                break
            time.sleep(0.5)

        # ==============================================================================
        # ETAPA C: PROCESSAR O PACOTE RECEBIDO
        # ==============================================================================
        status_da_comunicacao = 'Erro'
        dados_decodificados_app = {}
        id_remetente = None
        
        if Pacote_UL and len(Pacote_UL) == TAMANHO_DO_PACOTE_BYTES:
            status_da_comunicacao = 'OK'
            
            rssi_dl_int = Pacote_UL[0]; rssi_downlink_dbm = float(rssi_dl_int - 256 if rssi_dl_int > 127 else rssi_dl_int)
            rssi_ul_int = Pacote_UL[2]; rssi_uplink_dbm = float(rssi_ul_int - 256 if rssi_ul_int > 127 else rssi_ul_int)
            print(f"[Nível 3 - Borda] - MAC - RSSI medido: Uplink={rssi_uplink_dbm:.1f} dBm, Downlink={rssi_downlink_dbm:.1f} dBm.")

            id_remetente = str(Pacote_UL[10])
            contador_sensor = (Pacote_UL[14] << 8) | Pacote_UL[15]
            print(f"[Nível 3 - Borda] - Transporte - Contador de pacotes: {contador_sensor}.")
            
            mapeamento_geral = CONFIG.get('nivel1', {})
            config_sensor = mapeamento_geral.get(id_remetente)
            
            if config_sensor:
                print(f"[Nível 3 - Borda] - Aplicação - Decodificando pacote do Sensor {id_remetente} (Tipo: {config_sensor['tipo_dados']})")
                for instrucao in config_sensor.get('mapeamento_pacote', []):
                    posicao = instrucao['posicao_byte']
                    tamanho = instrucao['tamanho_bytes']
                    escala = instrucao.get('escala', 1)
                    campo = instrucao['campo']
                    bytes_lidos = Pacote_UL[posicao : posicao + tamanho]
                    valor_int = int.from_bytes(bytes_lidos, 'big', signed=True)
                    valor_final = float(valor_int) / escala
                    dados_decodificados_app[campo] = valor_final
                print(f"[Nível 3 - Borda] - Aplicação - Dados decodificados: {dados_decodificados_app}")
            else:
                 print(f"[Nível 3 - Borda] - Aplicação - ERRO: Sensor ID {id_remetente} não encontrado no arquivo de configuração.")
        else:
            print(f"[Nível 3 - Borda] FALHA. Resposta não recebida ou pacote inválido.")

        # ==============================================================================
        # ETAPA D: SALVAR OS DADOS
        # ==============================================================================
        pasta_logs = os.path.join(os.path.dirname(__file__), '..', CONFIG['nivel4']['diretorio_logs'])
        os.makedirs(pasta_logs, exist_ok=True)
        data_hora_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

        # --- Bloco de Log para Dados da Rede (agora em JSON Lines) ---
        caminho_log_rede = os.path.join(pasta_logs, CONFIG['nivel4']['nome_arquivo_rede'])
        
        log_rede_entry = {
            "timestamp": data_hora_atual,
            "id_sensor": int(id_remetente) if id_remetente else None,
            "status": status_da_comunicacao,
            "rssi_uplink_dbm": round(rssi_uplink_dbm, 2) if status_da_comunicacao == 'OK' else None,
            "rssi_downlink_dbm": round(rssi_downlink_dbm, 2) if status_da_comunicacao == 'OK' else None
        }
        
        with open(caminho_log_rede, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_rede_entry) + '\n')
        
        print(f"[Nível 3 - Borda] Log de Rede salvo.")

        # --- Bloco de Log para Dados da Aplicação (JSON Lines) ---
        if status_da_comunicacao == 'OK' and dados_decodificados_app:
            caminho_log_app = os.path.join(pasta_logs, CONFIG['nivel4']['nome_arquivo_aplicacao'])
            log_app_entry = {
                "timestamp": data_hora_atual,
                "id_sensor": int(id_remetente),
                "tipo_sensor": config_sensor.get('tipo_dados', 'Desconhecido'),
                "contador_pacote": contador_sensor,
                "dados": dados_decodificados_app
            }
            with open(caminho_log_app, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_app_entry) + '\n')
            print(f"[Nível 3 - Borda] Log de Aplicação salvo.")

        print(f"[Nível 3 - Borda] Aguardando {INTERVALO_LEITURA_S} segundos...")
        time.sleep(INTERVALO_LEITURA_S)
except KeyboardInterrupt:
    print("\n\n[Nível 3 - Borda] Programa interrompido pelo usuário.")
finally:
    print("[Nível 3 - Borda] Simulação encerrada.")
