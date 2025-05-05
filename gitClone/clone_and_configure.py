#!/usr/bin/env python3
"""
clone_and_configure.py

Um utilitário para clonar repositórios Git e aplicar configuração local de usuário
(name e email) com base na URL base do repositório.
"""
import os
import sys
import json
import subprocess
from urllib.parse import urlparse

# Determina o diretório onde o script está localizado
def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__))

# Carrega o arquivo de configuração sempre do diretório do script
def load_config(filename="config.json"):
    script_dir = get_script_dir()
    config_path = os.path.join(script_dir, filename)
    if not os.path.isfile(config_path):
        print(f"Arquivo de configuração não encontrado: {config_path}")
        sys.exit(1)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erro ao ler JSON de configuração em {config_path}: {e}")
        sys.exit(1)

def usage():
    print(f"Uso: {sys.argv[0]} <url-do-repositorio> <diretorio-de-destino>")
    sys.exit(1)

def clone_repo(repo_url, dest_dir):
    try:
        subprocess.run(["git", "clone", repo_url, dest_dir], check=True)
    except subprocess.CalledProcessError:
        print("Falha ao clonar o repositório.")
        sys.exit(1)


def apply_git_config(dest_dir, user_name, user_email):
    config_path = os.path.join(dest_dir, '.git', 'config')
    if not os.path.isfile(config_path):
        print(f"Config Git não encontrado em {config_path}")
        sys.exit(1)
    with open(config_path, 'a', encoding='utf-8') as cfg:
        cfg.write(f"\n[user]\n")
        cfg.write(f"    name = {user_name}\n")
        cfg.write(f"    email = {user_email}\n")
    print(f"Configuração aplicada: name={user_name}, email={user_email}")


def main():
    if len(sys.argv) != 3:
        usage()

    repo_url = sys.argv[1]
    dest_dir = sys.argv[2]

    config = load_config()
    git_user_name = config.get('gitUserName')
    workspaces = config.get('workSpaces', [])

    if not git_user_name or not workspaces:
        print("Configuração incompleta: verifique 'gitUserName' e 'workSpaces' no config.json.")
        sys.exit(1)

    # Extrai host/base da URL
    parsed = urlparse(repo_url)
    host = parsed.netloc or parsed.path.split('/')[0]

    # Seleciona email com base no host
    git_email = None
    for ws in workspaces:
        if ws.get('urlBase') in host:
            git_email = ws.get('gitEmail')
            break

    clone_repo(repo_url, dest_dir)

    if git_email:
        apply_git_config(dest_dir, git_user_name, git_email)
    else:
        print(f"Nenhuma regra de email para host '{host}'. Clone sem configurar email.")

if __name__ == '__main__':
    main()
