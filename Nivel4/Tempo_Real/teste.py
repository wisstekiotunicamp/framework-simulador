import requests
import json
import os
import sys

# --- Configuração ---
OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODELO_OLLAMA = "llama3"
NOME_ARQUIVO_DADOS = "dados_brutos_rede.jsonl"

def carregar_dados_jsonl(filepath):
    """
    Carrega os dados do arquivo .jsonl 'em tempo real'.
    Lê cada linha como um objeto JSON separado.
    """
    if not os.path.exists(filepath):
        print(f"Erro: Arquivo '{filepath}' não encontrado.", file=sys.stderr)
        return []
        
    dados = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    linha_limpa = line.strip()
                    if linha_limpa:
                        dados.append(json.loads(linha_limpa))
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}", file=sys.stderr)
    return dados

#
# --- MUDANÇA NÍVEL 1: LÓGICA DE REGRAS NO PYTHON ---
#
def classificar_rssi(rssi_valor):
    """
    Aplica as regras de negócio DIRETAMENTE no Python.
    """
    if rssi_valor > -60:
        return "Excelente"
    if rssi_valor > -90:
        return "Bom"
    if rssi_valor > -110:
        return "Fraco"
    return "Crítico"

def classificar_perda_pacotes(taxa_perda):
    """
    Aplica as regras de perda de pacotes DIRETAMENTE no Python.
    """
    if taxa_perda == 0:
        return "Excelente (0%)"
    if taxa_perda <= 5:
        return "Aceitável"
    return "Ruim (investigar)"

def processar_canal_rssi(lista_valores):
    """
    Helper para calcular estatísticas de uma lista de RSSI.
    """
    if not lista_valores:
        return {
            "analise_disponivel": False,
            "erro": "Nenhum dado deste tipo encontrado."
        }
    
    media = round(sum(lista_valores) / len(lista_valores), 2)
    min_val = min(lista_valores)
    max_val = max(lista_valores)
    # Classifica a MÉDIA (poderia ser o MÍNIMO, dependendo da regra)
    classificacao = classificar_rssi(media)
    
    return {
        "analise_disponivel": True,
        "rssi_medio_dbm": media,
        "rssi_min_dbm": min_val,
        "rssi_max_dbm": max_val,
        "classificacao_sinal": classificacao # <--- Python já classifica!
    }

def pre_processar_dados(dados_lista):
    """
    Usa o Python para o que ele faz de melhor: matemática e lógica.
    Agora pré-classifica TODOS os dados antes de enviar ao LLM.
    """
    if not dados_lista:
        return {"erro": "Nenhum dado válido encontrado."}

    try:
        # --- Cálculo de RSSI (UPLINK E DOWNLINK) ---
        # O arquivo de dados contém ambos 
        valores_rssi_uplink = [d['rssi_uplink_dbm'] for d in dados_lista if 'rssi_uplink_dbm' in d]
        valores_rssi_downlink = [d['rssi_downlink_dbm'] for d in dados_lista if 'rssi_downlink_dbm' in d]

        # --- Cálculo de Perda de Pacotes ---
        total_pacotes = len(dados_lista)
        pacotes_ok = sum(1 for d in dados_lista if d.get('status') == 'OK') # 
        pacotes_perdidos = total_pacotes - pacotes_ok
        taxa_perda = (pacotes_perdidos / total_pacotes) * 100 if total_pacotes > 0 else 0
        
        # --- Coleta de Metadados ---
        primeiro_timestamp = dados_lista[0].get('timestamp', 'N/A') # [cite: 1]
        ultimo_timestamp = dados_lista[-1].get('timestamp', 'N/A') # [cite: 6]
        id_sensor = dados_lista[0].get('id_sensor', 'N/A') # [cite: 1]

        # --- Geração do Sumário PRÉ-ANALISADO ---
        return {
            "id_sensor_analisado": id_sensor,
            "periodo_analise": f"de {primeiro_timestamp} até {ultimo_timestamp}",
            
            "sumario_pacotes": {
                "total_pacotes_registrados": total_pacotes,
                "pacotes_perdidos_ou_falha": pacotes_perdidos,
                "taxa_perda_pacotes_percent": round(taxa_perda, 2),
                "classificacao_pacotes": classificar_perda_pacotes(taxa_perda)
            },
            
            "sumario_sinal_uplink": processar_canal_rssi(valores_rssi_uplink),
            
            "sumario_sinal_downlink": processar_canal_rssi(valores_rssi_downlink)
        }
    except Exception as e:
        return {"erro": f"Erro no processamento dos dados: {e}"}

