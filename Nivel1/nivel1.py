# nivel1/no_sensor.py

"""
Simulador Nível 1 - Nó Sensor
Este script simula o Nível 1 do Framework TpM - Nó Sensor.

O fluxo de trabalho foi MODULARIZADO:
1. Ao ser iniciado, lê um argumento de linha de comando (--id) para saber sua identidade.
2. Fica continuamente verificando se um arquivo de requisição (Downlink) existe.
3. Ao encontrar um pedido, ele lê um arquivo de configuração local ('sensores_config.yml')
   para descobrir QUAL arquivo de script de dados deve usar (ex: 'clima.py').
4. Importa e executa dinamicamente a função 'get_data()' desse script.
5. Segue as instruções de 'mapeamento_pacote' para colocar os dados nos bytes corretos.
6. Monta o restante do pacote de resposta (Uplink).
7. Envia a resposta escrevendo-a em um arquivo no diretório Nivel2.
"""

# --- Importação de Bibliotecas ---
import os
import time
import yaml
from datetime import datetime
import argparse      # Biblioteca para ler argumentos da linha de comando
import importlib.util # Biblioteca para importar módulos dinamicamente
import sys

print("--- [Nível 1 - Nó Sensor] Iniciando Script.")

# --- 1. LÓGICA DE INICIALIZAÇÃO: DESCOBRIR A PRÓPRIA IDENTIDADE ---
parser = argparse.ArgumentParser(description="Simulador de Nó Sensor Genérico.")
parser.add_argument("--id", type=int, required=True, help="ID numérico único para este nó sensor.")
args = parser.parse_args()

MEU_ID = args.id
print(f"[Nível 1 - Nó Sensor] Eu sou o Sensor de ID = {MEU_ID}.")

# --- 2. Definições e Configurações Globais ---
ID_BASE = 0
TAMANHO_PACOTE = 52
contador_pacotes_enviados = 0

# --- 3. Mapeamento dos Arquivos de Comunicação ---
PASTA_ATUAL = os.path.dirname(__file__)
PASTA_NIVEL2 = os.path.join(PASTA_ATUAL, '..', 'Nivel2')
CAMINHO_PACOTE_DL = os.path.join(PASTA_NIVEL2, 'pacote_downlink_saida')
CAMINHO_PACOTE_UL = os.path.join(PASTA_NIVEL2, 'pacote_uplink_entrada')
CAMINHO_CONFIG_SENSORES = os.path.join(PASTA_ATUAL, 'sensores_config.yml')
CAMINHO_DATA_SOURCE = os.path.join(PASTA_ATUAL, 'data_source')

# --- Funções Auxiliares ---
def ler_minha_configuracao(id_do_meu_sensor):
    """Lê o arquivo de configuração e retorna as instruções específicas para este sensor."""
    config_padrao = {'source_file': None, 'mapeamento_pacote': {}}
    try:
        if os.path.exists(CAMINHO_CONFIG_SENSORES):
            with open(CAMINHO_CONFIG_SENSORES, 'r', encoding='utf-8') as f:
                config_completa = yaml.safe_load(f)
                return config_completa.get('config_sensores', {}).get(str(id_do_meu_sensor), config_padrao)
    except Exception as e:
        print(f"AVISO: Erro ao ler config de sensores. Usando configuração padrão. Erro: {e}")
    return config_padrao

def carregar_e_executar_funcao(nome_arquivo_fonte):
    """
    Importa dinamicamente um módulo do diretório 'data_source' e executa sua função 'get_data'.
    """
    if not nome_arquivo_fonte:
        print("[Nível 1 - Nó Sensor] - APLICAÇÃO - ERRO: Nenhum arquivo de fonte de dados especificado.")
        return None
        
    try:
        caminho_modulo = os.path.join(CAMINHO_DATA_SOURCE, nome_arquivo_fonte)
        # Especificação para carregar o módulo a partir do seu caminho de arquivo
        spec = importlib.util.spec_from_file_location(nome_arquivo_fonte, caminho_modulo)
        # Cria um novo módulo vazio baseado na especificação
        modulo_fonte = importlib.util.module_from_spec(spec)
        # Adiciona o módulo ao sistema para que ele possa ser "encontrado"
        sys.modules[spec.name] = modulo_fonte
        # Executa o código do módulo, o que define a função get_data()
        spec.loader.exec_module(modulo_fonte)
        
        print(f"[Nível 1 - Nó Sensor] - Aplicação - Executando get_data() de '{nome_arquivo_fonte}'...")
        # Chama a função get_data() do módulo que acabamos de carregar
        return modulo_fonte.get_data()
    except Exception as e:
        print(f"[Nível 1 - Nó Sensor] - APLICAÇÃO - ERRO: Falha ao carregar ou executar '{nome_arquivo_fonte}'. Erro: {e}")
        return None


