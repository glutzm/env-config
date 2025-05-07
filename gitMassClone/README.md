# git_mass_clone

Script Python para clonar em massa repositórios definidos em um arquivo YAML, com opção de
filtrar clientes por parâmetro.

## Instalação (escolha entre um ou outro)
1. Criar um Virtual Environment e usar pip dentro dele
    ```bash
    sudo apt install python3-venv python3-pip   # se necessário
    python3 -m venv .venv
    source .venv/bin/activate
    pip install pyyaml
    chmod +x git_mass_clone.py
    ```

2. Instalar o PyYAML via APT (recomendado para uso em system-wide)
    ```bash
    sudo apt update
    sudo apt install python3-yaml
    chmod +x git_mass_clone.py
    ```
Adicione o script como um programa executável
```bash
sudo ln -s /caminho/ate/env-config/gitClone/git_mass_clone.py /usr/local/bin/git-mass-clone
which gitclone
```
## Crie o arquivo repos.yaml

Exemplo de conteúdo de `repos.yaml` em [repos-example.yaml](repos-example.yaml):
```yaml
clientes:
  cliente1:
    urlBase: https://url.repo.cliente1/
    diretorioBase: /caminho/cliente1/repositorios
    projetos:
      - projeto: nomeProjeto1
        classe: grupo1
        repositorios:
          - repoA
          - repoB
```

## Uso

- Clonar todos os clientes (padrão ou `--all`):
  ```bash
  ./git_mass_clone.py repos.yaml
  ./git_mass_clone.py repos.yaml --all
  ```

- Clonar um ou mais clientes:
  ```bash
  ./git_mass_clone.py repos.yaml --cliente=cliente1
  ./git_mass_clone.py repos.yaml --cliente=cliente1,cliente2
  ```

O script irá processar apenas os clientes selecionados.