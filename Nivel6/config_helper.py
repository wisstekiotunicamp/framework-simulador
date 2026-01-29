# Nivel6/config_helper.py
import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'Nivel4', 'Parametros', 'configuracoes.yaml')

def get_default_config():
    """Retorna a estrutura de configuração padrão (baseada na sua proposta)."""
    return {
        'nivel3': {
            'ativo': True,
            'intervalo_leitura_s': 10,
            'id_base': 0,
            'tempo_limite_resposta_s': 20
        },
        'nivel4': {
            'diretorio_logs': 'Nivel4/Tempo_Real',
            'nome_arquivo_rede': 'dados_brutos_rede.jsonl',
            'nome_arquivo_aplicacao': 'dados_brutos_aplicacao.jsonl'
        },
        'nivel1': {
            '1': {
                'descricao': 'Sensor de Exemplo (Clima)', # PONTO 3
                'tipo_dados': 'Clima',                   # PONTO 5 (Mantido)
                'log_headers': ['Data e Hora', 'Contador', 'Temperatura (C)', 'Umidade (%)'],
                'mapeamento_pacote': [
                    {
                        'campo': 'temperatura',
                        'posicao_byte': 16,
                        'tamanho_bytes': 2,
                        'escala': 10
                    }
                ]
            }
        }
    }

def ler_config():
    """Lê o arquivo de configuração YAML."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if not config:
                return get_default_config()
                
            # Garante que as chaves principais existam
            if 'nivel3' not in config: config['nivel3'] = get_default_config()['nivel3']
            if 'nivel4' not in config: config['nivel4'] = get_default_config()['nivel4']
            if 'nivel1' not in config: config['nivel1'] = get_default_config()['nivel1']
            
            # PONTO 3: Garante que 'descricao' exista (para compatibilidade)
            for k, v in config['nivel1'].items():
                if 'descricao' not in v:
                    v['descricao'] = v.get('tipo_dados', f"Nó Sensor ID {k}")
            
            return config
    except FileNotFoundError:
        print("Arquivo de configuração não encontrado. Criando um padrão.")
        default_config = get_default_config()
        salvar_config(default_config) # Cria o arquivo padrão
        return default_config
    except Exception as e:
        print(f"Erro ao ler config: {e}. Usando padrão.")
        return get_default_config()

def salvar_config(data):
    """Salva o dicionário de dados no arquivo de configuração YAML."""
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar configuração: {e}")
        return False
