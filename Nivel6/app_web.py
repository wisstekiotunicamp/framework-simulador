# Nivel6/app_web.py
import os
import sys
import json
from flask import Flask, render_template, request, jsonify, url_for

sys.path.append(os.path.dirname(__file__))
import config_helper

app = Flask(__name__)

# Define o caminho base para os logs
LOG_DIR_PATH_BASE = os.path.join(os.path.dirname(__file__), '..')

def get_log_filepath(log_type='aplicacao'):
    """Lê a config e retorna o caminho completo do arquivo de log."""
    config = config_helper.ler_config()
    config_n4 = config.get('nivel4', {})
    
    dir_logs = config_n4.get('diretorio_logs', 'Nivel4/Tempo_Real')
    
    if log_type == 'rede':
        filename = config_n4.get('nome_arquivo_rede', 'dados_brutos_rede.jsonl')
    else:
        filename = config_n4.get('nome_arquivo_aplicacao', 'dados_brutos_aplicacao.jsonl')
        
    # Constrói o caminho completo a partir da raiz do projeto
    return os.path.join(LOG_DIR_PATH_BASE, dir_logs, filename)


def get_lista_sensores_para_dropdown():
    """
    PONTO 3: Lê a config e retorna uma lista de (id, descricao) para os dropdowns.
    """
    config = config_helper.ler_config()
    sensores_config = config.get('nivel1', {})
    lista_sensores = []
    for id_sensor, dados_sensor in sensores_config.items():
        # Usa o novo campo 'descricao'
        nome = dados_sensor.get('descricao', f"Nó Sensor ID {id_sensor}")
        lista_sensores.append((id_sensor, nome))
    return lista_sensores


@app.route('/') # Rota raiz
@app.route('/dashboard_dados') # Rota explícita
def dashboard_dados():
    """Renderiza o dashboard de dados de aplicação."""
    lista_sensores = get_lista_sensores_para_dropdown()
    return render_template('dashboard_dados.html', sensores=lista_sensores)


# PONTO 2: Nova Rota para Dashboard de Rede
@app.route('/dashboard_rede')
def dashboard_rede():
    """Renderiza o dashboard de dados de rede (RSSI)."""
    lista_sensores = get_lista_sensores_para_dropdown()
    return render_template('dashboard_rede.html', sensores=lista_sensores)


@app.route('/configuracao')
def configuracao():
    """Renderiza a página de configuração."""
    config = config_helper.ler_config()
    return render_template('configuracao.html', config=config)


@app.route('/api/salvar_config', methods=['POST'])
def api_salvar_config():
    """API para salvar a configuração completa no .yaml"""
    nova_config = request.json
    if not nova_config:
        return jsonify(success=False, error="Nenhum dado recebido."), 400
    try:
        if config_helper.salvar_config(nova_config):
            return jsonify(success=True, message="Configuração salva com sucesso!")
        else:
            return jsonify(success=False, error="Falha ao salvar o arquivo."), 500
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/api/dados_sensor/<sensor_id>')
def api_dados_sensor(sensor_id):
    """API para ler o log de APLICAÇÃO e retornar dados para o Chart.js."""
    config = config_helper.ler_config()
    log_filepath = get_log_filepath('aplicacao')

    sensor_config = config.get('nivel1', {}).get(str(sensor_id))
    if not sensor_config:
        return jsonify(error="Sensor ID não encontrado na configuração."), 404
    
    # PONTO 5: 'mapeamento_pacote' define os campos (sem 'tipo_dados' aqui)
    campos_dados = [m.get('campo') for m in sensor_config.get('mapeamento_pacote', []) if m.get('campo')]

    labels = [] 
    datasets_data = {campo: [] for campo in campos_dados}
    ultimo_valor_por_campo = {campo: "--" for campo in campos_dados}

    try:
        os.makedirs(os.path.dirname(log_filepath), exist_ok=True) # Garante que o dir exista
        with open(log_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if str(log_entry.get('id_sensor')) == str(sensor_id):
                        labels.append(log_entry.get('timestamp', ''))
                        dados = log_entry.get('dados', {})
                        for campo in campos_dados:
                            valor = dados.get(campo, None)
                            datasets_data[campo].append(valor)
                            if valor is not None:
                                ultimo_valor_por_campo[campo] = valor
                except json.JSONDecodeError:
                    continue 
    except FileNotFoundError:
        print(f"Arquivo de log não encontrado: {log_filepath}")
        return jsonify(labels=[], datasets=[], ultimos_valores={})

    # Formata a saída para o Chart.js
    chart_datasets = []
    colors = [('rgba(52, 152, 219, 1)', 'rgba(52, 152, 219, 0.2)'),
              ('rgba(231, 76, 60, 1)', 'rgba(231, 76, 60, 0.2)'),
              ('rgba(46, 204, 113, 1)', 'rgba(46, 204, 113, 0.2)')]
    
    for i, (campo, data) in enumerate(datasets_data.items()):
        color = colors[i % len(colors)]
        chart_datasets.append({
            'label': campo.replace('_', ' ').capitalize(),
            'data': data,
            'borderColor': color[0], 'backgroundColor': color[1],
            'borderWidth': 2, 'fill': True, 'tension': 0.4
        })

    return jsonify(
        labels=labels, 
        datasets=chart_datasets,
        ultimos_valores=ultimo_valor_por_campo
    )


# PONTO 2: Nova API para Dados de Rede
@app.route('/api/dados_rede/<sensor_id>')
def api_dados_rede(sensor_id):
    """API para ler o log de REDE e retornar dados de RSSI para o Chart.js."""
    log_filepath = get_log_filepath('rede')

    labels = []
    rssi_ul_data = []
    rssi_dl_data = []
    ultimos_valores = {"rssi_uplink_dbm": "--", "rssi_downlink_dbm": "--"}

    try:
        os.makedirs(os.path.dirname(log_filepath), exist_ok=True) # Garante que o dir exista
        with open(log_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if str(log_entry.get('id_sensor')) == str(sensor_id) and log_entry.get('status') == 'OK':
                        labels.append(log_entry.get('timestamp', ''))
                        
                        ul_val = log_entry.get('rssi_uplink_dbm', None)
                        dl_val = log_entry.get('rssi_downlink_dbm', None)
                        
                        rssi_ul_data.append(ul_val)
                        rssi_dl_data.append(dl_val)
                        
                        if ul_val is not None: ultimos_valores['rssi_uplink_dbm'] = ul_val
                        if dl_val is not None: ultimos_valores['rssi_downlink_dbm'] = dl_val
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Arquivo de log de rede não encontrado: {log_filepath}")
        return jsonify(labels=[], datasets=[], ultimos_valores={})

    chart_datasets = [
        {
            'label': 'RSSI Uplink (dBm)',
            'data': rssi_ul_data,
            'borderColor': 'rgba(52, 152, 219, 1)', 'backgroundColor': 'rgba(52, 152, 219, 0.2)',
            'borderWidth': 2, 'fill': True, 'tension': 0.4
        },
        {
            'label': 'RSSI Downlink (dBm)',
            'data': rssi_dl_data,
            'borderColor': 'rgba(231, 76, 60, 1)', 'backgroundColor': 'rgba(231, 76, 60, 0.2)',
            'borderWidth': 2, 'fill': True, 'tension': 0.4
        }
    ]

    return jsonify(
        labels=labels,
        datasets=chart_datasets,
        ultimos_valores=ultimos_valores
    )


if __name__ == '__main__':
    app.run(debug=True, port=5006)
