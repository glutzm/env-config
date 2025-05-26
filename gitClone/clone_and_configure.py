#!/usr/bin/env python3
"""
clone_and_configure.py

Um utilitário para clonar repositórios Git e aplicar configuração local de usuário
(name e email) com base no cliente informado via linha de comando.
"""
import os
import sys
import json
import subprocess
import argparse

# Determina o diretório onde o script está localizado
def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__))

# Carrega o arquivo de configuração sempre do diretório do script
def load_config(filename="config.json"):
    script_dir = get_script_dir()
    config_path = os.path.join(script_dir, filename)
    if not os.path.isfile(config_path):
        print(f"Erro: Arquivo de configuração não encontrado: {config_path}")
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erro: Falha ao ler o JSON de configuração em {config_path}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar a configuração: {e}")
        return None

def clone_repo(repo_url, dest_dir):
    print(f"Clonando repositório '{repo_url}' em '{dest_dir}'...")
    try:
        subprocess.run(["git", "clone", repo_url, dest_dir], check=True, capture_output=True)
        print("Repositório clonado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print("Erro: Falha ao clonar o repositório.")
        print(f"Comando: {' '.join(e.cmd)}")
        print(f"Stderr: {e.stderr.decode().strip()}")
        return False
    except FileNotFoundError:
        print("Erro: Comando 'git' não encontrado. Certifique-se de que o Git está instalado e no PATH.")
        return False

def apply_git_config(dest_dir, user_name, user_email):
    git_dir = os.path.join(dest_dir, '.git')

    if not os.path.isdir(git_dir):
        print(f"Erro: Diretório .git não encontrado em '{dest_dir}'. O clone falhou ou este não é um repositório Git.")
        return False

    print(f"Aplicando configuração Git local: name='{user_name}', email='{user_email}'")
    try:
        subprocess.run(["git", "config", "--local", "user.name", user_name], cwd=dest_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "--local", "user.email", user_email], cwd=dest_dir, check=True, capture_output=True)
        print("Configuração Git local aplicada com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print("Erro: Falha ao aplicar a configuração Git local.")
        print(f"Comando: {' '.join(e.cmd)}")
        print(f"Stderr: {e.stderr.decode().strip()}")
        return False
    except FileNotFoundError:
        print("Erro: Comando 'git' não encontrado durante a configuração.")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Clona um repositório Git e opcionalmente aplica configuração local de usuário (name/email) baseada em um cliente.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-c', '--cliente',
        help='Nome do cliente (definido em config.json) para buscar o email correspondente.',
        required=False
    )
    parser.add_argument(
        'repo_url',
        metavar='url-do-repositorio',
        help='URL do repositório Git a ser clonado.'
    )
    parser.add_argument(
        'dest_dir',
        metavar='diretorio-de-destino',
        help='Diretório onde o repositório será clonado.'
    )

    args = parser.parse_args()

    # 1. Clonar o repositório
    if not clone_repo(args.repo_url, args.dest_dir):
        sys.exit(1)

    # 2. Se um cliente foi especificado, tentar aplicar a configuração
    if args.cliente:
        print(f"Tentando aplicar configuração para o cliente: '{args.cliente}'")
        config = load_config()
        if config is None:
            print("Não foi possível carregar a configuração. A configuração local do Git não será aplicada.")
            sys.exit(1)

        git_user_name = config.get('gitUserName')
        clientes = config.get('clientes', {})
        cliente_info = clientes.get(args.cliente)

        if not git_user_name:
            print("Erro: 'gitUserName' não encontrado ou vazio no config.json.")
            sys.exit(1)

        if not cliente_info:
            print(f"Erro: Cliente '{args.cliente}' não encontrado na seção 'clientes' do config.json.")
            sys.exit(1)

        git_email = cliente_info.get('gitEmail')
        if not git_email:
            print(f"Erro: 'gitEmail' não encontrado para o cliente '{args.cliente}' no config.json.")
            sys.exit(1)

        # Aplicar a configuração
        if not apply_git_config(args.dest_dir, git_user_name, git_email):
            sys.exit(1)
    else:
        print("Nenhum cliente especificado. O repositório foi clonado sem configuração local de usuário/email.")

if __name__ == '__main__':
    main()

