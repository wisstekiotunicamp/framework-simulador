# explanation_windows.py
import customtkinter as ctk
import math

class FSLExplanationWindow(ctk.CTkToplevel):
    """ Janela de explicação para o modelo Free-Space Path Loss (Espaço Livre). """
    def __init__(self, parent, example_data=None):
        super().__init__(parent)
        self.transient(parent)
        self.title("Explicação: Espaço Livre (FSPL)")
        self.geometry("700x650")

        scroll_frame = ctk.CTkScrollableFrame(self, label_text="Modelo: Propagação em Espaço Livre (Free-Space Path Loss)")
        scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)

        body_font = ctk.CTkFont(family="Segoe UI", size=13)
        subtitle_font = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        formula_font = ctk.CTkFont(family="Courier New", size=14, weight="bold")
        
        def add_text_label(parent, text, font, justify="left", padx=10):
            label = ctk.CTkLabel(parent, text=text, font=font, justify=justify, wraplength=620)
            label.pack(anchor="w", pady=(0, 10), padx=padx)
        
        add_text_label(scroll_frame, 
            "O modelo de propagação em espaço livre (FSPL) é usado para prever a perda de sinal de uma onda eletromagnética "
            "em um ambiente ideal, sem obstáculos, barreiras ou reflexões. A perda de sinal depende fundamentalmente de dois fatores: "
            "a distância entre o transmissor e o receptor, e a frequência do sinal.", 
            font=body_font
        )
        
        add_text_label(scroll_frame, "Fórmulas Utilizadas", font=subtitle_font)
        
        add_text_label(scroll_frame, "1. Perda de Percurso (Atenuação) [Simplificada]:", font=body_font)
        add_text_label(scroll_frame, "L_PL [dB] = 20*log10(d) + 20*log10(f_MHz) - 27.55", font=formula_font, padx=20)
        
        add_text_label(scroll_frame, "2. Cálculo do RSSI (Received Signal Strength Indicator):", font=body_font)
        add_text_label(scroll_frame, "RSSI [dBm] = P_TX [dBm] + G_TX [dBi] + G_RX [dBi] - L_PL [dB]", font=formula_font, padx=20)

        add_text_label(scroll_frame, "Exemplo Prático com Dados da Simulação", font=subtitle_font)

        if example_data:
            d, freq_mhz, p_tx, g_tx, g_rx = (example_data['distance_m'], example_data['freq_mhz'], 
                                             example_data['p_tx'], example_data['g_tx'], example_data['g_rx'])
            
            path_loss_val = 20 * math.log10(d) + 20 * math.log10(freq_mhz) - 27.55 if d > 0 else float('inf')
            rssi_val = p_tx + g_tx + g_rx - path_loss_val

            example_text = (
                f"Dados utilizados (baseado no link {example_data['tx_id']} -> {example_data['rx_id']}):\n"
                f"   - Distância (d): {d:.2f} metros\n   - Frequência (f): {freq_mhz} MHz\n"
                f"   - Potência de Transmissão (P_TX): {p_tx} dBm\n   - Ganho da Antena TX (G_TX): {g_tx} dBi\n"
                f"   - Ganho da Antena RX (G_RX): {g_rx} dBi\n\n"
                f"Passo 1: Perda de Percurso (Atenuação) (L_PL) = 20*log10({d:.2f}) + 20*log10({freq_mhz}) - 27.55 = {path_loss_val:.2f} dB\n\n"
                f"Passo 2: RSSI = {p_tx} + {g_tx} + {g_rx} - {path_loss_val:.2f} = {rssi_val:.2f} dBm"
            )
            add_text_label(scroll_frame, example_text, font=body_font)
        else:
            add_text_label(scroll_frame, "Adicione nós ao simulador para gerar um exemplo prático.", font=body_font)
        
        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10, padx=10)

        self.grab_set()