#
# --- MUDANÇA NÍVEL 2: SIMPLIFICANDO O PROMPT DO LLM ---
#
def chamar_analista_llm(pergunta_usuario, sumario_dados):
    """
    Chama o LLM local (Ollama).
    O LLM agora é um "tradutor" de JSON para linguagem natural.
    """
    
    # O prompt agora é muito mais "burro" e direto.
    # Ele não contém mais as REGRAS.
    prompt_sistema = """
Você é um assistente de análise de rede. Você receberá um SUMÁRIO DE DADOS
que já foi pré-processado e pré-classificado por um script Python.

Sua ÚNICA tarefa é usar os dados desse sumário para responder à pergunta
do usuário de forma direta.

**INSTRUÇÕES DE RESPOSTA:**
- **NUNCA invente classificações** (como 'Fraco', 'Bom'). Use *exatamente*
  a classificação fornecida no JSON (ex: "classificacao_sinal": "Excelente").
- **ATEIA-SE AOS FATOS.** Não dê definições genéricas sobre LoRa ou RSSI.
- Se o usuário perguntar sobre "Downlink", use os dados de "sumario_sinal_downlink".
- Se o usuário perguntar sobre "Uplink", use os dados de "sumario_sinal_uplink".
- Se o usuário perguntar "qualidade do sinal", reporte a "classificacao_sinal".
"""

    prompt_usuario = f"""
    --- INÍCIO DO SUMÁRIO PRÉ-ANALISADO ---
    {json.dumps(sumario_dados, indent=2)}
    --- FIM DO SUMÁRIO PRÉ-ANALISADO ---

    Pergunta do Usuário: "{pergunta_usuario}"

    Sua resposta (baseada *apenas* no sumário acima):
    """

    payload = {
        "model": MODELO_OLLAMA,
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ],
        "stream": True
    }

    print("\n[Analista LLM]:")
    try:
        response = requests.post(
            OLLAMA_API_URL, 
            data=json.dumps(payload), 
            stream=True, 
            timeout=(10, 300)
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    content_piece = chunk['message']['content']
                    print(content_piece, end="", flush=True)

                except json.JSONDecodeError:
                    print(f"Erro ao decodificar um pedaço do stream: {line}")
        
        print()

    except requests.exceptions.ConnectionError:
        print("ERRO FATAL: Não foi possível conectar ao Ollama. Verifique se ele está rodando.")
    except requests.exceptions.RequestException as e:
        print(f"ERRO na API do Ollama: {e}")

#
# --- NENHUMA MUDANÇA ABAIXO ---
#
def main():
    """
    Loop principal de chat interativo.
    """
    print("--- Analista de Rede LoRa (Ollama + Python) ---")
    print(f"Monitorando o arquivo: '{NOME_ARQUIVO_DADOS}'")
    print("Conectando ao modelo: '" + MODELO_OLLAMA + "' via " + OLLAMA_API_URL)
    print("Faça sua pergunta sobre os dados (ou digite 'sair' para terminar).")
    print("-" * 50)

    while True:
        try:
            pergunta = input("\n[Você]: ")
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("Até logo!")
                break
                
            dados_brutos = carregar_dados_jsonl(NOME_ARQUIVO_DADOS)
            if not dados_brutos:
                print("[Sistema]: Não foi possível ler os dados ou o arquivo está vazio.")
                continue

            sumario_estatistico = pre_processar_dados(dados_brutos)
            
            print("[Sistema]: Analisando... (a resposta aparecerá em tempo real)")
            
            chamar_analista_llm(pergunta, sumario_estatistico)

        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
