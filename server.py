# server.py

import os
import json
import sqlite3

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Caminho absoluto do banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "simulador.db")

app = FastAPI(title="Servidor Simulador de Presença")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        desconectados = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                desconectados.append(connection)

        for connection in desconectados:
            self.disconnect(connection)


manager = ConnectionManager()


def buscar_dados_atuais_json():
    if not os.path.exists(DB_PATH):
        return {
            "erro": f"Banco de dados não encontrado: {DB_PATH}"
        }

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        ambientes = []

        cursor.execute("""
            SELECT id, nome, capacidade_maxima
            FROM ambientes
        """)

        for ambiente in cursor.fetchall():
            ambiente_id = ambiente["id"]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pessoas
                WHERE ambiente_id = ?
                """,
                (ambiente_id,)
            )

            presentes = cursor.fetchone()[0]
            capacidade = ambiente["capacidade_maxima"] or 0

            ambientes.append({
                "id": ambiente_id,
                "nome": ambiente["nome"],
                "capacidade_maxima": capacidade,
                "quantidade_atual": presentes,
                "percentual_ocupacao": (
                    round((presentes / capacidade) * 100, 2)
                    if capacidade > 0
                    else 0
                )
            })

        cursor.execute("SELECT COUNT(*) FROM pessoas")
        total_pessoas = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM pessoas
            WHERE status = 'Presente'
        """)
        total_presentes = cursor.fetchone()[0]

        return {
            "total_pessoas_cadastradas": total_pessoas,
            "total_pessoas_presentes": total_presentes,
            "total_pessoas_ausentes": total_pessoas - total_presentes,
            "ambientes": ambientes
        }

    except sqlite3.Error as e:
        return {
            "erro": f"Erro de banco de dados: {str(e)}"
        }

    finally:
        conn.close()


@app.get("/")
def root():
    return {
        "status": "online",
        "websockets_conectados": len(manager.active_connections)
    }


@app.get("/api/status")
def get_status():
    return buscar_dados_atuais_json()


@app.post("/api/atualizar")
async def receber_atualizacao(dados: dict):
    try:
        payload = json.dumps(dados, ensure_ascii=False)

        await manager.broadcast(payload)

        return {
            "status": "propagado",
            "clientes": len(manager.active_connections)
        }

    except Exception as e:
        return {
            "erro": str(e)
        }


@app.websocket("/ws/simulacao")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        await websocket.send_text(
            json.dumps(
                buscar_dados_atuais_json(),
                ensure_ascii=False
            )
        )

        while True:
            dados_recebidos = await websocket.receive_text()

            await manager.broadcast(dados_recebidos)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        print(f"Erro WebSocket: {e}")
        manager.disconnect(websocket)