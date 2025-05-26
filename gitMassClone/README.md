# git_mass_clone.py

Script Python para clonar ou atualizar em massa repositórios Git definidos em um arquivo `repos.yaml` localizado no mesmo diretório do script. Este script foi projetado para simplificar a gestão de múltiplos repositórios de diferentes clientes ou projetos.

**Principais Funcionalidades:**

*   **Configuração Centralizada:** Define todos os repositórios, suas URLs base e estruturas de diretório em um único arquivo `repos.yaml`.
*   **Integração com `gitclone`:** Se o comando `gitclone` (o script `clone_and_configure.py` tornado executável e adicionado ao PATH) estiver disponível, ele será utilizado para clonar novos repositórios. Isso permite aplicar configurações locais de usuário (nome e email) específicas para cada cliente, conforme definido no `config.json` do `gitclone`.
*   **Atualização Abrangente:** Para cada repositório (novo ou existente):
    *   Executa `git fetch --prune` e `git remote prune origin` para sincronizar com o estado remoto.
    *   Verifica branches locais que rastreiam branches remotas removidas (`gone`).
    *   Opcionalmente (via flag `--delete-gone-branches`), remove essas branches locais "órfãs".
    *   Tenta fazer checkout de todas as branches remotas existentes para garantir que o workspace local esteja completo, criando branches locais de rastreamento (`--track`) se necessário.
    *   Retorna para a branch original ou uma padrão (`main`/`master`).
*   **Relatório Detalhado:** Gera um relatório em JSON ao final da execução, listando quaisquer branches remotas que foram detectadas como removidas (`branches-removidas`) ou branches que apresentaram falha durante o processo de checkout/atualização (`branches-com-falha`).
*   **Estrutura de Diretórios Organizada:** Clona os repositórios em uma estrutura de pastas definida no `repos.yaml` (`{diretorioBase}/{classe}/{projeto}/{subgrupo_se_existir}/{nome_repositorio}`).

## Pré-requisitos

*   Python 3.6+ instalado.
*   Git disponível no PATH do sistema.
*   Biblioteca PyYAML instalada (`pip install pyyaml` ou `sudo apt install python3-yaml`).
*   **Opcional, mas recomendado:** O comando `gitclone` (script `clone_and_configure.py` do diretório `gitClone`) deve estar executável e disponível no PATH do sistema para que a configuração de usuário/email por cliente seja aplicada automaticamente durante o clone inicial. Se `gitclone` não for encontrado, o script usará o `git clone` padrão.

## Arquivo de Configuração (`repos.yaml`)

Crie um arquivo chamado `repos.yaml` **no mesmo diretório** onde o script `git_mass_clone.py` está localizado. A estrutura esperada é a seguinte:

```yaml
---
clientes:
  nome_cliente_1: # Identificador único do cliente
    urlBase: https://servidor.git.cliente1.com/ # URL base para os repositórios (HTTPS ou SSH)
    diretorioBase: /home/usuario/projetos/cliente1 # Diretório raiz onde os repositórios deste cliente serão clonados
    projetos:
      - projeto: NomeDoProjetoA # Nome do projeto (usado na estrutura de diretórios)
        classe: Backend # Agrupador/Categoria (usado na estrutura de diretórios)
        repositorios: # Lista ou Dicionário de repositórios
          # Opção 1: Lista simples de nomes de repositórios
          - repo-api
          - repo-servico-interno.git # Extensão .git é opcional, será tratada
          # Opção 2: Dicionário para subgrupos (ex: microserviços)
          # conjuntoMicroServico1:
          #   - ms-autenticacao
          #   - ms-usuarios
      - projeto: NomeDoProjetoB
        classe: Frontend
        repositorios:
          - repo-interface-web

  nome_cliente_2:
    urlBase: git@servidor.git.cliente2.com:grupo/ # Exemplo com SSH
    diretorioBase: /dados/work/cliente2
    projetos:
      - projeto: FerramentasInternas
        classe: Infra
        repositorios:
          - ferramenta-deploy
          - scripts-automacao.git
```

**Campos:**

*   `clientes`: Chave raiz contendo um objeto para cada cliente.
*   `nome_cliente_X`: Identificador único para cada cliente. **Este nome será passado para o comando `gitclone` via argumento `-c` durante o clone inicial, se `gitclone` estiver disponível.** Certifique-se de que este nome exista no `config.json` do `gitclone`.
*   `urlBase`: A URL base para construir a URL completa de clone.
*   `diretorioBase`: O caminho absoluto do diretório onde a estrutura de pastas do cliente será criada.
*   `projetos`: Uma lista de projetos para o cliente.
*   `projeto`: Nome descritivo do projeto.
*   `classe`: Categoria ou grupo do projeto.
*   `repositorios`: Pode ser uma lista de nomes de repositórios ou um dicionário de subgrupos contendo listas de nomes de repositórios.

A estrutura final do diretório será: `{diretorioBase}/{classe}/{projeto}/{subgrupo_se_existir}/{nome_repositorio}`.

## Tornando o script executável e acessível (Opcional)

Para facilitar o uso, você pode tornar o script executável e, opcionalmente, criar um link simbólico em um diretório do seu PATH:

