from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF

class VisualAmbiente(QGraphicsRectItem):
    def __init__(self, ambiente, controller):
        # Conversão de escala: 1 metro = 30 pixels no Canvas para visibilidade estável
        self.escala = 30.0
        largura_px = ambiente.largura * self.escala
        altura_px = ambiente.altura * self.escala
        
        super().__init__(0, 0, largura_px, altura_px)
        
        self.ambiente = ambiente
        self.controller = controller
        
        self.setPos(ambiente.pos_x, ambiente.pos_y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Componente de texto para renderizar label dentro do ambiente
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.text_item.setDefaultTextColor(QColor("#ffffff"))
        
        self.atualizar_visual()

    def atualizar_visual(self):
        largura_px = self.ambiente.largura * self.escala
        altura_px = self.ambiente.altura * self.escala
        self.setRect(0, 0, largura_px, altura_px)
        
        cor_base = QColor(self.ambiente.cor)
        self.setBrush(QBrush(cor_base))
        
        if self.isSelected():
            pen = QPen(QColor("#f1c40f"), 3, Qt.DashLine)
        else:
            pen = QPen(cor_base.darker(150), 2)
        self.setPen(pen)
        
        # Atualização de texto dinâmico (Ocupação e Capacidade)
        texto = f"{self.ambiente.nome}\nCap: {self.ambiente.quantidade_atual}/{self.ambiente.capacidade_maxima}\n({self.ambiente.percentual_ocupacao:.1f}%)"
        self.text_item.setPlainText(texto)
        
        # Centralizar texto suavemente
        rect_texto = self.text_item.boundingRect()
        self.text_item.setPos((largura_px - rect_texto.width()) / 2, (altura_px - rect_texto.height()) / 2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Captura a nova posição arrastada e persiste em memória instantaneamente
            nova_pos = value
            self.ambiente.pos_x = nova_pos.x()
            self.ambiente.pos_y = nova_pos.y()
            self.controller.salvar_ambiente_estado(self.ambiente)
        return super().itemChange(change, value)