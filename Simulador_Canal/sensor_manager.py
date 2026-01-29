# Simulador_Grafico/sensor_manager.py
import customtkinter as ctk
from tkinter import messagebox
import math # Importado para o cálculo do logaritmo

class SensorTypeManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, sensor_types_config):
        super().__init__(parent)
        self.transient(parent)
        self.title("Gerenciador de Tipos de Sensores")
        self.geometry("800x650")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.grab_set()

        self.current_config = {k: v.copy() for k, v in sensor_types_config.items()}
        self.result = None
        self.field_widgets = []
        self.selected_type_name = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Frame da Esquerda (Lista de Tipos) ---
        self.left_frame = ctk.CTkFrame(self, width=200)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        self.left_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.left_frame, text="Tipos Definidos", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        self.type_list_frame = ctk.CTkScrollableFrame(self.left_frame, label_text="")
        self.type_list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nswe")
        self.type_buttons = {}
        button_frame_left = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        button_frame_left.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.new_type_button = ctk.CTkButton(button_frame_left, text="Novo", command=self._on_new)
        self.new_type_button.pack(side="left", expand=True, padx=(0, 5))
        self.delete_type_button = ctk.CTkButton(button_frame_left, text="Excluir", command=self._on_delete, fg_color="firebrick")
        self.delete_type_button.pack(side="left", expand=True, padx=(5, 0))
        self.delete_type_button.configure(state="disabled")

        # --- Frame da Direita (Detalhes do Tipo) ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nswe")
        self.right_frame.grid_columnconfigure(0, weight=1)
        
        # --- Frame de Botões Inferior ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="e")
        self.close_button = ctk.CTkButton(self.bottom_frame, text="Fechar", command=self._on_close)
        self.close_button.pack()
        
        self._populate_type_list()
        self._clear_details_panel()

    def _populate_type_list(self):
        for button in self.type_buttons.values(): button.destroy()
        self.type_buttons.clear()
        for type_name in sorted(self.current_config.keys()):
            button = ctk.CTkButton(self.type_list_frame, text=type_name, fg_color="#565b5e", command=lambda name=type_name: self._on_select_type(name))
            button.pack(padx=5, pady=2, fill="x")
            self.type_buttons[type_name] = button

    def _display_details_panel(self, type_name, config):
        ctk.CTkLabel(self.right_frame, text="Nome do Tipo:").pack(anchor="w", padx=10, pady=(10, 0))
        self.type_name_entry = ctk.CTkEntry(self.right_frame, placeholder_text="Ex: Acelerometro"); self.type_name_entry.insert(0, type_name if type_name else ""); self.type_name_entry.pack(anchor="w", padx=10, pady=(0, 10), fill="x")
        
        ctk.CTkLabel(self.right_frame, text="Arquivo da Fonte de Dados (em Nivel1/data_source/):").pack(anchor="w", padx=10)
        self.source_file_entry = ctk.CTkEntry(self.right_frame, placeholder_text="Ex: acelerometro.py"); self.source_file_entry.insert(0, config.get('source_file', '')); self.source_file_entry.pack(anchor="w", padx=10, pady=(0, 20), fill="x")

        map_frame = ctk.CTkScrollableFrame(self.right_frame, label_text="Mapeamento de Pacote"); map_frame.pack(padx=10, pady=10, fill="both", expand=True)
        header_frame = ctk.CTkFrame(map_frame, fg_color="transparent"); header_frame.pack(fill="x", padx=5)
        ctk.CTkLabel(header_frame, text="Nome do Campo", width=120).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Posição", width=90).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Tamanho", width=100).pack(side="left", padx=5)
        # MUDANÇA: O cabeçalho da coluna agora é mais intuitivo.
        ctk.CTkLabel(header_frame, text="Casas Decimais", width=60).pack(side="left", padx=5)
        
        mapping = config.get('mapeamento_pacote', {})
        for field_name, details in mapping.items(): self._add_field_row(map_frame, field_name, details)
        
        action_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent"); action_frame.pack(pady=10)
        self.add_field_button = ctk.CTkButton(action_frame, text="Adicionar Campo", command=lambda mf=map_frame: self._add_field_row(mf)); self.add_field_button.pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(action_frame, text="Salvar Alterações", command=self._on_save); self.save_button.pack(side="left", padx=5)

    def _on_select_type(self, type_name):
        self.selected_type_name = type_name
        self._clear_details_panel(title=f"Editando: {type_name}")
        for name, btn in self.type_buttons.items():
            btn.configure(fg_color="#3a7ebf" if name == type_name else "#565b5e")
        self.delete_type_button.configure(state="normal")
        config = self.current_config.get(type_name, {})
        self._display_details_panel(type_name, config)

    def _add_field_row(self, parent, name="", details=None):
        if details is None: details = {}
        row_frame = ctk.CTkFrame(parent); row_frame.pack(fill="x", pady=2, padx=5)
        entry_name = ctk.CTkEntry(row_frame, placeholder_text="nome_campo", width=120); entry_name.insert(0, name); entry_name.pack(side="left", padx=5)
        entry_pos = ctk.CTkEntry(row_frame, placeholder_text="byte", width=90); entry_pos.insert(0, details.get('posicao_byte', '')); entry_pos.pack(side="left", padx=5)
        entry_size = ctk.CTkEntry(row_frame, placeholder_text="bytes", width=100); entry_size.insert(0, details.get('tamanho_bytes', '')); entry_size.pack(side="left", padx=5)
        
        # MUDANÇA: O campo agora é para 'casas decimais' e faz a conversão reversa para exibir.
        entry_decimals = ctk.CTkEntry(row_frame, placeholder_text="ex: 1", width=60)
        escala = details.get('escala', 1)
        casas_decimais = int(math.log10(escala)) if escala > 0 else 0
        entry_decimals.insert(0, casas_decimais)
        entry_decimals.pack(side="left", padx=5)
        
        delete_button = ctk.CTkButton(row_frame, text="X", width=28, fg_color="#565b5e", command=lambda rf=row_frame: self._delete_field_row(rf)); delete_button.pack(side="left", padx=5)
        self.field_widgets.append((row_frame, entry_name, entry_pos, entry_size, entry_decimals))

    def _delete_field_row(self, row_frame):
        self.field_widgets = [w for w in self.field_widgets if w[0] is not row_frame]
        row_frame.destroy()

    def _on_new(self):
        self.selected_type_name = None
        self._clear_details_panel(title="Criando Novo Tipo de Sensor")
        for btn in self.type_buttons.values(): btn.configure(fg_color="#565b5e")
        self.delete_type_button.configure(state="disabled")
        self._display_details_panel(None, {})

    def _on_delete(self):
        if not self.selected_type_name: return
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o tipo '{self.selected_type_name}'?", parent=self):
            del self.current_config[self.selected_type_name]
            self.result = self.current_config
            self.selected_type_name = None
            self._populate_type_list()
            self._clear_details_panel()
            self.delete_type_button.configure(state="disabled")
            messagebox.showinfo("Sucesso", "Tipo de sensor excluído.", parent=self)

    def _clear_details_panel(self, title="Selecione ou crie um novo tipo"):
        for widget in self.right_frame.winfo_children(): widget.destroy()
        self.field_widgets.clear()
        ctk.CTkLabel(self.right_frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10, padx=10)

    def _on_save(self):
        original_name = self.selected_type_name
        new_name = self.type_name_entry.get().strip()
        if not new_name:
            messagebox.showerror("Erro", "O nome do tipo não pode estar vazio.", parent=self)
            return
        if new_name != original_name and new_name in self.current_config:
            messagebox.showerror("Erro", f"O nome '{new_name}' já está em uso.", parent=self)
            return
            
        new_mapping = {}
        try:
            # MUDANÇA: A lógica de salvamento agora lê "casas decimais" e calcula a "escala".
            for _, name_entry, pos_entry, size_entry, decimals_entry in self.field_widgets:
                field_name = name_entry.get().strip()
                if field_name:
                    casas_decimais = int(decimals_entry.get())
                    escala_calculada = 10 ** casas_decimais
                    new_mapping[field_name] = {'posicao_byte': int(pos_entry.get()), 'tamanho_bytes': int(size_entry.get()), 'escala': escala_calculada}
        except (ValueError, TypeError):
            messagebox.showerror("Erro", "Os campos 'Posição', 'Tamanho' e 'Decimais' devem ser números inteiros.", parent=self)
            return
        
        final_data = {'source_file': self.source_file_entry.get().strip(), 'mapeamento_pacote': new_mapping}
        if original_name and original_name in self.current_config and original_name != new_name:
            del self.current_config[original_name]
        
        self.current_config[new_name] = final_data
        self.result = self.current_config
        self.selected_type_name = new_name
        
        self._populate_type_list()
        for name, btn in self.type_buttons.items():
            btn.configure(fg_color="#3a7ebf" if name == self.selected_type_name else "#565b5e")
        messagebox.showinfo("Sucesso", f"Alterações para '{self.selected_type_name}' salvas.", parent=self)
            
    def _on_close(self):
        self.destroy()
