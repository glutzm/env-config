#!/usr/bin/env python3
"""
git_mass_clone.py

Script para clonar ou atualizar em massa múltiplos repositórios definidos em um arquivo YAML
localizado no mesmo diretório do script. Integra-se com o comando `gitclone` (se disponível no PATH)
para aplicar configurações Git locais por cliente. Atualiza todas as branches remotas,
opcionalmente remove branches locais que foram removidas na origem, e gera um relatório
de status das branches.
"""
import os
import sys
import subprocess
import argparse
from typing import Any

import yaml
import json
import re
import shutil

# Variável global para armazenar o relatório de problemas
checkout_report = {}


def parse_args():
    parser = argparse.ArgumentParser(
        description=
        "Clona ou atualiza em massa repositórios definidos em repos.yaml (no diretório do script). "
        "Usa `gitclone` (se no PATH) para configuração por cliente.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--cliente",
        help="Nome(s) do(s) cliente(s) a processar (separados por vírgula). Processa todos se omitido."
    )
    parser.add_argument(
        "--delete-gone-branches",
        action="store_true",
        help="Remove automaticamente branches locais que foram removidas na origem (`git remote prune origin` já é executado)."
    )
    # O argumento do arquivo de configuração foi removido
    return parser.parse_args()


def load_config(filename="repos.yaml"):
    """Carrega a configuração do arquivo repos.yaml no diretório do script."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, filename)

    if not os.path.isfile(config_path):
        print(f"Erro: Arquivo de configuração padrão não encontrado: {config_path}")
        sys.exit(1)

    print(f"INFO: Carregando configuração de {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Erro ao ler o arquivo YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado ao carregar configuração: {e}")
        sys.exit(1)


def check_gitclone_command():
    """Verifica se o comando `gitclone` está disponível no PATH."""
    gitclone_path = shutil.which("gitclone")
    if gitclone_path:
        print(f"INFO: Comando `gitclone` encontrado em: {gitclone_path}")
        return "gitclone"  # Retorna o nome do comando para ser usado
    else:
        print("AVISO: Comando `gitclone` não encontrado no PATH.")
        print("Buscando script...")
        return find_gitclone_script()


def find_gitclone_script():
    """Encontra o caminho para o script clone_and_configure.py."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    gitclone_script_path = os.path.abspath(os.path.join(script_dir, '..', 'gitClone', 'clone_and_configure.py'))
    if not os.path.isfile(gitclone_script_path):
        print(f"AVISO: Script 'clone_and_configure.py' não encontrado em {os.path.dirname(gitclone_script_path)}")
        print("A configuração específica do cliente não será aplicada.")
        print("O clone será feito usando `git clone` padrão, sem configuração específica do cliente.")
        return None
    if not os.access(gitclone_script_path, os.X_OK):
        print(f"AVISO: Script '{gitclone_script_path}' não tem permissão de execução.")
        print("Tentando adicionar permissão de execução...")
        try:
            os.chmod(gitclone_script_path, 0o755)
            print("Permissão de execução adicionada.")
        except OSError as e:
            print(f"Erro ao adicionar permissão de execução: {e}")
            print("A configuração específica do cliente não será aplicada.")
            print("O clone será feito usando `git clone` padrão, sem configuração específica do cliente.")
            return None
    return gitclone_script_path


def filter_clientes(all_clientes, args):
    if not args.cliente:
        return all_clientes.items()
    else:
        selected_names = {c.strip() for c in args.cliente.split(',')}
        filtered = {}
        not_found = set()
        for name in selected_names:
            if name in all_clientes:
                filtered[name] = all_clientes[name]
            else:
                not_found.add(name)
        if not_found:
            print(
                f"Aviso: Cliente(s) não encontrado(s) no arquivo de configuração: {', '.join(sorted(list(not_found)))}")
        if not filtered:
            print("Nenhum dos clientes especificados foi encontrado. Saindo.")
            sys.exit(1)
        return filtered.items()


def _add_to_report(repo_identifier, type, branch_name):
    """Adiciona uma entrada ao relatório global."""
    if repo_identifier not in checkout_report:
        checkout_report[repo_identifier] = {}
    if type not in checkout_report[repo_identifier]:
        checkout_report[repo_identifier][type] = []
    if branch_name not in checkout_report[repo_identifier][type]:
        checkout_report[repo_identifier][type].append(branch_name)


