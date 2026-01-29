# components.py
import customtkinter as ctk
from tkinter import messagebox

class NodePropertiesWindow(ctk.CTkToplevel):
    def __init__(self, parent, node_data, available_types):
        super().__init__(parent)
        self.transient(parent)
        self.title(f"Propriedades de {node_data.get('descricao', node_data.get('id', ''))}")
        self.geometry("320x460")
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()
        self.result = None
        
        # --- ID do Nó (agora editável) ---
        self.id_label = ctk.CTkLabel(self, text="ID do Nó (único, numérico):")
        self.id_entry = ctk.CTkEntry(self) # Não está mais desabilitado
        self.id_entry.insert(0, str(node_data.get('id', '')))

        # --- Campo de Descrição ---
        self.description_label = ctk.CTkLabel(self, text="Descrição:")
        self.description_entry = ctk.CTkEntry(self)
        self.description_entry.insert(0, node_data.get('descricao', ''))
        
        # --- Campos de RF ---
        self.power_label = ctk.CTkLabel(self, text="Potência de Transmissão (dBm):")
        self.power_entry = ctk.CTkEntry(self)
        self.power_entry.insert(0, str(node_data['power_dbm']))

        self.gain_label = ctk.CTkLabel(self, text="Ganho da Antena (dBi):")
        self.gain_entry = ctk.CTkEntry(self)
        self.gain_entry.insert(0, str(node_data['gain_dbi']))

        # --- Menu de Seleção "Tipo de Sensor" ---
        self.type_label = ctk.CTkLabel(self, text="Tipo de Sensor de Aplicação:")
        self.sensor_type_var = ctk.StringVar(value=node_data.get('sensor_type', available_types[0] if available_types else ""))
        self.type_menu = ctk.CTkOptionMenu(self, variable=self.sensor_type_var, values=available_types)
        if not available_types:
            self.type_menu.configure(state="disabled")

        # --- Botões ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancelar", command=self._on_cancel)
        self.save_button = ctk.CTkButton(self.button_frame, text="Salvar", command=self._on_save)

        # --- Posicionamento (Layout) ---
        self.id_label.pack(pady=(20, 2), padx=20, anchor="w")
        self.id_entry.pack(pady=(0, 10), padx=20, fill="x")
        self.description_label.pack(pady=(10, 2), padx=20, anchor="w")
        self.description_entry.pack(pady=(0, 10), padx=20, fill="x")
        self.power_label.pack(pady=(10, 2), padx=20, anchor="w")
        self.power_entry.pack(pady=(0, 10), padx=20, fill="x")
        self.gain_label.pack(pady=(10, 2), padx=20, anchor="w")
        self.gain_entry.pack(pady=(0, 10), padx=20, fill="x")
        self.type_label.pack(pady=(10, 2), padx=20, anchor="w")
        self.type_menu.pack(pady=(0, 20), padx=20, fill="x")
        
        self.button_frame.pack(pady=10)
        self.cancel_button.pack(side="left", padx=10)
        self.save_button.pack(side="left", padx=10)
        
    def _on_save(self):
        try:
            # Coleta os dados dos campos, incluindo o novo ID como um inteiro.
            # Se o ID não for um número, a linha abaixo vai gerar um ValueError.
            new_id = int(self.id_entry.get())
            
            self.result = {
                "id": new_id,
                "descricao": self.description_entry.get().strip(), 
                "power_dbm": float(self.power_entry.get()), 
                "gain_dbi": float(self.gain_entry.get()),
            }
            # Só adiciona o tipo de sensor ao resultado se o menu estiver habilitado
            if self.type_menu.cget("state") == "normal":
                self.result["sensor_type"] = self.sensor_type_var.get()
            
            self.destroy()
        except ValueError: 
            # Se o usuário digitar algo que não é um número no campo ID (ou nos outros),
            # mostra uma mensagem de erro e não fecha a janela.
            messagebox.showerror("Erro de Validação", "O ID deve ser um número inteiro. \nPotência e Ganho devem ser números.", parent=self)
            
    def _on_cancel(self): 
        self.result = None
        self.destroy()