class LogDistanceExplanationWindow(ctk.CTkToplevel):
    """ Janela de explicação para o modelo Log-Distância. """
    def __init__(self, parent, example_data=None):
        super().__init__(parent)
        self.transient(parent)
        self.title("Explicação: Log-Distância")
        self.geometry("700x750")

        scroll_frame = ctk.CTkScrollableFrame(self, label_text="Modelo: Perda de Percurso Log-Distância")
        scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # --- Fontes ---
        body_font = ctk.CTkFont(family="Segoe UI", size=13)
        subtitle_font = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        formula_font = ctk.CTkFont(family="Courier New", size=14, weight="bold")
        
        def add_text_label(parent, text, font, justify="left", padx=10):
            label = ctk.CTkLabel(parent, text=text, font=font, justify=justify, wraplength=620)
            label.pack(anchor="w", pady=(0, 10), padx=padx)
        
        # --- Explicação do Modelo ---
        add_text_label(scroll_frame, 
            "O modelo Log-Distância é uma evolução do modelo de Espaço Livre. Ele generaliza a perda de sinal "
            "usando um 'Coeficiente Beta' (também chamado de Expoente de Perda de Percurso, 'n' ou 'β') para "
            "modelar diferentes ambientes (ex: cidade, dentro de prédios, etc.).",
            font=body_font
        )
        add_text_label(scroll_frame, 
            "Ele se baseia em uma perda de sinal conhecida (PL₀) medida a uma 'Distância de Referência' (d₀), "
            "e então extrapola a perda para distâncias maiores usando o Coeficiente Beta.",
            font=body_font
        )

        add_text_label(scroll_frame, "Novos Parâmetros (Intrínsecos do Modelo)", font=subtitle_font)
        add_text_label(scroll_frame, 
            "1. Distância de Referência (d₀):\n"
            "   A distância (em metros) onde a perda de referência (PL₀) é calculada. "
            "Geralmente definida como 1 metro.",
            font=body_font, padx=20
        )
        add_text_label(scroll_frame, 
            "2. Coeficiente Beta (β):\n"
            "   O Expoente de Perda de Percurso. Define quão rapidamente o sinal se atenua com a distância. "
            "Exemplos:\n"
            "   - β = 2.0 (Espaço Livre)\n"
            "   - β = 2.7 a 3.5 (Área Urbana)\n"
            "   - β = 3.0 a 5.0 (Dentro de Prédios com obstruções)",
            font=body_font, padx=20
        )

        add_text_label(scroll_frame, "Fórmulas Utilizadas", font=subtitle_font)
        
        add_text_label(scroll_frame, "1. Perda na Referência (PL₀) [dB]:", font=body_font)
        add_text_label(scroll_frame, "PL₀ = 20*log10(d₀) + 20*log10(f_MHz) - 27.55", font=formula_font, padx=20)
        
        add_text_label(scroll_frame, "2. Perda de Percurso Total (L_PL) [dB]:", font=body_font)
        add_text_label(scroll_frame, "L_PL = PL₀ + 10 * β * log10( d / d₀ )   (para d > d₀)", font=formula_font, padx=20)

        add_text_label(scroll_frame, "3. Cálculo do RSSI (Received Signal Strength Indicator):", font=body_font)
        add_text_label(scroll_frame, "RSSI [dBm] = P_TX [dBm] + G_TX [dBi] + G_RX [dBi] - L_PL [dB]", font=formula_font, padx=20)

        add_text_label(scroll_frame, "Exemplo Prático com Dados da Simulação", font=subtitle_font)

        if example_data:
            d, freq_mhz, p_tx, g_tx, g_rx = (example_data['distance_m'], example_data['freq_mhz'], 
                                             example_data['p_tx'], example_data['g_tx'], example_data['g_rx'])
            d0, beta = (example_data['d0'], example_data['beta'])

            # Cálculos
            pl_0_val = 20 * math.log10(d0) + 20 * math.log10(freq_mhz) - 27.55
            
            if d <= d0:
                path_loss_val = pl_0_val
                calc_step2 = f"Passo 2: L_PL = PL₀ (pois d ≤ d₀) = {path_loss_val:.2f} dB\n\n"
            else:
                path_loss_val = pl_0_val + 10 * beta * math.log10(d / d0)
                calc_step2 = f"Passo 2: L_PL = {pl_0_val:.2f} + 10 * {beta} * log10({d:.2f} / {d0}) = {path_loss_val:.2f} dB\n\n"

            rssi_val = p_tx + g_tx + g_rx - path_loss_val

            example_text = (
                f"Dados utilizados (baseado no link {example_data['tx_id']} -> {example_data['rx_id']}):\n"
                f"   - Distância (d): {d:.2f} metros\n   - Frequência (f): {freq_mhz} MHz\n"
                f"   - Potência TX (P_TX): {p_tx} dBm\n   - Ganhos (G_TX/G_RX): {g_tx} dBi / {g_rx} dBi\n\n"
                f"Parâmetros do Modelo:\n"
                f"   - Distância de Referência (d₀): {d0} m\n"
                f"   - Coeficiente Beta (β): {beta}\n\n"
                f"Passo 1: PL₀ = 20*log10({d0}) + 20*log10({freq_mhz}) - 27.55 = {pl_0_val:.2f} dB\n\n"
                f"{calc_step2}"
                f"Passo 3: RSSI = {p_tx} + {g_tx} + {g_rx} - {path_loss_val:.2f} = {rssi_val:.2f} dBm"
            )
            add_text_label(scroll_frame, example_text, font=body_font)
        else:
            add_text_label(scroll_frame, "Adicione nós ao simulador para gerar um exemplo prático.", font=body_font)
        
        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10, padx=10)

        self.grab_set()

