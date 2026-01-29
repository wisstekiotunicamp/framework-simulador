// Nivel6/static/js/dashboard_logic.js
// PONTO 2: Este script é GENÉRICO e funciona para ambos os dashboards

document.addEventListener('DOMContentLoaded', () => {
    // A variável API_ENDPOINT é definida no script inline do template HTML
    // (ex: '/api/dados_sensor/' ou '/api/dados_rede/')
    if (typeof API_ENDPOINT === 'undefined') {
        console.error("API_ENDPOINT não está definido no template HTML!");
        return;
    }

    const sensorSelector = document.getElementById('sensor-selector');
    const latestValuesEl = document.getElementById('latest-values-span');
    const ctx = document.getElementById('sensorDataChart').getContext('2d');

    // Configuração inicial do gráfico
    const sensorDataChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: false, title: { display: true, text: 'Valor' } },
                x: { title: { display: true, text: 'Horário da Coleta' } }
            },
            plugins: { legend: { display: true } }
        }
    });

    // Função principal que busca dados e atualiza o gráfico
    async function updateDashboard(sensorId) {
        if (!sensorId) {
            // Limpa o gráfico se "Selecione um sensor" for escolhido
            sensorDataChart.data.labels = [];
            sensorDataChart.data.datasets = [];
            sensorDataChart.update();
            latestValuesEl.textContent = "--";
            return;
        }

        try {
            // Chama a API definida no template (ex: /api/dados_rede/1)
            const response = await fetch(`${API_ENDPOINT}${sensorId}`);
            if (!response.ok) {
                throw new Error(`Erro na API: ${response.statusText}`);
            }
            const data = await response.json();

            // 1. Atualiza o Gráfico
            sensorDataChart.data.labels = data.labels;
            sensorDataChart.data.datasets = data.datasets;
            
            // Atualiza o título do eixo Y
            let yAxisTitle = "Valor";
            if (data.datasets.length > 0) {
                yAxisTitle = data.datasets.map(d => d.label).join(' / ');
            }
            sensorDataChart.options.scales.y.title.text = yAxisTitle;
            
            sensorDataChart.update();

            // 2. Atualiza o "Último Valor"
            let latestValuesHTML = "";
            if (data.ultimos_valores && Object.keys(data.ultimos_valores).length > 0) {
                for (const [campo, valor] of Object.entries(data.ultimos_valores)) {
                    // Formata o nome do campo (ex: 'rssi_uplink_dbm' -> 'Rssi Uplink (dBm)')
                    const nomeCampo = campo.replace(/_/g, ' ')
                                         .replace('dbm', ' (dBm)')
                                         .replace(/\b\w/g, l => l.toUpperCase());
                    latestValuesHTML += `<div style="margin-bottom: 10px;">${nomeCampo}: <strong>${valor}</strong></div>`;
                }
            } else {
                latestValuesHTML = "--";
            }
            latestValuesEl.innerHTML = latestValuesHTML;

        } catch (error) {
            console.error("Erro ao buscar dados do sensor:", error);
            latestValuesEl.textContent = "Erro ao carregar dados";
        }
    }

    // Adiciona o "listener" ao dropdown
    sensorSelector.addEventListener('change', () => {
        updateDashboard(sensorSelector.value);
    });

});
