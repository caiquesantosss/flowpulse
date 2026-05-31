class Pessoa:
    def __init__(self, id_db=None, nome="", cor="#e74c3c", status="Ausente", ambiente_id=None):
        self.id = id_db
        self.nome = nome
        self.cor = cor
        self.status = status  # 'Presente' ou 'Ausente'
        self.ambiente_id = ambiente_id  # ID do ambiente em que está, ou None
        
        # Atributos de coordenada interna para renderização fluida no Canvas
        self.canvas_x = 0.0
        self.canvas_y = 0.0