def run_git_command(repo_dir, *args, check=False, suppress_stderr=False, ignore_errors=False):
    """Executa um comando git no diretório especificado."""
    command = ['git', '-C', repo_dir] + list(args)
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=check, encoding='utf-8')
        return result
    except FileNotFoundError:
        print("Erro: Comando 'git' não encontrado. Verifique se o Git está instalado e no PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if not suppress_stderr and not ignore_errors:
            print(f"Erro ao executar git {' '.join(args)} em {repo_dir}: {e.stderr.strip()}")
        return e
    except Exception as e:
        if not ignore_errors:
            print(f"Erro inesperado ao executar git {' '.join(args)} em {repo_dir}: {e}")
        # Retorna um objeto simulado com código de retorno diferente de zero
        return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr=str(e))


def _fetch_and_prune(repo_dir, repo_identifier):
    """Executa git fetch --prune e remote prune origin."""
    print(f"[{repo_identifier}] Executando fetch --prune e remote prune...")
    run_git_command(repo_dir, 'remote', 'prune', 'origin', ignore_errors=True)  # Ignora erro se origin não existir
    fetch_result = run_git_command(repo_dir, 'fetch', '--prune')
    if fetch_result.returncode != 0:
        print(f"[{repo_identifier}] Aviso: Falha ao executar 'git fetch --prune'. {fetch_result.stderr.strip()}")
        _add_to_report(repo_identifier, 'branches-com-falha', fetch_result.stderr.strip())
        return False
    return True


def _get_remote_branches(repo_dir, repo_identifier):
    """Obtém a lista de branches remotas (origin/*)."""
    remote_branches_result = run_git_command(repo_dir, 'branch', '-r')
    if remote_branches_result.returncode != 0:
        print(f"[{repo_identifier}] Erro: Não foi possível listar branches remotas.")
        return None

    remote_branches = set()
    for line in remote_branches_result.stdout.splitlines():
        line = line.strip()
        if line.startswith('origin/') and '->' not in line:
            branch_name = line.split('/', 1)[1]
            remote_branches.add(branch_name)
    return remote_branches


def _delete_branches(branches_to_delete, repo_dir, repo_identifier):
    print(
        f"[{repo_identifier}] Removendo branches locais (--delete-gone-branches ativo): {', '.join(branches_to_delete)}")
    for local_branch in branches_to_delete:
        # Verificar se não é a branch atual antes de deletar
        current_branch_result = run_git_command(repo_dir, 'rev-parse', '--abbrev-ref', 'HEAD')
        if current_branch_result.returncode == 0 and current_branch_result.stdout.strip() == local_branch:
            print(
                f"[{repo_identifier}] Aviso: Não é possível remover a branch atual '{local_branch}'. Mude para outra branch primeiro.")
            _add_to_report(repo_identifier, 'branches-com-falha', local_branch)
            continue

        delete_result = run_git_command(repo_dir, 'branch', '-d', local_branch)
        if delete_result.returncode != 0:
            print(f"[{repo_identifier}] Falha ao remover branch local '{local_branch}'. Tentando com -D...")
            delete_result_force = run_git_command(repo_dir, 'branch', '-D', local_branch)
            if delete_result_force.returncode != 0:
                print(
                    f"[{repo_identifier}] Erro ao forçar remoção da branch local '{local_branch}': {delete_result_force.stderr.strip()}")
                _add_to_report(repo_identifier, 'branches-com-falha', local_branch)