print(f"[Nível 1 - Nó Sensor] Monitorando pacote de Downlink...")

try:
    while True:
        if os.path.exists(CAMINHO_PACOTE_DL):
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [Nível 1 - Nó Sensor] Pacote de Downlink detectado!")

            # ==========================================================================
            # ETAPA A: PROCESSAR PACOTE RECEBIDO
            # ==========================================================================
            arquivo_pacote_dl = open(CAMINHO_PACOTE_DL, 'rb')
            Pacote_DL = arquivo_pacote_dl.read()
            arquivo_pacote_dl.close()
            os.remove(CAMINHO_PACOTE_DL)

            print("[Nível 1 - Nó Sensor] - MAC - Extraindo RSSI do Downlink")
            rssi_dl_byte = Pacote_DL[0]

            id_destinatario = Pacote_DL[8]
            print(f"[Nível 1 - Nó Sensor] - Rede -  Pacote para o ID={id_destinatario}, Meu ID={MEU_ID}.")
            
            if id_destinatario == MEU_ID:
                # ==========================================================================
                # ETAPA B: MONTAR PACOTE DE RESPOSTA
                # ==========================================================================
                Pacote_UL = [0] * TAMANHO_PACOTE

                # --- Camada 4: APLICAÇÃO ---
                print("[Nível 1 - Nó Sensor] - Aplicação -   Verificando configuração de dados...")
                
                minha_config = ler_minha_configuracao(MEU_ID)
                arquivo_fonte = minha_config.get('source_file')
                mapeamento = minha_config.get('mapeamento_pacote', {})
                
                # 1. Carrega e executa dinamicamente a função de coleta de dados.
                dados = carregar_e_executar_funcao(arquivo_fonte)
                
                # 2. Lógica de empacotamento DINÂMICO
                if dados and mapeamento:
                    print(f"[Nível 1 - Nó Sensor] - Aplicação - Empacotando dados conforme mapeamento:")
                    for nome_campo, instrucoes in mapeamento.items():
                        if nome_campo in dados:
                            posicao = instrucoes['posicao_byte']
                            tamanho = instrucoes['tamanho_bytes']
                            escala = instrucoes.get('escala', 1)
                            
                            valor = dados[nome_campo]
                            valor_int = int(valor * escala)
                            
                            print(f"  - Campo '{nome_campo}': {valor} -> {valor_int} -> Posição {posicao}")
                            
                            bytes_valor = valor_int.to_bytes(tamanho, 'big', signed=True)
                            for i in range(tamanho):
                                Pacote_UL[posicao + i] = bytes_valor[i]
                elif dados is None:
                    print("[Nível 1 - Nó Sensor] - Aplicação - ERRO: Não foi possível obter dados da fonte.")

                # --- Camada 3: TRANSPORTE ---
                contador_pacotes_enviados += 1
                Pacote_UL[14] = (contador_pacotes_enviados >> 8) & 0xFF
                Pacote_UL[15] = contador_pacotes_enviados & 0xFF
                print(f"[Nível 1 - Nó Sensor] - Transporte -  Contador de pacotes incrementado para {contador_pacotes_enviados}.")
                
                # --- Camada 2: REDE ---
                Pacote_UL[8] = ID_BASE
                Pacote_UL[10] = MEU_ID # Usa o ID que foi lido da linha de comando
                print(f"[Nível 1 - Nó Sensor] - Rede -  Destino=ID {ID_BASE}, Remetente=ID {MEU_ID}.")

                # --- Camada 1: MAC ---
                print("[Nível 1 - Nó Sensor] - MAC - Escrevendo RSSI de Downlink no pacote de resposta.")
                Pacote_UL[0] = rssi_dl_byte

                arquivo_resp = open(CAMINHO_PACOTE_UL, 'wb')
                arquivo_resp.write(bytearray(Pacote_UL))
                arquivo_resp.close()

                print(f"[Nível 1 - Nó Sensor] - Resposta de Uplink enviada para o canal.")
            else:
                print("[Nível 1 - Nó Sensor] - Rede - ERRO: Pacote descartado, ID de destinatário não corresponde ao meu.")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n[Nível 1 - Nó Sensor] Simulador encerrado pelo usuário.")
