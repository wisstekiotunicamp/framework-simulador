// Nivel6/static/js/config_logic.js
// Implementa a estrutura de config que você propôs (Pontos 3 e 5)

document.addEventListener('DOMContentLoaded', () => {
    // Referências do DOM (N3 e N4)
    const n3Ativo = document.getElementById('n3-ativo');
    const n3Intervalo = document.getElementById('n3-intervalo');
    const n3IdBase = document.getElementById('n3-id-base');
    const n3Timeout = document.getElementById('n3-timeout');
    const n4Diretorio = document.getElementById('n4-diretorio');
    const n4ArquivoRede = document.getElementById('n4-arquivo-rede');
    const n4ArquivoApp = document.getElementById('n4-arquivo-app');
    
    // Referências do DOM (N1 - Gerenciador)
    const sensorListContainer = document.getElementById('sensor-list-container');
    const addSensorBtn = document.getElementById('add-sensor-btn');
    const saveAllBtn = document.getElementById('save-all-config-btn');
    const saveStatusEl = document.getElementById('save-status');

    let configData = JSON.parse(document.getElementById('config-data').textContent);

    // =================================================================
    // FUNÇÃO 1: Carregar Dados (Model -> View)
    // =================================================================
    function loadDataIntoForms() {
        const n3 = configData.nivel3 || {};
        n3Ativo.checked = n3.ativo || false;
        n3Intervalo.value = n3.intervalo_leitura_s || '';
        n3IdBase.value = n3.id_base || '';
        n3Timeout.value = n3.tempo_limite_resposta_s || '';

        const n4 = configData.nivel4 || {};
        n4Diretorio.value = n4.diretorio_logs || '';
        n4ArquivoRede.value = n4.nome_arquivo_rede || '';
        n4ArquivoApp.value = n4.nome_arquivo_aplicacao || '';

        renderSensorList();
    }

    // =================================================================
    // FUNÇÃO 2: Renderizar a Lista de Sensores (ATUALIZADA)
    // =================================================================
    function renderSensorList() {
        sensorListContainer.innerHTML = ''; // Limpa a lista
        const n1 = configData.nivel1 || {};

        for (const sensorId in n1) {
            const sensor = n1[sensorId];
            const sensorCard = document.createElement('div');
            sensorCard.className = 'sensor-card';
            sensorCard.dataset.sensorId = sensorId;

            // PONTO 5: O header do mapeamento NÃO tem 'tipo_dados'
            let fieldsHTML = '<div class="sensor-field-list">';
            fieldsHTML += `
                <div class="sensor-field" style="font-weight: 700; grid-template-columns: 2fr 1fr 1fr 1fr 0.5fr;">
                    <label>Nome do Campo (no log)</label>
                    <label>Posição (Byte)</label>
                    <label>Tamanho (Bytes)</label>
                    <label>Escala (Divisor)</label>
                    <label>Ações</label>
                </div>
            `;
            
            (sensor.mapeamento_pacote || []).forEach((field, index) => {
                // PONTO 5: Removido input 'sensor-tipo-dados' daqui
                fieldsHTML += `
                    <div class="sensor-field" data-field-index="${index}" style="grid-template-columns: 2fr 1fr 1fr 1fr 0.5fr;">
                        <input type="text" class="sensor-campo" value="${field.campo || ''}" placeholder="nome_campo">
                        <input type="number" class="sensor-posicao" value="${field.posicao_byte || ''}" placeholder="byte">
                        <input type="number" class="sensor-tamanho" value="${field.tamanho_bytes || ''}" placeholder="bytes">
                        <input type="number" class="sensor-escala" value="${field.escala || ''}" placeholder="escala">
                        <button class="btn btn-danger btn-small remove-field-btn">X</button>
                    </div>
                `;
            });
            fieldsHTML += '</div>';

            // PONTO 3: Adicionado input 'sensor-descricao-input'
            // PONTO 5: Adicionado input 'sensor-tipo-dados-input' (nível superior)
            sensorCard.innerHTML = `
                <div class="sensor-card-header">
                    <h4>
                        ID: <input type="number" class="sensor-id-input" value="${sensorId}" style="width: 80px;">
                    </h4>
                    <button class="btn btn-danger remove-sensor-btn">Excluir Nó Sensor</button>
                </div>
                <div class="sensor-card-body">
                    <div class="form-group">
                        <label>Descrição (para o Dashboard)</label>
                        <input type="text" class="sensor-descricao-input" value="${sensor.descricao || ''}" placeholder="Ex: Sensor da Sala">
                    </div>
                    <div class="form-group">
                        <label>Tipo de Dados (para o Nível 3)</label>
                        <input type="text" class="sensor-tipo-dados-input" value="${sensor.tipo_dados || ''}" placeholder="Ex: Clima">
                    </div>

                    <h5>Mapeamento de Pacote (Sensores instalados):</h5>
                    ${fieldsHTML}
                    <button class="btn btn-primary btn-small add-field-btn">+ Adicionar Campo (Sensor)</button>
                </div>
            `;
            sensorListContainer.appendChild(sensorCard);
        }
    }

    // =================================================================
    // FUNÇÃO 3: Coletar Dados (View -> Model) (ATUALIZADA)
    // =================================================================
    function collectDataFromForms() {
        // Coleta Nível 3
        configData.nivel3 = {
            ativo: n3Ativo.checked,
            intervalo_leitura_s: parseInt(n3Intervalo.value) || 10,
            id_base: parseInt(n3IdBase.value) || 0,
            tempo_limite_resposta_s: parseInt(n3Timeout.value) || 20
        };

        // Coleta Nível 4
        configData.nivel4 = {
            diretorio_logs: n4Diretorio.value,
            nome_arquivo_rede: n4ArquivoRede.value,
            nome_arquivo_aplicacao: n4ArquivoApp.value
        };

        // Coleta Nível 1
        const novoNivel1 = {};
        document.querySelectorAll('.sensor-card').forEach(card => {
            const sensorId = card.querySelector('.sensor-id-input').value;
            if (!sensorId) return;

            // PONTO 3: Coleta a 'descricao'
            const descricao = card.querySelector('.sensor-descricao-input').value;
            // PONTO 5: Coleta o 'tipo_dados'
            const tipo_dados = card.querySelector('.sensor-tipo-dados-input').value;
            
            const mapeamento = [];

            card.querySelectorAll('.sensor-field').forEach(fieldRow => {
                if (fieldRow.style.fontWeight === '700') return; // Ignora o header
                
                const campo = fieldRow.querySelector('.sensor-campo').value;
                if (!campo) return; // Ignora campos sem nome

                // PONTO 5: 'tipo_dados' não é mais coletado aqui
                mapeamento.push({
                    campo: campo,
                    posicao_byte: parseInt(fieldRow.querySelector('.sensor-posicao').value) || 0,
                    tamanho_bytes: parseInt(fieldRow.querySelector('.sensor-tamanho').value) || 1,
                    escala: parseInt(fieldRow.querySelector('.sensor-escala').value) || 1
                });
            });

            novoNivel1[sensorId] = {
                descricao: descricao,   // PONTO 3
                tipo_dados: tipo_dados, // PONTO 5
                mapeamento_pacote: mapeamento
            };
            
            // Adiciona de volta 'log_headers' se ele existia (para não perdê-lo)
            if (configData.nivel1[sensorId] && configData.nivel1[sensorId].log_headers) {
                novoNivel1[sensorId].log_headers = configData.nivel1[sensorId].log_headers;
            }
        });
        configData.nivel1 = novoNivel1;
    }
    
    // =================================================================
    // FUNÇÃO 4: Salvar Configuração (API Call)
    // =================================================================
    async function saveConfiguration() {
        collectDataFromForms(); // Atualiza o objeto 'configData'
        
        saveStatusEl.textContent = 'Salvando...';
        saveStatusEl.style.color = 'var(--cor-texto-secundario)';
        
        try {
            const response = await fetch('/api/salvar_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            const result = await response.json();
            
            if (result.success) {
                saveStatusEl.textContent = 'Configuração salva com sucesso!';
                saveStatusEl.style.color = 'var(--cor-sucesso)';
                // Atualiza o configData local e re-renderiza
                configData = JSON.parse(JSON.stringify(configData));
                renderSensorList();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            saveStatusEl.textContent = `Erro ao salvar: ${error.message}`;
            saveStatusEl.style.color = 'var(--cor-perigo)';
        }
        
        setTimeout(() => { saveStatusEl.textContent = ''; }, 3000);
    }

    // =================================================================
    // Event Handlers
    // =================================================================

    saveAllBtn.addEventListener('click', saveConfiguration);

    addSensorBtn.addEventListener('click', () => {
        // Adiciona um novo sensor vazio ao objeto de dados
        const novoId = (Object.keys(configData.nivel1 || {}).length + 1).toString();
        configData.nivel1[novoId] = {
            descricao: "Novo Nó Sensor", // PONTO 3
            tipo_dados: "NovoTipo",      // PONTO 5
            mapeamento_pacote: [
                { campo: "novo_campo", posicao_byte: 16, tamanho_bytes: 2, escala: 1 }
            ]
        };
        renderSensorList();
    });

    sensorListContainer.addEventListener('click', (e) => {
        // Botão "Excluir Nó Sensor"
        if (e.target.classList.contains('remove-sensor-btn')) {
            const card = e.target.closest('.sensor-card');
            const sensorId = card.dataset.sensorId;
            // Coleta os dados do formulário ANTES de excluir, para não perder edições pendentes
            collectDataFromForms();
            delete configData.nivel1[sensorId];
            renderSensorList();
        }
        
        // Botão "+ Adicionar Campo (Sensor)"
        if (e.target.classList.contains('add-field-btn')) {
            const card = e.target.closest('.sensor-card');
            const sensorId = card.querySelector('.sensor-id-input').value || card.dataset.sensorId;
            // Coleta dados primeiro para garantir que o sensorId esteja atualizado
            collectDataFromForms();
            if(configData.nivel1[sensorId]){
                configData.nivel1[sensorId].mapeamento_pacote.push({
                    campo: "", posicao_byte: 0, tamanho_bytes: 1, escala: 1
                });
            }
            renderSensorList();
        }
        
        // Botão "X" (Remover Campo)
        if (e.target.classList.contains('remove-field-btn')) {
            const card = e.target.closest('.sensor-card');
            const sensorId = card.querySelector('.sensor-id-input').value || card.dataset.sensorId;
            const fieldRow = e.target.closest('.sensor-field');
            const fieldIndex = parseInt(fieldRow.dataset.fieldIndex);
            // Coleta dados primeiro
            collectDataFromForms();
            if(configData.nivel1[sensorId]){
                configData.nivel1[sensorId].mapeamento_pacote.splice(fieldIndex, 1);
            }
            renderSensorList();
        }
    });

    // =================================================================
    // INICIALIZAÇÃO
    // =================================================================
    loadDataIntoForms();
});
