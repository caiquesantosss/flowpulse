from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QGraphicsView, QGraphicsScene, QGroupBox, QFormLayout, 
                             QColorDialog, QMessageBox, QSplitter)
from PySide6.QtGui import QColor, QBrush, QPen, QIcon
from PySide6.QtCore import Qt, QTimer
from views.ambiente_widget import VisualAmbiente
from views.estatisticas_widget import PainelEstatisticas

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Simulador Avançado de Presença em Ambientes de TI")
        self.resize(1300, 800)
        self.cor_selecionada_ambiente = "#3498db"
        self.cor_selecionada_pessoa = "#e74c3c"
        
        self.aplicar_tema_escuro()
        self.init_ui()
        
        # Renderização inicial de dados históricos restaurados
        self.sincronizar_canvas_e_listas()

    def aplicar_tema_escuro(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI'; }
            QGroupBox { border: 2px solid #333333; border-radius: 6px; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #555; border-radius: 4px; padding: 5px; color: white; }
            QPushButton { background-color: #0e639c; border: none; border-radius: 4px; padding: 8px 15px; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #0c5281; }
            QListWidget { background-color: #252526; border: 1px solid #333; border-radius: 4px; }
            QScrollBar:vertical { border: none; background: #2d2d2d; width: 10px; }
            QScrollBar::handle:vertical { background: #555; border-radius: 5px; }
        """)

    def init_ui(self):
        # Widget Central Dividido estruturalmente por um QSplitter resiliente
        splitter_principal = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter_principal)

        # ---------------- BARRA LATERAL ESQUERDA (Controles e Cadastros) ----------------
        barra_lateral = QWidget()
        layout_lateral = QVBoxLayout(barra_lateral)
        layout_lateral.setContentsMargins(10, 10, 10, 10)

        # Painel Controle de Fluxo da Simulação
        grp_simulacao = QGroupBox("Controle do Motor de Simulação")
        lyt_simulacao = QHBoxLayout(grp_simulacao)
        self.btn_play = QPushButton("Iniciar")
        self.btn_play.setStyleSheet("background-color: #27ae60;")
        self.btn_play.clicked.connect(self.alternar_simulacao)
        self.btn_reset = QPushButton("Reiniciar")
        self.btn_reset.setStyleSheet("background-color: #7f8c8d;")
        self.btn_reset.clicked.connect(self.reiniciar_simulacao)
        lyt_simulacao.addWidget(self.btn_play)
        lyt_simulacao.addWidget(self.btn_reset)
        layout_lateral.addWidget(grp_simulacao)

        # Form de Cadastro de Ambientes
        grp_amb = QGroupBox("Gerenciamento de Ambientes")
        lyt_amb = QFormLayout(grp_amb)
        self.txt_amb_nome = QLineEdit()
        self.txt_amb_largura = QLineEdit("5")
        self.txt_amb_altura = QLineEdit("5")
        self.txt_amb_cap = QLineEdit("10")
        self.btn_amb_cor = QPushButton("Escolher Cor")
        self.btn_amb_cor.setStyleSheet("background-color: #3498db;")
        self.btn_amb_cor.clicked.connect(self.abrir_paleta_ambiente)
        
        self.btn_salvar_amb = QPushButton("Adicionar Ambiente")
        self.btn_salvar_amb.clicked.connect(self.adicionar_ambiente_clique)
        self.btn_deletar_amb = QPushButton("Excluir Selecionado")
        self.btn_deletar_amb.setStyleSheet("background-color: #c0392b;")
        self.btn_deletar_amb.clicked.connect(self.deletar_ambiente_clique)

        lyt_amb.addRow("Nome:", self.txt_amb_nome)
        lyt_amb.addRow("Largura (m):", self.txt_amb_largura)
        lyt_amb.addRow("Altura (m):", self.txt_amb_altura)
        lyt_amb.addRow("Capacidade:", self.txt_amb_cap)
        lyt_amb.addRow("Visual:", self.btn_amb_cor)
        lyt_amb.addRow(self.btn_salvar_amb)
        lyt_amb.addRow(self.btn_deletar_amb)
        layout_lateral.addWidget(grp_amb)

        # Form de Cadastro de Pessoas
        grp_pes = QGroupBox("Gerenciamento de Pessoas")
        lyt_pes = QFormLayout(grp_pes)
        self.txt_pes_nome = QLineEdit()
        self.btn_pes_cor = QPushButton("Escolher Cor")
        self.btn_pes_cor.setStyleSheet("background-color: #e74c3c;")
        self.btn_pes_cor.clicked.connect(self.abrir_paleta_pessoa)
        
        self.btn_salvar_pes = QPushButton("Cadastrar Pessoa")
        self.btn_salvar_pes.clicked.connect(self.adicionar_pessoa_clique)
        self.btn_deletar_pes = QPushButton("Remover Pessoa")
        self.btn_deletar_pes.setStyleSheet("background-color: #c0392b;")
        self.btn_deletar_pes.clicked.connect(self.deletar_pessoa_clique)

        self.list_pessoas = QListWidget()
        self.list_pessoas.setMaximumHeight(150)

        lyt_pes.addRow("Nome:", self.txt_pes_nome)
        lyt_pes.addRow("Identidade Visual:", self.btn_pes_cor)
        lyt_pes.addRow(self.btn_salvar_pes)
        lyt_pes.addRow(self.list_pessoas)
        lyt_pes.addRow(self.btn_deletar_pes)
        layout_lateral.addWidget(grp_pes)

        splitter_principal.addWidget(barra_lateral)

        # ---------------- ÁREA CENTRAL (Canvas de Simulação) ----------------
        container_canvas = QWidget()
        layout_canvas = QVBoxLayout(container_canvas)
        layout_canvas.setContentsMargins(5, 10, 5, 10)
        
        lbl_canvas = QLabel("Área Computacional de Simulação Espacial (Arraste os Ambientes)")
        lbl_canvas.setStyleSheet("font-weight: bold; font-size: 13px; color: #aaa;")
        layout_canvas.addWidget(lbl_canvas)

        self.scene = QGraphicsScene(0, 0, 2000, 2000)
        self.scene.setBackgroundBrush(QBrush(QColor("#1a1a1a")))
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        layout_canvas.addWidget(self.view)

        splitter_principal.addWidget(container_canvas)

        # ---------------- PAINEL DIREITO (Estatísticas e Gráficos) ----------------
        self.painel_estatisticas = PainelEstatisticas(self.controller)
        splitter_principal.addWidget(self.painel_estatisticas)

        # Ajuste inicial das proporções de divisão de tela
        splitter_principal.setSizes([300, 650, 350])

    def abrir_paleta_ambiente(self):
        cor = QColorDialog.getColor(QColor(self.cor_selecionada_ambiente), self)
        if cor.isValid():
            self.cor_selecionada_ambiente = cor.name()
            self.btn_amb_cor.setStyleSheet(f"background-color: {cor.name()};")

    def abrir_paleta_pessoa(self):
        cor = QColorDialog.getColor(QColor(self.cor_selecionada_pessoa), self)
        if cor.isValid():
            self.cor_selecionada_pessoa = cor.name()
            self.btn_pes_cor.setStyleSheet(f"background-color: {cor.name()};")

    def adicionar_ambiente_clique(self):
        nome = self.txt_amb_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Insira o nome do ambiente.")
            return
        try:
            largura = float(self.txt_amb_largura.text())
            altura = float(self.txt_amb_altura.text())
            capacidade = int(self.txt_amb_cap.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Parâmetros dimensionais inválidos.")
            return

        self.controller.criar_ambiente(nome, largura, altura, self.cor_selecionada_ambiente, capacity := capacidade)
        self.sincronizar_canvas_e_listas()
        self.txt_amb_nome.clear()

        # [SINCRO NUVEM] Força envio imediato após inserção
        if hasattr(self.controller, 'on_state_change_callback') and self.controller.on_state_change_callback:
            self.controller.on_state_change_callback()

    def deletar_ambiente_clique(self):
        itens_selecionados = self.scene.selectedItems()
        mudou = False
        for item in itens_selecionados:
            if isinstance(item, VisualAmbiente):
                self.controller.remover_ambiente(item.ambiente.id)
                self.scene.removeItem(item)
                mudou = True
        self.sincronizar_canvas_e_listas()

        # [SINCRO NUVEM] Força envio imediato após exclusão
        if mudou and hasattr(self.controller, 'on_state_change_callback') and self.controller.on_state_change_callback:
            self.controller.on_state_change_callback()

    def adicionar_pessoa_clique(self):
        nome = self.txt_pes_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Insira o nome da pessoa.")
            return
        self.controller.criar_pessoa(nome, self.cor_selecionada_pessoa)
        self.sincronizar_canvas_e_listas()
        self.txt_pes_nome.clear()

        # [SINCRO NUVEM] Força envio imediato após cadastro de pessoa
        if hasattr(self.controller, 'on_state_change_callback') and self.controller.on_state_change_callback:
            self.controller.on_state_change_callback()

    def deletar_pessoa_clique(self):
        item_atual = self.list_pessoas.currentItem()
        if item_atual:
            pessoa_id = item_atual.data(Qt.UserRole)
            self.controller.remover_pessoa(pessoa_id)
            self.sincronizar_canvas_e_listas()

            # [SINCRO NUVEM] Força envio imediato após remoção de pessoa
            if hasattr(self.controller, 'on_state_change_callback') and self.controller.on_state_change_callback:
                self.controller.on_state_change_callback()

    def alternar_simulacao(self):
        if self.controller.simulacao_ativa:
            self.controller.pausar_simulacao()
            self.btn_play.setText("Iniciar")
            self.btn_play.setStyleSheet("background-color: #27ae60;")
        else:
            self.controller.iniciar_simulacao()
            self.btn_play.setText("Pausar")
            self.btn_play.setStyleSheet("background-color: #d35400;")

    def reiniciar_simulacao(self):
        self.controller.reiniciar_simulacao()
        self.btn_play.setText("Iniciar")
        self.btn_play.setStyleSheet("background-color: #27ae60;")
        self.sincronizar_canvas_e_listas()

        # [SINCRO NUVEM] Zera o estado no Render imediatamente
        if hasattr(self.controller, 'on_state_change_callback') and self.controller.on_state_change_callback:
            self.controller.on_state_change_callback()

    def sincronizar_canvas_e_listas(self):
        # 1. Atualizar List Box de Pessoas de forma desacoplada
        self.list_pessoas.clear()
        for p in self.controller.pessoas.values():
            item = QListWidgetItem(f"{p.nome} ({p.status})")
            item.setData(Qt.UserRole, p.id)
            self.list_pessoas.addItem(item)

        # 2. Atualizar renderização gráfica no Canvas
        itens_existentes = {item.ambiente.id: item for item in self.scene.items() if isinstance(item, VisualAmbiente)}
        
        for amb_id, item in itens_existentes.items():
            if amb_id not in self.controller.ambientes:
                self.scene.removeItem(item)

        for amb in self.controller.ambientes.values():
            if amb.id in itens_existentes:
                itens_existentes[amb.id].atualizar_visual()
            else:
                novo_visual = VisualAmbiente(amb, self.controller)
                self.scene.addItem(novo_visual)

        # 3. Limpar círculos antigos de pessoas
        for item in self.scene.items():
            if hasattr(item, "is_pessoa_marker"):
                self.scene.removeItem(item)

        # 4. Renderizar novas posições espaciais
        escala = 30.0
        for amb in self.controller.ambientes.values():
            for p in amb.pessoas_presentes:
                p_global_x = amb.pos_x + (p.canvas_x * escala)
                p_global_y = amb.pos_y + (p.canvas_y * escala)
                
                raio = 6
                circulo = self.scene.addEllipse(p_global_x - raio, p_global_y - raio, raio*2, raio*2, 
                                                QPen(QColor("#ffffff"), 1), QBrush(QColor(p.cor)))
                circulo.is_pessoa_marker = True
                circulo.setToolTip(f"Pessoa: {p.nome}")

        # 5. Forçar recalculação do dashboard de estatísticas
        self.controller.recalcular_metricas_gerais()