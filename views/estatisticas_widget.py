from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class PainelEstatisticas(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(15)

        # KPIs Rápidos do Sistema (Cards Informativos)
        self.grid_kpi = QVBoxLayout()
        
        self.lbl_ambientes = self.criar_card("Total de Ambientes: 0")
        self.lbl_pessoas = self.criar_card("Total de Pessoas: 0")
        self.lbl_presentes = self.criar_card("Pessoas Presentes: 0", "#2ecc71")
        self.lbl_ausentes = self.criar_card("Pessoas Ausentes: 0", "#e74c3c")
        self.lbl_taxa_geral = self.criar_card("Taxa Ocupação Geral: 0.0%", "#f1c40f")

        self.grid_kpi.addWidget(self.lbl_ambientes)
        self.grid_kpi.addWidget(self.lbl_pessoas)
        self.grid_kpi.addWidget(self.lbl_presentes)
        self.grid_kpi.addWidget(self.lbl_ausentes)
        self.grid_kpi.addWidget(self.lbl_taxa_geral)
        
        layout_principal.addLayout(self.grid_kpi)

        # Divisor Visual
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setFrameShadow(QFrame.Sunken)
        linha.setStyleSheet("background-color: #444;")
        layout_principal.addWidget(linha)

        # Gráfico Matplotlib Real-Time incorporado nativamente via QTAgg
        self.fig = Figure(figsize=(4, 3), dpi=100, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.set_title("Ocupação Histórica (%)", color='white', fontsize=10)
        
        self.canvas_grafico = FigureCanvas(self.fig)
        layout_principal.addWidget(self.canvas_grafico)

        self.historico_x = []
        self.historico_y = []

    def criar_card(self, texto, cor_borda="#555"):
        label = QLabel(texto)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: #333333;
                color: #ffffff;
                border-left: 5px solid {cor_borda};
                padding: 10px;
                font-size: 12px;
                font-family: 'Segoe UI';
                font-weight: bold;
                border-radius: 3px;
            }}
        """)
        return label

    def atualizar_estatisticas(self, total_amb, total_pes, presentes, ausentes, taxa_geral, historico_pontos):
        self.lbl_ambientes.setText(f"Total de Ambientes: {total_amb}")
        self.lbl_pessoas.setText(f"Total de Pessoas: {total_pes}")
        self.lbl_presentes.setText(f"Pessoas Presentes: {presentes}")
        self.lbl_ausentes.setText(f"Pessoas Ausentes: {ausentes}")
        self.lbl_taxa_geral.setText(f"Taxa Ocupação Geral: {taxa_geral:.1f}%")

        # Processar e redesenhar gráfico em tempo real de forma assíncrona
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.set_title("Ocupação Histórica (%)", color='white', fontsize=10)
        self.ax.tick_params(colors='white')
        
        if len(historico_pontos) > 0:
            y_dados = [ponto[0] for ponto in historico_pontos]
            x_dados = np.arange(len(y_dados))
            self.ax.plot(x_dados, y_dados, color='#1abc9c', linewidth=2, marker='o', markersize=4)
            self.ax.set_ylim(-5, 105)
        else:
            self.ax.text(0.5, 0.5, 'Aguardando Simulação...', color='gray', ha='center', va='center')
            
        self.canvas_grafico.draw()