def _handle_gone_branches(repo_dir, repo_identifier, delete_gone_branches_flag):
    """Identifica e opcionalmente remove branches locais cujo upstream foi removido."""
    local_branches_result = run_git_command(repo_dir, 'branch', '-vv')
    if local_branches_result.returncode != 0:
        print(
            f"[{repo_identifier}] Aviso: Não foi possível executar 'git branch -vv'. Não foi possível verificar branches 'gone'.")
        return

    gone_branch_pattern = re.compile(r"^\*?\s+(\S+)\s+\S+\s+\[origin/(\S+): gone\]")
    branches_to_delete = []
    for line in local_branches_result.stdout.splitlines():
        match = gone_branch_pattern.search(line)
        if match:
            local_branch = match.group(1)
            remote_branch_name = match.group(2)
            print(
                f"[{repo_identifier}] Branch remota 'origin/{remote_branch_name}' (rastreada por '{local_branch}') foi removida.")
            _add_to_report(repo_identifier, 'branches-removidas', remote_branch_name)
            if delete_gone_branches_flag:
                branches_to_delete.append(local_branch)

    if branches_to_delete:
        _delete_branches(branches_to_delete, repo_dir, repo_identifier)


def _checkout_remote_branch(repo_dir, repo_identifier, branch):
    """Tenta fazer checkout de uma branch remota, criando-a localmente se necessário."""
    print(f"[{repo_identifier}] Verificando branch '{branch}'...")
    checkout_result = run_git_command(repo_dir, 'checkout', branch, suppress_stderr=True, ignore_errors=True)
    if checkout_result.returncode != 0:
        track_result = run_git_command(repo_dir, 'checkout', '--track', f'origin/{branch}', suppress_stderr=True)
        if track_result.returncode != 0:
            error_msg = track_result.stderr.strip() if hasattr(track_result, 'stderr') else "Erro desconhecido"
            print(f"[{repo_identifier}] Falha ao fazer checkout da branch '{branch}'. Erro: {error_msg}")
            _add_to_report(repo_identifier, 'branches-com-falha', branch)
            return False
    return True


def _return_to_original_branch(repo_dir, repo_identifier, original_branch):
    """Retorna para a branch original ou uma branch padrão (main/master)."""
    checkout_success = False
    if original_branch and original_branch != 'HEAD':
        print(f"[{repo_identifier}] Retornando para branch original '{original_branch}'...")
        result = run_git_command(repo_dir, 'checkout', original_branch, ignore_errors=True)
        if result.returncode == 0:
            checkout_success = True

    if not checkout_success:
        for default_branch in ('main', 'master'):
            print(f"[{repo_identifier}] Tentando retornar para branch padrão '{default_branch}'...")
            result = run_git_command(repo_dir, 'checkout', default_branch, ignore_errors=True)
            if result.returncode == 0:
                checkout_success = True
                print(f"[{repo_identifier}] Retornou para '{default_branch}'.")
                break

    if not checkout_success:
        print(f"[{repo_identifier}] Aviso: Não foi possível retornar para a branch original ou padrão.")


# --- Funções Refatoradas de clone_or_update ---

def update_repository_branches(repo_dir, repo_identifier, delete_gone_branches_flag):
    """Função principal que orquestra a atualização das branches e o relatório."""
    print(f"[{repo_identifier}] Atualizando branches...")

    current_branch_result = run_git_command(repo_dir, 'rev-parse', '--abbrev-ref', 'HEAD')
    original_branch = current_branch_result.stdout.strip() if current_branch_result.returncode == 0 else None

    if not _fetch_and_prune(repo_dir, repo_identifier):
        # Se o fetch falhar, ainda tenta retornar para a branch original
        _return_to_original_branch(repo_dir, repo_identifier, original_branch)
        return

    remote_branches = _get_remote_branches(repo_dir, repo_identifier)
    if remote_branches is None:
        _return_to_original_branch(repo_dir, repo_identifier, original_branch)
        return  # Não pode continuar sem a lista de branches

    _handle_gone_branches(repo_dir, repo_identifier, delete_gone_branches_flag)

    for branch in sorted(list(remote_branches)):
        if branch == 'HEAD': continue
        _checkout_remote_branch(repo_dir, repo_identifier, branch)

    _return_to_original_branch(repo_dir, repo_identifier, original_branch)


