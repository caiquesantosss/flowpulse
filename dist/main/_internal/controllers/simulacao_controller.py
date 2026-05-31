import random
from PySide6.QtCore import QObject, QTimer
from database.database import DatabaseManager
from models.ambiente import Ambiente
from models.pessoa import Pessoa

class SimulacaoController(QObject):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.ambientes = {}
        self.pessoas = {}
        self.simulacao_ativa = False
        
        # Timer cíclico para o loop da simulação (Passo de 1 segundo)
        self.timer = QTimer()
        self.timer.timeout.connect(self.processar_passo_simulacao)
        
        self.carregar_dados_iniciais()
        self.main_window = None

    def set_view(self, window):
        self.main_window = window

    def carregar_dados_iniciais(self):
        # Recuperação íntegra de dados do SQLite para memória RAM operacional
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Carregar Ambientes
            cursor.execute("SELECT id, nome, largura, altura, cor, capacidade_maxima, pos_x, pos_y FROM ambientes")
            for linha in cursor.fetchall():
                amb = Ambiente(linha[0], linha[1], linha[2], linha[3], linha[4], linha[5], linha[6], linha[7])
                self.ambientes[amb.id] = amb
            
            # Carregar Pessoas
            cursor.execute("SELECT id, nome, cor, status, ambiente_id FROM pessoas")
            for linha in cursor.fetchall():
                p = Pessoa(linha[0], linha[1], linha[2], linha[3], linha[4])
                self.pessoas[p.id] = p
                if p.ambiente_id and p.ambiente_id in self.ambientes:
                    # Posicionar randomicamente dentro do ambiente recuperado
                    amb_alvo = self.ambientes[p.ambiente_id]
                    p.canvas_x = random.uniform(0.5, max(0.6, amb_alvo.largura - 0.5))
                    p.canvas_y = random.uniform(0.5, max(0.6, amb_alvo.altura - 0.5))
                    amb_alvo.pessoas_presentes.append(p)
                else:
                    p.status = "Ausente"
                    p.ambiente_id = None

    def criar_ambiente(self, nome, largura, altura, cor, capacidade):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ambientes (nome, largura, altura, cor, capacidade_maxima, pos_x, pos_y)
                VALUES (?, ?, ?, ?, ?, 50, 50)
            """, (nome, largura, altura, cor, capacidade))
            novo_id = cursor.lastrowid
        
        self.ambientes[novo_id] = Ambiente(novo_id, nome, largura, altura, cor, capacidade)

    def salvar_ambiente_estado(self, ambiente):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ambientes SET pos_x = ?, pos_y = ? WHERE id = ?
            """, (ambiente.pos_x, ambiente.pos_y, ambiente.id))

    def remover_ambiente(self, amb_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ambientes WHERE id = ?", (amb_id,))
            cursor.execute("UPDATE pessoas SET ambiente_id = NULL, status = 'Ausente' WHERE ambiente_id = ?", (amb_id,))
        
        if amb_id in self.ambientes:
            for p in self.ambientes[amb_id].pessoas_presentes:
                p.ambiente_id = None
                p.status = "Ausente"
            del self.ambientes[amb_id]

    def criar_pessoa(self, nome, cor):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pessoas (nome, cor, status, ambiente_id) VALUES (?, ?, 'Ausente', NULL)
            """, (nome, cor))
            novo_id = cursor.lastrowid
            
        self.pessoas[novo_id] = Pessoa(novo_id, nome, cor)

    def remover_pessoa(self, pes_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pessoas WHERE id = ?", (pes_id,))
        
        if pes_id in self.pessoas:
            p = self.pessoas[pes_id]
            if p.ambiente_id and p.ambiente_id in self.ambientes:
                self.ambientes[p.ambiente_id].remover_pessoa(p)
            del self.pessoas[pes_id]

    def iniciar_simulacao(self):
        self.simulacao_ativa = True
        self.timer.start(1000)

    def pausar_simulacao(self):
        self.simulacao_ativa = False
        self.timer.stop()

    def reiniciar_simulacao(self):
        self.pausar_simulacao()
        self.db.limpar_historico()
        
        # Desalocar todas as pessoas de volta para o estado Ausente
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE pessoas SET ambiente_id = NULL, status = 'Ausente'")
            
        for amb in self.ambientes.values():
            amb.pessoas_presentes.clear()
            
        for p in self.pessoas.values():
            p.ambiente_id = None
            p.status = "Ausente"

    def processar_passo_simulacao(self):
        if not self.ambientes or not self.pessoas:
            return

        lista_ambientes = list(self.ambientes.values())
        lista_pessoas = list(self.pessoas.values())

        # Motor Estocástico: Sorteia uma ação aleatória para simular comportamento real
        acao = random.choice(["entrar", "sair", "mover"])

        if acao == "entrar":
            p = random.choice(lista_pessoas)
            if p.status == "Ausente":
                amb = random.choice(lista_ambientes)
                if amb.quantidade_atual < amb.capacidade_maxima:
                    p.canvas_x = random.uniform(0.5, max(0.6, amb.largura - 0.5))
                    p.canvas_y = random.uniform(0.5, max(0.6, amb.altura - 0.5))
                    amb.adicionar_pessoa(p)
                    self.atualizar_pessoa_db(p)

        elif acao == "sair":
            p = random.choice(lista_pessoas)
            if p.status == "Presente" and p.ambiente_id in self.ambientes:
                self.ambientes[p.ambiente_id].remover_pessoa(p)
                self.atualizar_pessoa_db(p)

        elif acao == "mover":
            # Pessoas andam pequenas distâncias dentro do mesmo ambiente simulando dinamismo
            for amb in self.ambientes.values():
                for p in amb.pessoas_presentes:
                    p.canvas_x = max(0.3, min(amb.largura - 0.3, p.canvas_x + random.uniform(-0.4, 0.4)))
                    p.canvas_y = max(0.3, min(amb.altura - 0.3, p.canvas_y + random.uniform(-0.4, 0.4)))

        # Sincronizar UI e persistir telemetria histórica
        if self.main_window:
            self.main_window.sincronizar_canvas_e_listas()

    def atualizar_pessoa_db(self, pessoa):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pessoas SET status = ?, ambiente_id = ? WHERE id = ?
            """, (pessoa.status, pessoa.ambiente_id, pessoa.id))

    def recalcular_metricas_gerais(self):
        total_amb = len(self.ambientes)
        total_pes = len(self.pessoas)
        presentes = sum(1 for p in self.pessoas.values() if p.status == "Presente")
        ausentes = total_pes - presentes
        
        capacidade_total_predio = sum(amb.capacidade_maxima for amb in self.ambientes.values())
        taxa_geral = (presentes / capacidade_total_predio * 100.0) if capacidade_total_predio > 0 else 0.0

        # Gravar métricas consolidadas na tabela de histórico se a simulação estiver rodando
        if self.simulacao_ativa:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO historico_simulacao (taxa_ocupacao, total_presentes) VALUES (?, ?)
                """, (taxa_geral, presentes))

        # Buscar últimos 30 pontos para plotagem no painel
        historico_pontos = []
        if total_amb > 0:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT taxa_ocupacao FROM historico_simulacao ORDER BY id DESC LIMIT 30")
                historico_pontos = cursor.fetchall()
                historico_pontos.reverse()

        if self.main_window and hasattr(self.main_window, 'painel_estatisticas'):
            self.main_window.painel_estatisticas.atualizar_estatisticas(
                total_amb, total_pes, presentes, ausentes, taxa_geral, historico_pontos
            )

def processar_passo_simulacao(self):
        if not self.ambientes or not self.pessoas:
            return

        lista_ambientes = list(self.ambientes.values())
        lista_pessoas = list(self.pessoas.values())

        # Motor Estocástico: Sorteia uma ação aleatória
        acao = random.choice(["entrar", "sair", "mover"])

        if acao == "entrar":
            p = random.choice(lista_pessoas)
            if p.status == "Ausente":
                amb = random.choice(lista_ambientes)
                if amb.quantidade_atual < amb.capacidade_maxima:
                    p.canvas_x = random.uniform(0.5, max(0.6, amb.largura - 0.5))
                    p.canvas_y = random.uniform(0.5, max(0.6, amb.altura - 0.5))
                    amb.adicionar_pessoa(p)
                    self.atualizar_pessoa_db(p)

        elif acao == "sair":
            p = random.choice(lista_pessoas)
            if p.status == "Presente" and p.ambiente_id in self.ambientes:
                self.ambientes[p.ambiente_id].remover_pessoa(p)
                self.atualizar_pessoa_db(p)

        elif acao == "mover":
            for amb in self.ambientes.values():
                for p in amb.pessoas_presentes:
                    p.canvas_x = max(0.3, min(amb.largura - 0.3, p.canvas_x + random.uniform(-0.4, 0.4)))
                    p.canvas_y = max(0.3, min(amb.altura - 0.3, p.canvas_y + random.uniform(-0.4, 0.4)))

        # Sincronizar UI e persistir telemetria histórica
        if self.main_window:
            self.main_window.sincronizar_canvas_e_listas()

        # [NOVO] Notificar o servidor WebSocket que houve uma mudança de estado!
        if hasattr(self, 'on_state_change_callback') and self.on_state_change_callback:
            self.on_state_change_callback()           