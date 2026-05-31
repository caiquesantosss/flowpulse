class Ambiente:
    def __init__(self, id_db=None, nome="", largura=5.0, altura=5.0, cor="#3498db", capacidade_maxima=10, pos_x=50.0, pos_y=50.0):
        self.id = id_db
        self.nome = nome
        self.largura = float(largura)  # Em metros
        self.altura = float(altura)    # Em metros
        self.cor = cor
        self.capacidade_maxima = int(capacidade_maxima)
        self.pos_x = float(pos_x)
        self.pos_y = float(pos_y)
        self.pessoas_presentes = []

    @property
    def quantidade_atual(self):
        return len(self.pessoas_presentes)

    @property
    def percentual_ocupacao(self):
        if self.capacidade_maxima == 0:
            return 0.0
        return (self.quantidade_atual / self.capacidade_maxima) * 100.0

    def adicionar_pessoa(self, pessoa):
        if self.quantidade_atual < self.capacidade_maxima and pessoa not in self.pessoas_presentes:
            self.pessoas_presentes.append(pessoa)
            pessoa.ambiente_id = self.id
            pessoa.status = "Presente"
            return True
        return False

    def remover_pessoa(self, pessoa):
        if pessoa in self.pessoas_presentes:
            self.pessoas_presentes.remove(pessoa)
            pessoa.ambiente_id = None
            pessoa.status = "Ausente"
            return True
        return False