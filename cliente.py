import socket
import json
import os
import bcrypt
import time
import sys
from datetime import datetime

server_host = None
server_port = None
socket_client = None
current_user = None
current_user_name = None

def clear_screen():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def hash_password(password):
    """Gera hash da senha usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def connect_to_server():
    """Conecta ao servidor de email"""
    global socket_client
    try:
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_client.connect((server_host, server_port))
        return True
    except Exception as e:
        print(f"Erro ao conectar com o servidor: {e}")
        return False

def send_request(request_data):
    """Envia uma solicitação ao servidor e recebe a resposta"""
    global socket_client
    try:
        if not socket_client:
            if not connect_to_server():
                return {'status': 'error', 'message': 'Não foi possível conectar ao servidor'}

        socket_client.send(json.dumps(request_data).encode('utf-8'))

        response = socket_client.recv(8192)
        return json.loads(response.decode('utf-8'))
    except Exception as e:
        print(f"Erro na comunicação com o servidor: {e}")
        socket_client = None
        return {'status': 'error', 'message': f'Erro na comunicação: {e}'}

def check_server_connection():
    """Verifica se o servidor está disponível"""
    return send_request({'operation': 'check_connection'})

def register_user():
    """Registra um novo usuário no serviço de email"""
    global current_user, current_user_name
    clear_screen()
    print("===== CADASTRO DE NOVA CONTA =====")

    nome = input("Nome completo: ")
    while not nome:
        print("Nome é obrigatório!")
        nome = input("Nome completo: ")

    username = input("Nome de usuário (sem espaços): ")
    while not username or ' ' in username:
        print("Nome de usuário inválido!")
        username = input("Nome de usuário (sem espaços): ")

    senha = input("Senha: ")
    while not senha:
        print("Senha é obrigatória!")
        senha = input("Senha: ")

    response = send_request({
        'operation': 'register',
        'nome': nome,
        'username': username,
        'senha': senha
    })

    print(f"\n{response['message']}")
    input("\nPressione Enter para continuar...")

def login():
    """Realiza login no serviço de email"""
    global current_user, current_user_name
    clear_screen()
    print("===== LOGIN =====")

    username = input("Nome de usuário: ")
    senha = input("Senha: ")

    response = send_request({
        'operation': 'login',
        'username': username,
        'senha': senha
    })

    if response['status'] == 'success':
        current_user = username
        current_user_name = response['nome']
        return True
    else:
        print(f"\n{response['message']}")
        input("\nPressione Enter para continuar...")
        return False

def logout():
    """Realiza logout do serviço de email"""
    global current_user, current_user_name
    response = send_request({'operation': 'logout'})
    current_user = None
    current_user_name = None
    print(f"\n{response['message']}")
    input("\nPressione Enter para continuar...")

def send_email():
    """Envia um novo email"""
    clear_screen()
    print("===== ENVIAR E-MAIL =====")

    destinatario = input("Destinatário (username): ")
    assunto = input("Assunto: ")
    print("Corpo do e-mail (termine com uma linha contendo apenas '.'): ")

    lines = []
    while True:
        line = input()
        if line == '.':
            break
        lines.append(line)

    corpo = '\n'.join(lines)

    response = send_request({
        'operation': 'send_email',
        'destinatario': destinatario,
        'assunto': assunto,
        'corpo': corpo
    })

    print(f"\n{response['message']}")
    input("\nPressione Enter para continuar...")

def receive_emails():
    """Recebe emails da caixa de entrada"""
    clear_screen()
    print("===== RECEBER E-MAILS =====")
    print("Recebendo E-mails...")

    response = send_request({'operation': 'receive_emails'})

    if response['status'] == 'success':
        emails = response.get('emails', [])
        count = len(emails)

        print(f"{count} e-mails recebidos:")

        if count > 0:
            for i, email in enumerate(emails, 1):
                print(f"[{i}] {email['remetente_nome']}: {email['assunto']}")

            try:
                choice = int(input("\nQual e-mail deseja ler (0 para voltar): "))
                if 1 <= choice <= count:
                    email = emails[choice-1]
                    clear_screen()
                    print("=" * 50)
                    print(f"De: {email['remetente_nome']} ({email['remetente']})")
                    print(f"Para: {current_user}")
                    print(f"Data/Hora: {email['data_hora']}")
                    print(f"Assunto: {email['assunto']}")
                    print("=" * 50)
                    print(f"\n{email['corpo']}")
                    print("\n" + "=" * 50)
            except ValueError:
                pass
    else:
        print(f"Erro: {response['message']}")

    input("\nPressione Enter para continuar...")

def configure_server():
    """Configura o endereço e porta do servidor"""
    global server_host, server_port
    clear_screen()
    print("===== CONFIGURAR SERVIDOR =====")

    server_host = input("Endereço IP do servidor [default: localhost]: ") or "localhost"

    try:
        port = input("Porta do servidor [default: 8080]: ") or "8080"
        server_port = int(port)
    except ValueError:
        server_port = 8080
        print("Porta inválida. Usando porta 8080.")

    print("\nTestando conexão...")
    response = check_server_connection()

    if response['status'] == 'success':
        print(f"Status: {response['message']}")
    else:
        print(f"Erro: {response['message']}")

    input("\nPressione Enter para continuar...")

def main_menu():
    """Exibe o menu principal do cliente"""
    clear_screen()
    print("===== Cliente E-mail Service BSI Online =====")
    print("1) Apontar Servidor")

    if server_host and server_port:
        print("2) Cadastrar Conta")
        print("3) Acessar E-mail")

    print("0) Sair")

    choice = input("\nEscolha uma opção: ")

    if choice == '1':
        configure_server()
    elif choice == '2' and server_host and server_port:
        register_user()
    elif choice == '3' and server_host and server_port:
        if login():
            logged_in_menu()
    elif choice == '0':
        print("Encerrando o programa...")
        if socket_client:
            socket_client.close()
        sys.exit(0)
    else:
        print("Opção inválida!")
        time.sleep(1)

def logged_in_menu():
    """Exibe o menu de usuário logado"""
    global current_user, current_user_name
    while current_user:
        clear_screen()
        print(f"Seja Bem Vindo {current_user_name}")
        print("4) Enviar E-mail")
        print("5) Receber E-mails")
        print("6) Logout")
        print("0) Sair")

        choice = input("\nEscolha uma opção: ")

        if choice == '4':
            send_email()
        elif choice == '5':
            receive_emails()
        elif choice == '6':
            logout()
            break
        elif choice == '0':
            print("Encerrando o programa...")
            if socket_client:
                socket_client.close()
            sys.exit(0)
        else:
            print("Opção inválida!")
            time.sleep(1)

def run():
    """Inicia a execução do cliente de email"""
    try:
        while True:
            main_menu()
    except KeyboardInterrupt:
        print("\nEncerrando o programa...")
        if socket_client:
            socket_client.close()
        sys.exit(0)

if __name__ == "__main__":
    run()
