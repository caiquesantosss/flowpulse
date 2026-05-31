import sys
import os
import threading
import asyncio
import json
import sqlite3
import urllib.request  
from PySide6.QtWidgets import QApplication
from controllers.simulacao_controller import SimulacaoController
from views.main_window import MainWindow

# ---- CONFIGURAÇÃO DE PRODUÇÃO NUVEM ----
URL_RENDER_ATUALIZAR = "https://flowpulse-4e3g.onrender.com/api/atualizar"
# ----------------------------------------

# ---- CÓDIGO DA API HTTP E WEBSOCKET ----
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerenciador de conexões ativas do WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Envia a mensagem para todos os frontends conectados simultaneamente"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Remove conexões fantasma que caíram sem disparar o disconnect
                pass

manager = ConnectionManager()

def buscar_dados_atuais_json():
    """Função auxiliar para ler o banco de dados e estruturar o JSON de resposta"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "simulador.db")
    if not os.path.exists(db_path):
        # Fallback caso o banco esteja na raiz em tempo de execução
        db_path = "simulador.db"
        if not os.path.exists(db_path):
            return {"erro": "Banco de dados não inicializado"}
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, capacidade_maxima FROM ambientes")
    ambientes = []
    for id_amb, nome, cap in cursor.fetchall():
        cursor.execute("SELECT COUNT(*) FROM pessoas WHERE ambiente_id = ?", (id_amb,))
        presentes = cursor.fetchone()[0]
        ambientes.append({
            "id": id_amb,
            "nome": nome,
            "capacidade_maxima": cap,
            "quantidade_atual": presentes,
            "percentual_ocupacao": (presentes / cap * 100) if cap > 0 else 0
        })
        
    cursor.execute("SELECT COUNT(*) FROM pessoas")
    total_pessoas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pessoas WHERE status = 'Presente'")
    total_presentes = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_pessoas_cadastradas": total_pessoas,
        "total_pessoas_presentes": total_presentes,
        "total_pessoas_ausentes": total_pessoas - total_presentes,
        "ambientes": ambientes
    }

@api.get("/api/status")
def get_status_rest():
    """Mantém o endpoint HTTP antigo ativo por compatibilidade"""
    return buscar_dados_atuais_json()

@api.websocket("/ws/simulacao")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint do WebSocket para atualização contínua em tempo real"""
    await manager.connect(websocket)
    
    # Assim que o cliente conecta, já enviamos o estado atual imediatamente
    dados_iniciais = buscar_dados_atuais_json()
    await websocket.send_text(json.dumps(dados_iniciais))
    
    try:
        while True:
            # Mantém a conexão viva escutando mensagens do cliente (se houver)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def rodar_servidor_api(loop_compartilhado):
    import uvicorn
    # Configura o loop de eventos assíncronos correto para a thread do FastAPI
    asyncio.set_event_loop(loop_compartilhado)
    uvicorn.run(api, host="127.0.0.1", port=8000, log_level="warning")

def enviar_dados_para_render_async(dados_json):
    """Executa a requisição POST para o Render em uma thread separada para evitar engasgos na UI"""
    def thread_post():
        try:
            payload = json.dumps(dados_json).encode('utf-8')
            req = urllib.request.Request(
                URL_RENDER_ATUALIZAR,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            # Timeout curto de 3 segundos para não segurar a fila se a conexão oscilar
            with urllib.request.urlopen(req, timeout=3) as response:
                pass
        except Exception as e:
            print(f"[Nuvem] Falha ao sincronizar com o Render: {e}")

    t = threading.Thread(target=thread_post, daemon=True)
    t.start()
# ----------------------------------------

def main():
    app = QApplication(sys.argv)
    
    controller = SimulacaoController()
    window = MainWindow(controller)
    controller.set_view(window)
    
    # Criamos um loop de eventos assíncronos para a Thread do FastAPI conseguir gerenciar o WebSocket
    loop_api = asyncio.new_event_loop()
    
    # Gerenciador unificado de eventos de atualização
    def disparar_notificacao_sistema():
        dados_atualizados = buscar_dados_atuais_json()
        payload = json.dumps(dados_atualizados)
        
        # 1. Notifica o WebSocket Local (Se houver clientes locais conectados rodando em dev)
        asyncio.run_coroutine_threadsafe(manager.broadcast(payload), loop_api)
        
        # 2. Envia para a nuvem do Render para atualizar o App Mobile conectado remotamente
        if "seu-subdominio" not in URL_RENDER_ATUALIZAR:
            enviar_dados_para_render_async(dados_atualizados)

    controller.on_state_change_callback = disparar_notificacao_sistema
    
    # Inicializa o servidor FastAPI com o loop assíncrono dedicado
    api_thread = threading.Thread(target=rodar_servidor_api, args=(loop_api,), daemon=True)
    api_thread.start()
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()