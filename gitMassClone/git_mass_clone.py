#!/usr/bin/env python3
"""
git_mass_clone.py

Script para clonar em massa múltiplos repositórios definidos em um arquivo YAML.
Utiliza o alias 'gitclone' (apontando para 'clone_and_configure.py') para executar
cada clone com configurações de usuário.
"""
import os
import sys
import subprocess
import argparse
import yaml


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clona em massa repositórios definidos em um arquivo YAML.'
    )
    parser.add_argument('config_file', help='Caminho para o arquivo YAML de configuração')
    return parser.parse_args()


def load_config(path):
    if not os.path.isfile(path):
        print(f"Arquivo não encontrado: {path}")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Erro ao ler YAML: {e}")
            sys.exit(1)


def gitclone(repo_url, dest_dir):
    print(f"Clonando {repo_url} em {dest_dir}")
    os.makedirs(dest_dir, exist_ok=True)
    ret = subprocess.run(['gitclone', repo_url, dest_dir])
    if ret.returncode != 0:
        print(f"Erro ao clonar {repo_url}")


def handle_repos_list(base_url, dir_base, classe, nome_proj, repos_list):
    for repo_name in repos_list:
        url = base_url + repo_name
        dest = os.path.join(dir_base, classe, nome_proj, repo_name)
        gitclone(url, dest)


def handle_repos_dict(base_url, dir_base, classe, nome_proj, repos_dict):
    for grupo, lista in repos_dict.items():
        for repo_name in lista:
            url = base_url + repo_name
            dest = os.path.join(dir_base, classe, nome_proj, grupo, repo_name)
            gitclone(url, dest)


def process_projeto(base_url, dir_base, projeto):
    nome_proj = projeto.get('projeto')
    classe = projeto.get('classe')
    repos = projeto.get('repositorios')
    if not nome_proj or not classe or repos is None:
        print(f"Projeto inválido ou incompleto: {projeto}")
        return

    if isinstance(repos, list):
        handle_repos_list(base_url, dir_base, classe, nome_proj, repos)
    elif isinstance(repos, dict):
        handle_repos_dict(base_url, dir_base, classe, nome_proj, repos)
    else:
        print(f"Formato de repositórios desconhecido para {nome_proj}")


def process_cliente(cliente_name, data):
    url_base = data.get('urlBase', '').rstrip('/') + '/'
    dir_base = data.get('diretorioBase')
    if not url_base or not dir_base:
        print(f"Configuração incompleta para {cliente_name}, pulando.")
        return

    projetos = data.get('projetos', [])
    for projeto in projetos:
        process_projeto(url_base, dir_base, projeto)


def main():
    args = parse_args()
    cfg = load_config(args.config_file)

    clientes = cfg.get('clientes', {})
    if not clientes:
        print("Nenhum cliente definido no arquivo de configuração.")
        sys.exit(1)

    for cliente, data in clientes.items():
        process_cliente(cliente, data)

if __name__ == '__main__':
    main()
