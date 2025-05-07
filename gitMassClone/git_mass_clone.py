#!/usr/bin/env python3
"""
git_mass_clone.py

Script para clonar em massa múltiplos repositórios definidos em um arquivo YAML.
Permite filtrar quais clientes do arquivo serão processados.
Utiliza o alias `gitclone` para executar cada clone com configurações de usuário.
Após o clone, faz checkout de todas as branches remotas e retorna à branch principal.
Em repositórios já clonados, faz pull na branch corrente.
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
    parser.add_argument('--all', action='store_true', help='Processar todos os clientes')
    parser.add_argument('--cliente', help='Nome(s) de cliente(s) separados por vírgula')
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


def run_git_command(repo_dir, *args):
    result = subprocess.run(['git', '-C', repo_dir] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro no git {' '.join(args)} em {repo_dir}: {result.stderr.strip()}")
    return result


def clone_or_update(repo_url, dest_dir):
    git_dir = os.path.join(dest_dir, '.git')
    if os.path.isdir(git_dir):
        print(f"Repositório já existe em {dest_dir}, executando pull...")
        run_git_command(dest_dir, 'pull')
    else:
        print(f"Clonando {repo_url} em {dest_dir}")
        os.makedirs(dest_dir, exist_ok=True)
        subprocess.run(['gitclone', repo_url, dest_dir])
        checkout_all_branches(dest_dir)


def checkout_all_branches(dest_dir):
    result = run_git_command(dest_dir, 'branch', '-r')
    if result.returncode != 0:
        return
    branches = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith('origin/') and '->' not in line:
            _, _, branch = line.partition('origin/')
            branches.append(branch)
    for branch in branches:
        if branch == 'HEAD':
            continue
        print(f"Fazendo checkout da branch {branch} em {dest_dir}")
        run_git_command(dest_dir, 'checkout', branch) or \
            run_git_command(dest_dir, 'checkout', '--track', f'origin/{branch}')
    for default in ('main', 'master'):
        result = run_git_command(dest_dir, 'checkout', default)
        if result.returncode == 0:
            print(f"Retornado para branch {default} em {dest_dir}")
            break


def handle_repos_list(base_url, dir_base, classe, nome_proj, repos_list):
    for repo_name in repos_list:
        process_repo_entry(base_url, dir_base, classe, nome_proj, None, repo_name)


def handle_repos_dict(base_url, dir_base, classe, nome_proj, repos_dict):
    for grupo, lista in repos_dict.items():
        for repo_name in lista:
            process_repo_entry(base_url, dir_base, classe, nome_proj, grupo, repo_name)


def process_repo_entry(base_url, dir_base, classe, nome_proj, grupo, repo_name):
    repo_url = base_url + repo_name
    parts = [dir_base, classe, nome_proj]
    if grupo:
        parts.append(grupo)
    parts.append(repo_name)
    dest = os.path.join(*parts)
    clone_or_update(repo_url, dest)


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


def filter_clientes(clientes, args):
    if args.all or not args.cliente:
        return clientes.items()
    names = [c.strip() for c in args.cliente.split(',')]
    return [(name, clientes[name]) for name in names if name in clientes]


def main():
    args = parse_args()
    cfg = load_config(args.config_file)

    clientes = cfg.get('clientes', {})
    if not clientes:
        print("Nenhum cliente definido no arquivo de configuração.")
        sys.exit(1)

    for cliente_name, data in filter_clientes(clientes, args):
        process_cliente(cliente_name, data)

if __name__ == '__main__':
    main()
