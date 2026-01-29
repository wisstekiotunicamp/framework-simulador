# app.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import math
import time 
import yaml
import os
import re
from collections import Counter

from components import NodePropertiesWindow
from simulation_models import MODELS
from sensor_manager import SensorTypeManagerWindow

class App(ctk.CTk):
    DRAG_THRESHOLD = 4

    def __init__(self):
        super().__init__()
        self.title("Simulador de RF")
        self.geometry("1000x800")
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        
        self.pixels_per_metro = tk.DoubleVar(value=20.0)
        self.frequency_mhz = tk.DoubleVar(value=915.0)
        self.distance_unit = tk.StringVar(value="Metros")
        
        self.propagation_models_registry = MODELS
        self.propagation_model = tk.StringVar(value=list(self.propagation_models_registry.keys())[0])
        
        self.model_d0 = tk.DoubleVar(value=1.0)
        self.model_beta = tk.DoubleVar(value=2.0)

        self.sensor_types_config = {}
        self.available_sensor_types = []
        self._load_dados_sensores()

        self.nodes, self.obstacles, self.action_history = [], [], []
        self.node_id_counter = 0
        
        self.background_photo, self.background_image_id = None, None
        self.background_image_path = None
        self.current_file_path = None
        self.obstacle_styles = {"Parede de Concreto": {"color": "#8B8B83", "width": 7, "dash": ()},"Parede de Tijolos":  {"color": "#B22222", "width": 5, "dash": ()},"Parede Drywall":     {"color": "#C0C0C0", "width": 3, "dash": (10, 5)}}
        self.active_tool, self.current_obstacle_id = None, None
        self._drag_data = {"x": 0, "y": 0, "item": None, "is_dragging": False}
        self._last_click_time = 0
        self.last_clicked_item = None

        self._create_widgets()
        self._create_menu()

        self._update_model_param_ui()
        self.update_distances()

    def _create_widgets(self):
        self.control_frame = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.control_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nswe")
        self.control_frame.grid_propagate(False)
        ctk.CTkLabel(self.control_frame, text="Ferramentas", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10, padx=10)
        tools_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent"); tools_frame.pack(padx=10, pady=5, fill="x")
        self.tool_buttons = {}
        for tool in ["Nó Base","Nó Sensor","Obstáculo", "Excluir"]: button = ctk.CTkButton(tools_frame, text=tool, command=lambda t=tool: self._select_tool(t)); button.pack(pady=4, fill="x"); self.tool_buttons[tool] = button
        self.obstacle_type_var = tk.StringVar(value="Parede de Concreto"); self.obstacle_dropdown = ctk.CTkOptionMenu(self.control_frame, variable=self.obstacle_type_var, values=list(self.obstacle_styles.keys()))
        
        sim_frame = ctk.CTkFrame(self.control_frame); sim_frame.pack(padx=10, pady=15, fill="x")
        ctk.CTkLabel(sim_frame, text="Parâmetros de Simulação", font=ctk.CTkFont(weight="bold")).pack(pady=(5,10))
        
        # --- MUDANÇA DE LAYOUT (PONTO 1) ---
        # 1. Container para a seção de modelo de propagação.
        propagation_section_frame = ctk.CTkFrame(sim_frame, fg_color="transparent")
        propagation_section_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 2. Frame para o menu dropdown (AGORA NO TOPO DA SEÇÃO)
        model_frame = ctk.CTkFrame(propagation_section_frame, fg_color="transparent")
        model_frame.pack(fill="x")
        model_frame.grid_columnconfigure(0, weight=1)
        
        label_modelo = ctk.CTkLabel(model_frame, text="Modelo de Propagação:")
        label_modelo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        
        model_menu = ctk.CTkOptionMenu(model_frame, variable=self.propagation_model, values=list(self.propagation_models_registry.keys()), command=self._on_model_change)
        model_menu.grid(row=1, column=0, sticky="ew")
        
        self.explanation_button = ctk.CTkButton(model_frame, text="?", width=28, command=self._show_explanation_window)
        self.explanation_button.grid(row=1, column=1, padx=(5,0))

        # 3. Frame para os parâmetros extras (d0, beta)
        self.model_params_frame = ctk.CTkFrame(propagation_section_frame, fg_color="transparent")
        self.model_params_frame.pack(fill="x", pady=(5, 0))

        self.label_d0 = ctk.CTkLabel(self.model_params_frame, text="Distância de Referência - d₀ (m):")
        self.label_d0.pack(anchor="w")
        self.entry_d0 = ctk.CTkEntry(self.model_params_frame, textvariable=self.model_d0)
        self.entry_d0.pack(pady=(0,5), fill="x")
        self.entry_d0.bind("<Return>", lambda e: self.update_distances())

        self.label_beta = ctk.CTkLabel(self.model_params_frame, text="Coeficiente Beta (β ou n):")
        self.label_beta.pack(anchor="w")
        self.entry_beta = ctk.CTkEntry(self.model_params_frame, textvariable=self.model_beta)
        self.entry_beta.pack(pady=(0,5), fill="x")
        self.entry_beta.bind("<Return>", lambda e: self.update_distances())
        
        # 4. Frequência (AGORA ABAIXO da seção de modelo)
        ctk.CTkLabel(sim_frame, text="Frequência (MHz):").pack(padx=10, anchor="w")
        freq_entry = ctk.CTkEntry(sim_frame, textvariable=self.frequency_mhz); freq_entry.pack(padx=10, pady=(0,10), fill="x"); freq_entry.bind("<Return>", lambda e: self.update_distances())
        # --- FIM DA MUDANÇA DE LAYOUT ---
        
        unit_frame = ctk.CTkFrame(self.control_frame); unit_frame.pack(padx=10, pady=(5,0), fill="x")
        ctk.CTkLabel(unit_frame, text="Unidade de Medida:").pack(padx=10, anchor="w", pady=(5,0))
        self.unit_menu = ctk.CTkOptionMenu(unit_frame, variable=self.distance_unit, values=["Metros", "Quilômetros"], command=self._on_unit_change); self.unit_menu.pack(padx=10, pady=(0,10), fill="x")
        scale_frame = ctk.CTkFrame(self.control_frame); scale_frame.pack(padx=10, pady=0, fill="x")
        ctk.CTkLabel(scale_frame, text="Ajuste de Escala").pack()
        self.scale_unit_label = ctk.CTkLabel(scale_frame, text="(pixels / metro)"); self.scale_unit_label.pack()
        scale_entry_frame = ctk.CTkFrame(scale_frame, fg_color="transparent"); scale_entry_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.scale_slider = ctk.CTkSlider(scale_entry_frame, from_=5, to=150, variable=self.pixels_per_metro, command=self._update_scale_from_slider); self.scale_slider.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.scale_entry = ctk.CTkEntry(scale_entry_frame, width=50, textvariable=self.pixels_per_metro); self.scale_entry.pack(side="left"); self.scale_entry.bind("<Return>", self._update_scale_from_entry)
        ctk.CTkButton(self.control_frame, text="Carregar Imagem de Fundo", command=self._load_background_image).pack(padx=10, pady=(15,5), fill="x")
        ctk.CTkButton(self.control_frame, text="Gerar Relatório", command=self.generate_report).pack(padx=10, pady=10, fill="x")
        ctk.CTkButton(self.control_frame, text="Desfazer", command=self.undo_last_action).pack(padx=10, pady=10, fill="x")
        ctk.CTkButton(self.control_frame, text="Limpar Tela", command=self.clear_all, fg_color="#D35B58", hover_color="#C77C78").pack(padx=10, pady=10, fill="x")
        self.canvas = tk.Canvas(self, bg="#2B2B2B", bd=0, highlightthickness=0); self.canvas.grid(row=0, column=1, padx=(0, 10), pady=(10, 0), sticky="nswe")
        self.canvas.bind("<ButtonPress-1>", self.on_press); self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<ButtonRelease-1>", self.on_release)
        ctk.CTkLabel(self, text="Conexões (Sensor -> Base):", anchor="w").grid(row=1, column=1, padx=(0, 10), pady=(5, 0), sticky="we")
        self.results_textbox = ctk.CTkTextbox(self, height=120, state="disabled"); self.results_textbox.grid(row=2, column=1, padx=(0, 10), pady=(0, 10), sticky="we")
        self._update_ui_for_tool_selection()

    def _update_model_param_ui(self):
        model_name = self.propagation_model.get()
        model_info = self.propagation_models_registry.get(model_name)
        
        if model_info and "beta" in model_info.get("params", []):
            self.model_params_frame.pack(fill="x", pady=(5, 0))
        else:
            self.model_params_frame.pack_forget()

    def _on_model_change(self, choice):
        self._update_model_param_ui()
        self.update_distances()
    
    def _create_menu(self):
        self.menubar = tk.Menu(self)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Abrir Simulação...", command=self._load_simulation)
        file_menu.add_separator()
        file_menu.add_command(label="Salvar", command=self._save_simulation)
        file_menu.add_command(label="Salvar Como...", command=self._save_simulation_as)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.destroy)
        self.menubar.add_cascade(label="Arquivo", menu=file_menu)
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Gerenciar Tipos de Sensores...", command=self._open_sensor_type_manager)
        self.menubar.add_cascade(label="Editar", menu=edit_menu)
        self.config(menu=self.menubar)

    def _load_dados_sensores(self):
        config_path = os.path.join(os.path.dirname(__file__), 'dados_sensores.yml')
        default_config = {
            'Clima': {'source_file': 'clima.py', 'mapeamento_pacote': {'temperatura': {'posicao_byte': 16, 'tamanho_bytes': 2, 'escala': 10},'umidade': {'posicao_byte': 18, 'tamanho_bytes': 2, 'escala': 10}}},
            'Luminosidade': {'source_file': 'luminosidade.py', 'mapeamento_pacote': {'luminosidade_lux': {'posicao_byte': 16, 'tamanho_bytes': 2, 'escala': 1}}}
        }
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.sensor_types_config = config.get('sensor_types', default_config)
        except FileNotFoundError:
            self.sensor_types_config = default_config
            self._save_dados_sensores()
        self.available_sensor_types = list(self.sensor_types_config.keys()) if self.sensor_types_config else []

    def _save_dados_sensores(self):
        config_path = os.path.join(os.path.dirname(__file__), 'dados_sensores.yml')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump({'sensor_types': self.sensor_types_config}, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar a configuração de sensores:\n{e}", parent=self)

    def _open_sensor_type_manager(self):
        manager_window = SensorTypeManagerWindow(self, self.sensor_types_config)
        self.wait_window(manager_window)
        if manager_window.result is not None:
            self.sensor_types_config = manager_window.result
            self.available_sensor_types = list(self.sensor_types_config.keys()) if self.sensor_types_config else []
            self._save_dados_sensores()
            self.update_distances()
    
    def _save_simulation(self):
        if self.current_file_path:
            self._write_to_file(self.current_file_path)
        else:
            self._save_simulation_as()

    def _save_simulation_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".yml",
            filetypes=[("Arquivos de Simulação YAML", "*.yml *.yaml"), ("Todos os arquivos", "*.*")],
            title="Salvar Simulação Como..."
        )
        if not file_path: return
        self._write_to_file(file_path)

    def _write_to_file(self, file_path):
        nodes_to_save = []
        for node in self.nodes:
            node_info = {"id": node['id'], "descricao": node['descricao'], "type": node['type'], "coords": list(node['coords']), "power_dbm": node['power_dbm'], "gain_dbi": node['gain_dbi']}
            if node['type'] == 'Nó Sensor':
                node_info['sensor_type'] = node['sensor_type']
            nodes_to_save.append(node_info)
        obstacles_to_save = [{"type": o["type"], "coords": [list(o["coords"][0]), list(o["coords"][1])]} for o in self.obstacles]
        
        simulation_data = {
            "parameters": {
                "pixels_per_metro": self.pixels_per_metro.get(), 
                "frequency_mhz": self.frequency_mhz.get(), 
                "distance_unit": self.distance_unit.get(), 
                "propagation_model": self.propagation_model.get(),
                "model_d0": self.model_d0.get(),
                "model_beta": self.model_beta.get()
            }, 
            "background_image_path": self.background_image_path, 
            "nodes": nodes_to_save, 
            "obstacles": obstacles_to_save
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(simulation_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            self.current_file_path = file_path
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo do projeto:\n{e}", parent=self)

    def _load_simulation(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Arquivos de Simulação YAML", "*.yml *.yaml"), ("Todos os arquivos", "*.*")],
            title="Carregar Simulação"
        )
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self.clear_all()
            
            params = data.get("parameters", {})
            self.pixels_per_metro.set(params.get("pixels_per_metro", 20.0))
            self.frequency_mhz.set(params.get("frequency_mhz", 915.0))
            self.distance_unit.set(params.get("distance_unit", "Metros"))
            self.propagation_model.set(params.get("propagation_model", "Espaço Livre"))
            
            self.model_d0.set(params.get("model_d0", 1.0))
            self.model_beta.set(params.get("model_beta", 2.0))

            self._on_unit_change(None)

            bg_path = data.get("background_image_path")
            if bg_path:
                try:
                    self.background_image_path = bg_path; image = Image.open(bg_path); self.background_photo = ImageTk.PhotoImage(image); self.background_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.background_photo); self.canvas.tag_lower(self.background_image_id)
                except FileNotFoundError:
                    self.background_image_path = None
            
            max_id = -1
            nodes_in_file = data.get("nodes", [])
            for node_data in nodes_in_file:
                x, y = node_data["coords"]; size, color = (30, "dodgerblue" if node_data["type"] == "Nó Sensor" else "#2CC985")
                shape_id = self.canvas.create_oval(x - size/2, y - size/2, x + size/2, y + size/2, fill=color, outline="", tags=("shape", node_data["type"]))
                text_id = self.canvas.create_text(x, y, text=node_data["descricao"], fill="white", font=("Segoe UI", 9, "bold"), tags=("text",))
                if node_data['type'] == 'Nó Sensor':
                    if 'sensor_type' not in node_data or node_data['sensor_type'] not in self.available_sensor_types:
                        node_data['sensor_type'] = self.available_sensor_types[0] if self.available_sensor_types else ""
                max_id = max(max_id, node_data['id'])
                self.nodes.append({"shape_id": shape_id, "text_id": text_id, **node_data})
            
            self.node_id_counter = max_id + 1
            
            for obs_data in data.get("obstacles", []):
                start_coords, end_coords = obs_data["coords"]; style = self.obstacle_styles[obs_data["type"]]
                line_id = self.canvas.create_line(start_coords, end_coords, fill=style["color"], width=style["width"], dash=style["dash"], capstyle=tk.ROUND, tags="obstacle")
                self.obstacles.append({"id": line_id, **obs_data})
            
            self.current_file_path = file_path
            self._update_model_param_ui() 
            self.update_distances()
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Não foi possível carregar o arquivo do projeto:\n{e}", parent=self); self.current_file_path = None

    def clear_all(self): 
        self.canvas.delete("all"); self.nodes.clear(); self.obstacles.clear(); self.action_history.clear(); self.node_id_counter = 0; self.background_photo, self.background_image_id, self.background_image_path = None, None, None; self.current_file_path = None; self.update_distances()

    def add_node(self, event):
        node_type = self.active_tool; x, y = event.x, event.y; size = 30; color = "dodgerblue" if node_type == "Nó Sensor" else "#2CC985"
        shape_id = self.canvas.create_oval(x - size/2, y - size/2, x + size/2, y + size/2, fill=color, outline="", tags=("shape", node_type))
        node_data = {"shape_id": shape_id, "text_id": None, "type": node_type, "coords": (x, y), "power_dbm": 14.0, "gain_dbi": 2.2, "id": self.node_id_counter}
        if node_type == "Nó Sensor":
            node_data["descricao"] = f"Sensor {self.node_id_counter}"
            node_data["sensor_type"] = self.available_sensor_types[0] if self.available_sensor_types else ""
        else:
            node_data["descricao"] = f"Base {self.node_id_counter}"
        self.node_id_counter += 1
        node_data["text_id"] = self.canvas.create_text(x, y, text=node_data["descricao"], fill="white", font=("Segoe UI", 9, "bold"), tags=("text",))
        self.nodes.append(node_data); self.action_history.append({"verb": "add", "type": "node", "data": node_data}); self.update_distances()
    
    def _handle_double_click(self, clicked_item_id):
        if not clicked_item_id or clicked_item_id == self.background_image_id: return
        node_to_edit = self._get_node_by_canvas_id(clicked_item_id)
        if not node_to_edit: return
        sources = self.available_sensor_types if node_to_edit['type'] == 'Nó Sensor' else []
        prop_window = NodePropertiesWindow(self, node_to_edit, available_types=sources)
        self.wait_window(prop_window)
        if prop_window.result:
            new_id = prop_window.result.get('id'); current_id = node_to_edit.get('id')
            if new_id != current_id:
                is_id_in_use = any(node.get('id') == new_id for node in self.nodes if node is not node_to_edit)
                if is_id_in_use: messagebox.showerror("Erro de ID", f"O ID '{new_id}' já está em uso.", parent=self); return
            node_to_edit.update(prop_window.result); self.canvas.itemconfig(node_to_edit['text_id'], text=node_to_edit['descricao']); self.update_distances()
            
    def update_distances(self):
        self._clear_distance_visuals(); self.results_textbox.configure(state="normal"); self.results_textbox.delete("1.0", "end")
        sensores = [n for n in self.nodes if n["type"] == "Nó Sensor"]; bases = [n for n in self.nodes if n["type"] == "Nó Base"]
        if not sensores or not bases:
            self.results_textbox.insert("1.0", "Adicione pelo menos um Nó Sensor e um Nó Base.")
        else:
            scale_factor_to_meters, unit_label = self._get_scale_factor_and_label(); model_name = self.propagation_model.get()
            calculator_func = self.propagation_models_registry[model_name]["calculator"]
            
            params = {
                'freq_mhz': self.frequency_mhz.get(),
                'd0': self.model_d0.get(),
                'beta': self.model_beta.get()
            }

            for sensor in sensores:
                closest_base, min_dist_px = self._find_closest_node(sensor, bases)
                if closest_base:
                    distance_in_selected_unit = min_dist_px / self.pixels_per_metro.get()
                    distance_for_rssi_m = distance_in_selected_unit * scale_factor_to_meters
                    
                    params['d_m'] = distance_for_rssi_m
                    
                    rssi, path_loss = calculator_func(sensor, closest_base, params)
                    
                    line_id = self.canvas.create_line(sensor["coords"], closest_base["coords"], fill="#E0E0E0", width=1.5, dash=(5, 5), tags="distance_viz"); self.canvas.tag_lower(line_id, "shape")
                    mid_x = (sensor["coords"][0] + closest_base["coords"][0]) / 2; mid_y = (sensor["coords"][1] + closest_base["coords"][1]) / 2
                    text_content = f"{distance_in_selected_unit:.2f}{unit_label}"; text_font = ("Segoe UI", 8, "bold")
                    for dx, dy in [(-1, -1), (1, 1), (-1, 1), (1, -1), (0, 1), (1, 0), (0, -1), (-1, 0)]: self.canvas.create_text(mid_x + dx, mid_y - 8 + dy, text=text_content, fill="black", font=text_font, tags="distance_viz")
                    self.canvas.create_text(mid_x, mid_y - 8, text=text_content, fill="#FFFF70", font=text_font, tags="distance_viz")
                    result_text = f"{sensor['descricao']} (ID:{sensor['id']}) -> {closest_base['descricao']} (ID:{closest_base['id']}): {text_content} | RSSI: {rssi:.2f} dBm | Atenuação: {path_loss:.2f} dB\n"
                    self.results_textbox.insert("end", result_text)
        self.results_textbox.configure(state="disabled"); self._write_channel_config(); self._write_sensores_config()

    def _write_channel_config(self):
        config_data = {'modelo_atual': self.propagation_model.get(), 'links': {}}
        sensores = [n for n in self.nodes if n["type"] == "Nó Sensor"]; bases = [n for n in self.nodes if n["type"] == "Nó Base"]
        if sensores and bases:
            calculator_func = self.propagation_models_registry[self.propagation_model.get()]["calculator"]
            
            params = {
                'freq_mhz': self.frequency_mhz.get(),
                'd0': self.model_d0.get(),
                'beta': self.model_beta.get()
            }
            scale_factor, _ = self._get_scale_factor_and_label()

            for sensor in sensores:
                base, dist_px = self._find_closest_node(sensor, bases)
                if base:
                    dist_m = (dist_px / self.pixels_per_metro.get()) * scale_factor
                    
                    params['d_m'] = dist_m
                    
                    rssi_ul, path_loss_ul = calculator_func(sensor, base, params)
                    rssi_dl, path_loss_dl = calculator_func(base, sensor, params)
                    
                    config_data['links'][str(sensor['id'])] = {'rssi_uplink_dbm': rssi_ul, 'atenuacao_uplink_db': path_loss_ul, 'rssi_downlink_dbm': rssi_dl, 'atenuacao_downlink_db': path_loss_dl}
        try:
            path = os.path.join(os.path.dirname(__file__), '..', 'Nivel2', 'canal_config.yml')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e: print(f"ERRO ao escrever arquivo do canal: {e}")

    def _write_sensores_config(self):
        config_data = {'config_sensores': {}}
        for node in self.nodes:
            if node['type'] == 'Nó Sensor':
                sensor_id = node.get('id'); sensor_type = node.get('sensor_type', self.available_sensor_types[0] if self.available_sensor_types else "")
                type_config = self.sensor_types_config.get(sensor_type)
                if sensor_id is not None and type_config:
                    config_data['config_sensores'][str(sensor_id)] = {'id_sensor': sensor_id, 'source_file': type_config['source_file'], 'mapeamento_pacote': type_config['mapeamento_pacote']}
        try:
            path = os.path.join(os.path.dirname(__file__), '..', 'Nivel1', 'sensores_config.yml')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e: print(f"ERRO ao escrever arquivo dos sensores: {e}")
        
    def _load_background_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos os arquivos", "*.*")])
        if not file_path: return
        self.background_image_path = file_path; image = Image.open(file_path); self.background_photo = ImageTk.PhotoImage(image)
        if self.background_image_id: self.canvas.delete(self.background_image_id)
        self.background_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.background_photo); self.canvas.tag_lower(self.background_image_id)

    def _on_unit_change(self, choice):
        self.update_distances()

    def _get_scale_factor_and_label(self):
        unit = self.distance_unit.get()
        if unit == "Quilômetros": self.scale_unit_label.configure(text="(pixels / quilômetro)"); return 1000, "km"
        self.scale_unit_label.configure(text="(pixels / metro)"); return 1, "m"

    def _show_explanation_window(self):
        model_name = self.propagation_model.get(); model_info = self.propagation_models_registry.get(model_name)
        
        if not model_info or "explanation_class" not in model_info: 
            messagebox.showinfo("Informação", "Nenhuma janela de explicação foi definida para este modelo.", parent=self)
            return

        ExplanationWindowClass = model_info["explanation_class"]; example_data = None
        sensores = [n for n in self.nodes if n["type"] == "Nó Sensor"]; bases = [n for n in self.nodes if n["type"] == "Nó Base"]
        
        if sensores and bases:
            first_sensor = sorted(sensores, key=self._sort_key_for_nodes)[0]
            closest_base, dist_px = self._find_closest_node(first_sensor, bases)
            if closest_base:
                scale_factor, _ = self._get_scale_factor_and_label(); distance_m = (dist_px / self.pixels_per_metro.get()) * scale_factor
                
                example_data = {
                    "tx_id": first_sensor['descricao'], "rx_id": closest_base['descricao'], 
                    "distance_m": distance_m, "freq_mhz": self.frequency_mhz.get(), 
                    "p_tx": first_sensor['power_dbm'], "g_tx": first_sensor['gain_dbi'], "g_rx": closest_base['gain_dbi'],
                    "d0": self.model_d0.get(),
                    "beta": self.model_beta.get()
                }
        ExplanationWindowClass(self, example_data=example_data)

    def generate_report(self):
        report_window = ctk.CTkToplevel(self); report_window.title("Relatório de Conectividade"); report_window.geometry("650x500"); report_window.transient(self)
        textbox = ctk.CTkTextbox(report_window, wrap="word", font=("Segoe UI", 13)); textbox.pack(expand=True, fill="both", padx=10, pady=10)
        sensores = sorted([n for n in self.nodes if n["type"] == "Nó Sensor"], key=self._sort_key_for_nodes); bases = sorted([n for n in self.nodes if n["type"] == "Nó Base"], key=self._sort_key_for_nodes)
        if not sensores or not bases: textbox.insert("1.0", "Dados insuficientes."); textbox.configure(state="disabled"); return
        
        scale_factor_to_meters, unit_label = self._get_scale_factor_and_label(); model_name = self.propagation_model.get()
        calculator_func = self.propagation_models_registry[model_name]["calculator"]
        
        params = {
            'freq_mhz': self.frequency_mhz.get(),
            'd0': self.model_d0.get(),
            'beta': self.model_beta.get()
        }
        
        report_lines = [f"RELATÓRIO DE SIMULAÇÃO (Freq: {self.frequency_mhz.get()} MHz, Modelo: {model_name})\n", "="*70 + "\n"]
        for sensor in sensores:
            closest_base, distance_px = self._find_closest_node(sensor, bases)
            if not closest_base: continue
            distance_in_selected_unit = distance_px / self.pixels_per_metro.get()
            
            params['d_m'] = distance_in_selected_unit * scale_factor_to_meters

            rssi_at_base, path_loss = calculator_func(sensor, closest_base, params)
            rssi_at_sensor, _ = calculator_func(closest_base, sensor, params)

            intersecting_types = [obs["type"] for obs in self.obstacles if self._lines_intersect(sensor["coords"], closest_base["coords"], obs["coords"][0], obs["coords"][1])]
            report_lines.append(f"▶ NÓ SENSOR: {sensor['descricao']} (ID:{sensor['id']}) (Tx: {sensor['power_dbm']} dBm, G: {sensor['gain_dbi']} dBi)")
            report_lines.append(f"  - Conectado a: {closest_base['descricao']} (ID:{closest_base['id']}) (Tx: {closest_base['power_dbm']} dBm, G: {closest_base['gain_dbi']} dBi)")
            report_lines.append(f"  - Distância: {distance_in_selected_unit:.2f} {unit_label}"); report_lines.append(f"  - Perda de Percurso (Atenuação): {path_loss:.2f} dB")
            report_lines.append(f"  - RSSI na Base: {rssi_at_base:.2f} dBm"); report_lines.append(f"  - RSSI no Sensor (retorno): {rssi_at_sensor:.2f} dBm")
            if not intersecting_types: report_lines.append("  - Obstáculos no caminho: 0\n")
            else: counts = Counter(intersecting_types); summary = ", ".join([f"{count}x {name}" for name, count in counts.items()]); report_lines.append(f"  - Obstáculos no caminho: {len(intersecting_types)} ({summary})\n")
        textbox.insert("1.0", "\n".join(report_lines)); textbox.configure(state="disabled")
    
    def on_press(self, event):
        items = self.canvas.find_withtag("current"); item_id = items[0] if items else None
        if item_id == self.background_image_id: item_id = None
        self._drag_data.update({"item": item_id, "x": event.x, "y": event.y, "is_dragging": False})
        if self.active_tool == "Obstáculo" and not item_id: self._start_drawing_obstacle(event)
    def on_drag(self, event):
        if self.current_obstacle_id: self.canvas.coords(self.current_obstacle_id, self._drag_data['start_coords'][0], self._drag_data['start_coords'][1], event.x, event.y); return
        if not self._drag_data["item"]: return
        if not self._drag_data["is_dragging"]:
            dist = math.hypot(event.x - self._drag_data["x"], event.y - self._drag_data["y"])
            if dist > self.DRAG_THRESHOLD: self._drag_data["is_dragging"] = True; self._clear_distance_visuals()
        if self._drag_data["is_dragging"]: dx = event.x - self._drag_data["x"]; dy = event.y - self._drag_data["y"]; self._execute_drag(dx, dy); self._drag_data.update({"x": event.x, "y": event.y})
    def on_release(self, event):
        if self.current_obstacle_id: self._end_drawing_obstacle(event)
        elif self._drag_data["is_dragging"]: self._end_dragging()
        else:
            clicked_item_id = self._drag_data["item"]; now = time.time()
            if clicked_item_id and clicked_item_id == self.last_clicked_item and (now - self._last_click_time) < 0.3: self._handle_double_click(clicked_item_id); self._last_click_time = 0; self.last_clicked_item = None
            else: self._handle_single_click(event, clicked_item_id); self._last_click_time = now; self.last_clicked_item = clicked_item_id
        self._drag_data = {"x": 0, "y": 0, "item": None, "is_dragging": False}; self.current_obstacle_id = None
    def _handle_single_click(self, event, clicked_item_id):
        if clicked_item_id:
            if self.active_tool == "Excluir": self.delete_item(clicked_item_id)
        elif self.active_tool in ["Nó Sensor", "Nó Base"]: self.add_node(event)
    def _execute_drag(self, dx, dy):
        item_id = self._drag_data["item"]; node = self._get_node_by_canvas_id(item_id)
        if node: self.canvas.move(node["shape_id"], dx, dy); self.canvas.move(node["text_id"], dx, dy)
        else: self.canvas.move(item_id, dx, dy)
    def _end_dragging(self):
        item_id = self._drag_data["item"]; node = self._get_node_by_canvas_id(item_id)
        if node: coords = self.canvas.coords(node["shape_id"]); node["coords"] = ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)
        obstacle = self._get_obstacle_by_id(item_id)
        if obstacle: coords = self.canvas.coords(item_id); obstacle["coords"] = ((coords[0], coords[1]), (coords[2], coords[3]))
        self.update_distances()
    def _start_drawing_obstacle(self, event):
        start_coords = (event.x, event.y); self._drag_data['start_coords'] = start_coords; style = self.obstacle_styles[self.obstacle_type_var.get()]; self.current_obstacle_id = self.canvas.create_line(start_coords, start_coords, fill=style["color"], width=style["width"], dash=style["dash"], capstyle=tk.ROUND, tags="obstacle")
    def _end_drawing_obstacle(self, event):
        start_coords = self._drag_data['start_coords']; end_coords = (event.x, event.y)
        if start_coords == end_coords: self.canvas.delete(self.current_obstacle_id); return
        self.canvas.coords(self.current_obstacle_id, start_coords[0], start_coords[1], end_coords[0], end_coords[1])
        obs_data = {"id": self.current_obstacle_id, "coords": (start_coords, end_coords), "type": self.obstacle_type_var.get()}; self.obstacles.append(obs_data); self.action_history.append({"verb": "add", "type": "obstacle", "data": obs_data})
    def delete_item(self, canvas_id):
        node_to_delete = self._get_node_by_canvas_id(canvas_id)
        if node_to_delete: self.action_history.append({"verb": "delete", "type": "node", "data": node_to_delete}); self.nodes.remove(node_to_delete); self.canvas.delete(node_to_delete["shape_id"]); self.canvas.delete(node_to_delete["text_id"]); self.update_distances(); return
        obstacle_to_delete = self._get_obstacle_by_id(canvas_id)
        if obstacle_to_delete: self.action_history.append({"verb": "delete", "type": "obstacle", "data": obstacle_to_delete}); self.obstacles.remove(obstacle_to_delete); self.canvas.delete(obstacle_to_delete["id"]); self.update_distances()
    def _clear_distance_visuals(self):
        for item_id in self.canvas.find_withtag("distance_viz"): self.canvas.delete(item_id)
    def _update_scale_from_slider(self, value):
        self.pixels_per_metro.set(round(float(value), 1)); self.update_distances()
    def _update_scale_from_entry(self, event):
        try:
            value = float(self.scale_entry.get())
            if 5 <= value <= 150: self.pixels_per_metro.set(value)
            else: self.scale_entry.delete(0, "end"); self.scale_entry.insert(0, str(self.pixels_per_metro.get()))
        except ValueError: self.scale_entry.delete(0, "end"); self.scale_entry.insert(0, str(self.pixels_per_metro.get()))
        self.control_frame.focus(); self.update_distances()
    def _select_tool(self, tool_name):
        self.active_tool = None if self.active_tool == tool_name else tool_name; self._update_ui_for_tool_selection()
    def _update_ui_for_tool_selection(self):
        active_color, inactive_color = "#C04040", ("#3a7ebf", "#1f538d")
        for name, button in self.tool_buttons.items(): button.configure(fg_color=active_color if name == self.active_tool else inactive_color)
        if self.active_tool == "Obstáculo": self.obstacle_dropdown.pack(padx=10, pady=10, fill="x", after=self.tool_buttons["Obstáculo"]); self.canvas.config(cursor="tcross")
        else:
            self.obstacle_dropdown.pack_forget()
            if self.active_tool == "Excluir": self.canvas.config(cursor="X_cursor")
            elif self.active_tool is None: self.canvas.config(cursor="hand2")
            else: self.canvas.config(cursor="tcross")
    def undo_last_action(self):
        if not self.action_history: return
        action = self.action_history.pop()
        verb, type, data = action.values()
        if verb == "add":
            if type == "node": self.nodes.remove(data); self.canvas.delete(data["shape_id"]); self.canvas.delete(data["text_id"])
            elif type == "obstacle": self.obstacles.remove(data); self.canvas.delete(data["id"])
        elif verb == "delete":
            if type == "node":
                color = "dodgerblue" if data["type"] == "Nó Sensor" else "#2CC985"; coords = data['coords']; size = 30
                shape_id = self.canvas.create_oval(coords[0]-size/2, coords[1]-size/2, coords[0]+size/2, coords[1]+size/2, fill=color, outline="", tags=("shape", data["type"]))
                text_id = self.canvas.create_text(coords[0], coords[1], text=data["descricao"], fill="white", font=("Segoe UI", 9, "bold"), tags=("text",))
                data.update({"shape_id": shape_id, "text_id": text_id}); self.nodes.append(data)
            elif type == "obstacle":
                style = self.obstacle_styles[data["type"]]; line_id = self.canvas.create_line(data["coords"][0], data["coords"][1], fill=style["color"], width=style["width"], dash=style["dash"], capstyle=tk.ROUND, tags="obstacle")
                data["id"] = line_id; self.obstacles.append(data)
        self.update_distances()
    def _sort_key_for_nodes(self, node):
        return node.get('id', 0)
    def _get_node_by_canvas_id(self, canvas_id):
        for node in self.nodes:
            if node["shape_id"] == canvas_id or node["text_id"] == canvas_id: return node
    def _get_obstacle_by_id(self, item_id):
        for obs in self.obstacles:
            if obs["id"] == item_id: return obs
    def _find_closest_node(self, source_node, target_nodes):
        closest_node, min_dist = None, float('inf')
        for target in target_nodes:
            dist = math.hypot(source_node["coords"][0] - target["coords"][0], source_node["coords"][1] - target["coords"][1])
            if dist < min_dist: min_dist, closest_node = dist, target
        return closest_node, min_dist
    def _on_segment(self,p,q,r):return(q[0]<=max(p[0],r[0])and q[0]>=min(p[0],r[0])and q[1]<=max(p[1],r[1])and q[1]>=min(p[1],r[1]))
    def _orientation(self,p,q,r): v=(q[1]-p[1])*(r[0]-q[0])-(q[0]-p[0])*(r[1]-q[1]); return 0 if v==0 else 1 if v>0 else 2
    def _lines_intersect(self,p1,q1,p2,q2):
        o1,o2,o3,o4=self._orientation(p1,q1,p2),self._orientation(p1,q1,q2),self._orientation(p2,q2,p1),self._orientation(p2,q2,q1)
        if o1!=o2 and o3!=o4:return True;
        if o1==0 and self._on_segment(p1,p2,q1):return True;
        if o2==0 and self._on_segment(p1,q2,q1):return True;
        if o3==0 and self._on_segment(p2,p1,q2):return True;
        if o4==0 and self._on_segment(p2,q1,q2):return True;
        return False