1.  **Permissão de execução:**
    ```bash
    chmod +x /caminho/completo/para/git_mass_clone.py
    ```
2.  **Link simbólico (exemplo):**
    ```bash
    # Exemplo: Criar um link chamado 'git-mass-clone' em /usr/local/bin
    sudo ln -s /caminho/completo/para/git_mass_clone.py /usr/local/bin/git-mass-clone
    ```
3.  **Verificação:**
    ```bash
    which git-mass-clone
    ```

## Uso

Execute o script a partir do seu diretório. Ele automaticamente procurará por `repos.yaml` nesse mesmo diretório.

```bash
# Navegue até o diretório onde git_mass_clone.py e repos.yaml estão
cd /caminho/para/env-config/gitMassClone

# Execute o script
python git_mass_clone.py [opções]

# Ou, se você criou o link simbólico:
git-mass-clone [opções]
```

**Opções:**

- `--cliente <nomes>`: (Opcional) Uma lista separada por vírgulas dos nomes dos clientes (exatamente como definidos no `repos.yaml`) que devem ser processados. Se omitido, **todos** os clientes no `repos.yaml` serão processados.
- `--delete-gone-branches`: (Opcional) Se esta flag for incluída, o script tentará remover automaticamente as branches locais que foram identificadas como "gone" (removidas na origem) após a execução de `git fetch --prune`. **O comportamento padrão (sem a flag) é apenas reportar essas branches na seção `branches-removidas` do relatório final, sem excluí-las localmente.**

### Exemplos

**1. Processar todos os clientes definidos em `repos.yaml` (comportamento padrão):**

```bash
python git_mass_clone.py
# ou
git-mass-clone
```

**2. Processar apenas `cliente1` e `empresaX`:**

```bash
python git_mass_clone.py --cliente cliente1,empresaX
# ou
git-mass-clone --cliente cliente1,empresaX
```

**3. Processar todos os clientes e remover branches locais "gone":**

```bash
python git_mass_clone.py --delete-gone-branches
# ou
git-mass-clone --delete-gone-branches
```

**4. Processar apenas `cliente_dev` e remover branches locais "gone":**

```bash
python git_mass_clone.py --cliente cliente_dev --delete-gone-branches
# ou
git-mass-clone --cliente cliente_dev --delete-gone-branches
```

## Funcionamento Detalhado

1.  **Parse Argumentos:** Lê as opções da linha de comando (`--cliente`, `--delete-gone-branches`).
2.  **Carrega Config:** Lê e parseia o arquivo `repos.yaml` do diretório atual do script.
3.  **Verifica `gitclone`:** Checa se o comando `gitclone` está no PATH.
4.  **Filtra Clientes:** Seleciona os clientes a serem processados com base no argumento `--cliente` (ou todos, se omitido).
5.  **Itera Clientes/Projetos/Repositórios:** Para cada repositório selecionado:  
    a. **Monta URL e Destino:** Constrói a URL completa e o caminho local.  
    b. **Verifica Existência:** Checa se `destino/.git` existe.  
    c. **Clone ou Update:**  
        - **Se não existe:** Tenta clonar usando `gitclone -c <cliente> ...` (se disponível) ou `git clone ...` (fallback).  
        - **Se já existe:** Executa `git pull` na branch atual.  
    d. **Atualiza Branches (Sempre):** Após clone ou pull, executa a rotina de atualização:  
        i.  `git remote prune origin` e `git fetch --prune`.  
        ii. Lista branches remotas (`git branch -r`).  
        iii. Verifica branches locais "gone" (`git branch -vv`). Registra no relatório (`branches-removidas`). Se `--delete-gone-branches` estiver ativo, tenta remover a branch local (`git branch -d` ou `-D`).  
        iv. Tenta fazer `git checkout` de cada branch remota existente. Se falhar, tenta `git checkout --track origin/<branch>`. Registra falhas no relatório (`branches-com-falha`).  
        v. Retorna para a branch original ou uma padrão (`main`, `master`).  
6.  **Relatório Final:** Ao final, se houverem sido registradas branches removidas ou com falha, imprime um relatório consolidado em formato JSON.

## Formato do Relatório JSON

Se forem encontrados problemas, um relatório JSON será impresso no final. O formato é:

```json
{
    "identificador_repo_1": {
        "branches-removidas": [
            "nome_branch_removida_1" 
        ],
        "branches-com-falha": [
            "nome_branch_falha_checkout"
        ]
    },
    "identificador_repo_2": {
        "branches-removidas": [
            "old-feature"
        ]
    }
}
```

- **Chaves Principais:** Identificador único do repositório (`{cliente}/{classe}/{projeto}/{subgrupo_se_existir}/{nome_repositorio}`).
- `branches-removidas`: Lista de nomes de branches remotas que foram detectadas como removidas na origem, mas ainda podem ter uma branch local associada (a menos que `--delete-gone-branches` tenha sido usado).
- `branches-com-falha`: Lista de nomes de branches que falharam no checkout/track, ou mensagens de erro gerais (falha no clone, falha ao remover branch local, etc.).

Este relatório ajuda a identificar repositórios que podem precisar de intervenção manual.

