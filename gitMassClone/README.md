# git_mass_clone

Um script Python para clonar em massa repositórios definidos em um arquivo YAML. Usa o alias
`gitclone` (que deve apontar para o seu `clone_and_configure.py`) para aplicar configurações
de usuário Git automaticamente.

## Instalação

1. Clone ou baixe este repositório.
2. Instale dependência:
   ```bash
   pip install pyyaml
   ```
3. Certifique-se de que o alias `gitclone` (ou um executável equivalente) esteja disponível no PATH.
4. Torne o script executável:
   ```bash
   chmod +x git_mass_clone.py
   ```

## Configuração (repos.yaml)

Exemplo de estrutura:

```yaml
clientes:
  cliente1:
    urlBase: https://url.repo.cliente1/
    diretorioBase: /caminho/ate/cliente1/repositories
    projetos:
      - projeto: nomeProjeto1
        classe: nomeGrupo1
        repositorios:
          conjuntoMicroServico1:
            - projeto1-git-servico1
            - projeto1-git-servico2
          conjuntoMicroServico2:
            - projeto1-git-servico3
      - projeto: nomeProjeto2
        classe: nomeGrupo1
        repositorios:
          - projeto2-git-servico1
  cliente2:
    urlBase: git@url.repo.cliente2:grupo/
    diretorioBase: /caminho/ate/cliente2/repositories
    projetos:
      - projeto: nomeProjeto1
        classe: nomeGrupo3
        repositorios:
          - projeto1-git-servico1.git
```

- **clientes**: mapeamento de cliente para dados.
- **urlBase**: URL base de clone (HTTPS ou SSH), sempre finalizada em `/`.
- **diretorioBase**: pasta onde serão criadas subpastas.
- **projetos**: lista de projetos, cada um com:
  - **projeto**: nome do projeto.
  - **classe**: agrupamento (pasta intermediária).
  - **repositorios**: pode ser lista simples (array) ou dicionário de grupos.

## Uso

```bash
./git_mass_clone.py repos.yaml
```

Cada repositório será clonado usando:

```bash
gitclone <urlBase + nomeRepo> <diretorioBase>/<classe>/<projeto>[/<grupo>]/<nomeRepo>
```

As pastas intermediárias serão criadas automaticamente.