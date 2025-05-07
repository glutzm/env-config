#!/usr/bin/env python3
"""
git_mass_clone.py

Script para clonar em massa múltiplos repositórios definidos em um arquivo YAML.
Utiliza o alias 'gitclone' (apontando para 'clone_and_configure.py') para executar
cada clone com configurações de usuário.

Requisitos:
    pip install pyyaml
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
    # utiliza alias `gitclone`
    print(f"Clonando {repo_url} em {dest_dir}")
    os.makedirs(dest_dir, exist_ok=True)
    ret = subprocess.run(['gitclone', repo_url, dest_dir])
    if ret.returncode != 0:
        print(f"Erro ao clonar {repo_url}")


def main():
    args = parse_args()
    cfg = load_config(args.config_file)

    clientes = cfg.get('clientes', {})
    for cliente, data in clientes.items():
        url_base = data.get('urlBase', '').rstrip('/') + '/'
        dir_base = data.get('diretorioBase')
        if not url_base or not dir_base:
            print(f"Configuração incompleta para {cliente}, pulando.")
            continue

        projetos = data.get('projetos', [])
        for proj in projetos:
            nome_proj = proj.get('projeto')
            classe = proj.get('classe')
            repos = proj.get('repositorios', {})

            # caso repositorios seja lista simples
            if isinstance(repos, list):
                for repo_name in repos:
                    repo_url = url_base + repo_name
                    dest = os.path.join(dir_base, classe, nome_proj, repo_name)
                    gitclone(repo_url, dest)

            # caso seja dict de grupos
            elif isinstance(repos, dict):
                for grupo, lista in repos.items():
                    for repo_name in lista:
                        repo_url = url_base + repo_name
                        dest = os.path.join(dir_base, classe, nome_proj, grupo, repo_name)
                        gitclone(repo_url, dest)

            else:
                print(f"Formato de repositórios inválido em projeto {nome_proj}")

if __name__ == '__main__':
    main()
