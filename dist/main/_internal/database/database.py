import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_name="simulador.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Ambientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ambientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    largura REAL NOT NULL,
                    altura REAL NOT NULL,
                    cor TEXT NOT NULL,
                    capacidade_maxima INTEGER NOT NULL,
                    pos_x REAL DEFAULT 50,
                    pos_y REAL DEFAULT 50
                )
            """)
            
            # Tabela de Pessoas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pessoas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cor TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Ausente',
                    ambiente_id INTEGER,
                    FOREIGN KEY (ambiente_id) REFERENCES ambientes(id) ON DELETE SET NULL
                )
            """)
            
            # Tabela de Histórico para Gráficos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_simulacao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    taxa_ocupacao REAL NOT NULL,
                    total_presentes INTEGER NOT NULL
                )
            """)
            conn.commit()

    def limpar_historico(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historico_simulacao")
            conn.commit()