def _clone_repository(repo_url, dest_dir, client_name, gitclone_command, repo_identifier):
    """Clona o repositório usando gitclone ou git clone padrão."""
    print(f"[{repo_identifier}] Clonando {repo_url} em {dest_dir} para o cliente '{client_name}'...")

    # Garante que o diretório pai exista ANTES de tentar clonar
    parent_dir = os.path.dirname(dest_dir)
    if not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
            print(f"[{repo_identifier}] Diretório pai criado: {parent_dir}")
        except OSError as e:
            print(f"[{repo_identifier}] Erro ao criar diretório pai {parent_dir}: {e}")
            return False  # Não pode clonar sem o diretório pai

    clone_cmd_list: list[Any]
    if gitclone_command:
        clone_cmd_list = [gitclone_command, '-c', client_name, repo_url, dest_dir]
    else:
        clone_cmd_list = ['git', 'clone', repo_url, dest_dir]

    try:
        clone_result = subprocess.run(clone_cmd_list, capture_output=True, text=True, check=True, encoding='utf-8')
        print(f"[{repo_identifier}] Clone concluído. Saída: {clone_result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip()
        print(f"[{repo_identifier}] Erro ao clonar o repositório {repo_url}.")
        print(f"Comando: {' '.join(e.cmd)}")
        print(f"Erro: {error_output}")
        return False
    except FileNotFoundError:
        print(f"[{repo_identifier}] Erro: Comando '{clone_cmd_list[0]}' não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"[{repo_identifier}] Erro inesperado durante o clone: {e}")
        return False


def _update_repository(repo_dir, repo_identifier):
    """Atualiza um repositório existente (pull)."""
    print(f"[{repo_identifier}] Repositório já existe em {repo_dir}. Atualizando com pull...")
    pull_result = run_git_command(repo_dir, 'pull')
    if pull_result.returncode != 0:
        error_msg = pull_result.stderr.strip() if hasattr(pull_result, 'stderr') else "Erro desconhecido no pull"
        print(f"[{repo_identifier}] Aviso: Falha ao executar 'git pull'. {error_msg}")
        # Não adiciona ao relatório principal, pois a atualização de branches tentará de qualquer forma
        # _add_to_report(repo_identifier, 'branches-com-falha', f"Falha no pull: {error_msg}")
    return pull_result.returncode == 0


def process_repository(repo_url, dest_dir, client_name, gitclone_command, repo_identifier, delete_gone_branches_flag):
    """Orquestra o clone ou atualização e a verificação de branches para um repositório."""
    git_dir = os.path.join(dest_dir, '.git')
    repo_exists = os.path.isdir(git_dir)

    if repo_exists:
        _update_repository(repo_dir=dest_dir, repo_identifier=repo_identifier)
        # Sempre executa a verificação/atualização de todas as branches
        update_repository_branches(repo_dir=dest_dir, repo_identifier=repo_identifier,
                                   delete_gone_branches_flag=delete_gone_branches_flag)
    else:
        clone_successful = _clone_repository(repo_url, dest_dir, client_name, gitclone_command, repo_identifier)
        if clone_successful:
            # Executa a verificação/atualização de todas as branches após o clone inicial
            update_repository_branches(repo_dir=dest_dir, repo_identifier=repo_identifier,
                                       delete_gone_branches_flag=delete_gone_branches_flag)
        # Se o clone falhou, o erro já foi reportado em _clone_repository


def processar_repo_name(repo):
    repo_name = repo if isinstance(repo, str) else str(repo).strip()
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def build_repo_identifier(client_name, classe, nome_proj, grupo, repo_name):
    return f"{client_name}/{classe}/{nome_proj}/{grupo + '/' if grupo else ''}{repo_name}"


def process_repo_entry(base_url, dir_base, classe, nome_proj, grupo, repo_name, client_name, gitclone_command,
                       delete_gone_branches_flag):
    needs_slash = not base_url.endswith(('/', ':'))
    repo_url = base_url + ('/' if needs_slash else '') + repo_name
    repo_name_updated = processar_repo_name(repo_name)

    parts = [dir_base, classe, nome_proj]
    if grupo:
        parts.append(grupo)
    parts.append(repo_name_updated)
    dest = os.path.abspath(os.path.join(*parts))

    repo_identifier = build_repo_identifier(client_name, classe, nome_proj, grupo, repo_name_updated)

    process_repository(repo_url, dest, client_name, gitclone_command, repo_identifier, delete_gone_branches_flag)


def handle_repos_list(base_url, dir_base, classe, nome_proj, repos_list, client_name, gitclone_command,
                      delete_gone_branches_flag):
    for repo_name in repos_list:
        process_repo_entry(base_url, dir_base, classe, nome_proj, None, repo_name, client_name, gitclone_command,
                           delete_gone_branches_flag)


def handle_repos_dict(base_url, dir_base, classe, nome_proj, repos_dict, client_name, gitclone_command,
                      delete_gone_branches_flag):
    for grupo, lista in repos_dict.items():
        for repo in lista:
            process_repo_entry(base_url, dir_base, classe, nome_proj, grupo, repo, client_name, gitclone_command,
                               delete_gone_branches_flag)


def process_projeto(base_url, dir_base, projeto_data, client_name, gitclone_command, delete_gone_branches_flag):
    nome_proj = projeto_data.get('projeto')
    classe = projeto_data.get('classe')
    repos = projeto_data.get('repositorios')

    if not nome_proj or not classe or repos is None:
        print(
            f"Aviso: Definição de projeto inválida ou incompleta para cliente '{client_name}'. Pulando: {projeto_data}")
        return

    print(f"-- Processando Projeto: {classe}/{nome_proj} --")
    if isinstance(repos, list):
        handle_repos_list(base_url, dir_base, classe, nome_proj, repos, client_name, gitclone_command,
                          delete_gone_branches_flag)
    elif isinstance(repos, dict):
        handle_repos_dict(base_url, dir_base, classe, nome_proj, repos, client_name, gitclone_command,
                          delete_gone_branches_flag)
    else:
        print(
            f"Aviso: Formato de 'repositorios' desconhecido para o projeto '{nome_proj}' do cliente '{client_name}'. Pulando.")


def process_cliente(cliente_name, cliente_data, gitclone_command, delete_gone_branches_flag):
    print(f"=== Processando Cliente: {cliente_name} ===")
    url_base = cliente_data.get('urlBase')
    dir_base = cliente_data.get('diretorioBase')

    if not url_base or not dir_base:
        print(
            f"Erro: Configuração 'urlBase' ou 'diretorioBase' ausente para o cliente '{cliente_name}'. Pulando cliente.")
        return

    projetos = cliente_data.get('projetos', [])
    if not projetos:
        print(f"Aviso: Nenhum projeto listado para o cliente '{cliente_name}'.")
        return

    for projeto_data in projetos:
        process_projeto(url_base, dir_base, projeto_data, cliente_name, gitclone_command, delete_gone_branches_flag)


def _print_report():
    # Imprime o relatório final se houver algo a reportar
    if checkout_report:
        print("\n--- Relatório de Problemas no Checkout/Atualização de Branches ---")
        try:
            # Ordenar chaves do relatório para consistência
            sorted_report = {k: checkout_report[k] for k in sorted(checkout_report.keys())}
            # Ordenar listas dentro do relatório
            for repo_id in sorted_report:
                if 'branches-removidas' in sorted_report[repo_id]:
                    sorted_report[repo_id]['branches-removidas'].sort()
                if 'branches-com-falha' in sorted_report[repo_id]:
                    sorted_report[repo_id]['branches-com-falha'].sort()

            report_json = json.dumps(sorted_report, indent=4, ensure_ascii=False)
            print(report_json)
        except Exception as e:
            print(f"Erro ao formatar o relatório JSON: {e}")
            print("Dados brutos do relatório:", checkout_report)
        print("--- Fim do Relatório ---")
    else:
        print("\nProcessamento concluído. Nenhum problema reportado no checkout/atualização de branches.")


def main():
    args = parse_args()
    config_data = load_config()
    gitclone_command = check_gitclone_command()

    all_clientes_data = config_data.get('clientes', {})
    if not all_clientes_data:
        print("Erro: Nenhuma seção 'clientes' encontrada no arquivo de configuração.")
        sys.exit(1)

    clientes_para_processar = filter_clientes(all_clientes_data, args)

    if not clientes_para_processar:
        print("Nenhum cliente selecionado para processamento.")
        sys.exit(0)

    for cliente_name, cliente_data in clientes_para_processar:
        process_cliente(cliente_name, cliente_data, gitclone_command, args.delete_gone_branches)

    _print_report()


if __name__ == '__main__':
    main()
