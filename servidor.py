import socket
import threading
import json
import time
import bcrypt
import os
from datetime import datetime

users = {} 
emails = {}
running = False
lock = threading.Lock()

def hash_password(password):
    """Gera hash da senha usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def start_server(host='localhost', port=8080):
    """Inicia o servidor de email"""
    global running
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        running = True

        print(f"[INFO] Servidor iniciado em {host}:{port}")

        while running:
            client_socket, client_address = server_socket.accept()
            print(f"[INFO] Nova conexão de {client_address[0]}:{client_address[1]}")

            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()

    except Exception as e:
        print(f"[ERRO] Falha ao iniciar o servidor: {e}")
    finally:
        if server_socket:
            server_socket.close()
            print("[INFO] Servidor encerrado")

def handle_client(client_socket, client_address):
    """Gerencia a comunicação com um cliente específico"""
    client_username = None
    try:
        while running:
            data = client_socket.recv(4096)
            if not data:
                break

            request = json.loads(data.decode('utf-8'))
            operation = request.get('operation')
            response = {'status': 'error', 'message': 'Operação desconhecida'}

            print(f"[INFO] Operação recebida de {client_address[0]}:{client_address[1]} - {operation}")

            if operation == 'check_connection':
                response = {'status': 'success', 'message': 'Serviço Disponível'}

            elif operation == 'register':
                response = register_user(request.get('nome'), request.get('username'), request.get('senha'))

            elif operation == 'login':
                result, nome = authenticate_user(request.get('username'), request.get('senha'))
                if result:
                    client_username = request.get('username')
                    response = {'status': 'success', 'message': 'Login realizado com sucesso', 'nome': nome}
                else:
                    response = {'status': 'error', 'message': 'Credenciais inválidas'}

            elif operation == 'send_email':
                if client_username:
                    response = send_email(client_username, request.get('destinatario'), request.get('assunto'), request.get('corpo'))
                else:
                    response = {'status': 'error', 'message': 'Usuário não autenticado'}

            elif operation == 'receive_emails':
                if client_username:
                    emails_list, response = get_emails(client_username)
                    response['emails'] = emails_list
                else:
                    response = {'status': 'error', 'message': 'Usuário não autenticado'}

            elif operation == 'logout':
                client_username = None
                response = {'status': 'success', 'message': 'Logout realizado com sucesso'}

            client_socket.send(json.dumps(response).encode('utf-8'))

    except Exception as e:
        print(f"[ERRO] Erro ao processar solicitação do cliente {client_address}: {e}")
    finally:
        print(f"[INFO] Conexão encerrada com {client_address[0]}:{client_address[1]}")
        client_socket.close()

def register_user(nome, username, senha):
    """Registra um novo usuário no sistema"""
    with lock:
        if not username or not nome or not senha:
            return {'status': 'error', 'message': 'Todos os campos são obrigatórios'}

        if username in users:
            return {'status': 'error', 'message': 'Nome de usuário já existe'}

        hashed_password = hash_password(senha)
        users[username] = {'nome': nome, 'senha': hashed_password}
        emails[username] = [] 

        print(f"[INFO] Novo usuário registrado: {username} ({nome})")
        return {'status': 'success', 'message': 'Usuário registrado com sucesso'}

def authenticate_user(username, senha):
    """Autentica um usuário usando bcrypt"""
    with lock:
        if username not in users:
            return False, None

        stored_user = users[username]
        if bcrypt.checkpw(senha.encode('utf-8'), stored_user['senha'].encode('utf-8')):
            print(f"[INFO] Login bem-sucedido: {username}")
            return True, stored_user['nome']
        else:
            print(f"[INFO] Tentativa de login falhou: {username}")
            return False, None

def send_email(remetente, destinatario, assunto, corpo):
    """Envia um email de um usuário para outro"""
    with lock:
        if destinatario not in users:
            return {'status': 'error', 'message': 'Destinatário Inexistente'}

        email = {
            'remetente': remetente,
            'remetente_nome': users[remetente]['nome'],
            'destinatario': destinatario,
            'data_hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'assunto': assunto,
            'corpo': corpo
        }

        emails[destinatario].append(email)

        print(f"[INFO] E-mail enviado: De {remetente} para {destinatario} - Assunto: {assunto}")
        return {'status': 'success', 'message': 'E-mail enviado com sucesso'}

def get_emails(username):
    """Recupera e remove emails da caixa de entrada de um usuário"""
    with lock:
        if username not in emails:
            return [], {'status': 'success', 'message': '0 e-mails recebidos'}

        user_emails = emails[username]
        count = len(user_emails)

        emails[username] = []

        print(f"[INFO] {count} e-mails entregues para {username}")
        return user_emails, {'status': 'success', 'message': f'{count} e-mails recebidos'}

def stop_server():
    """Encerra o servidor"""
    global running
    running = False
    try:
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('localhost', 8080))
    except:
        pass

if __name__ == "__main__":
    host = input("Endereço IP do servidor [default: localhost]: ") or "localhost"
    try:
        port = int(input("Porta do servidor [default: 8080]: ") or "8080")
    except ValueError:
        port = 8080
        print("Porta inválida. Usando porta 8080.")

    try:
        start_server(host, port)
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando servidor...")
        stop_server()
