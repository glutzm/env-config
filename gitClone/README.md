# clone_and_configure.py

Este script em Python clona um repositório Git e aplica configurações
locais de nome e email de usuário com base na URL base informada para
não conflitar com configuração global. A intenção é permitir trabalhar
em múltiplos repositórios sem conflitar identificação de usuário.

## Pré-requisitos

- Python 3.6+ instalado
- Git disponível no PATH
- Arquivo `config.json` na mesma pasta do script

## Crie o arquivo config.json

Exemplo de conteúdo de `config.json` em [config-example.json](config-example.json):
```json
{
  "gitUserName": "Nome Do Usuário",
  "workSpaces": [
    {
      "urlBase": "github.com",
      "gitEmail": "email@example.com"
    },
    {
      "urlBase": "gitlab.com",
      "gitEmail": "email@example2.com"
    }
  ]
}
```

- `gitUserName`: nome comum a todos os repositórios
- `workSpaces`: lista de objetos com:
  - `urlBase`: parte da URL para identificar o workspace
  - `gitEmail`: email a ser aplicado quando a URL contém `urlBase`


## Torne o script executável

```bash
chmod +x clone_and_configure.py
sudo ln -s /caminho/ate/env-config/gitClone/clone_and_configure.py /usr/local/bin/gitclone
which gitclone
```

## Uso

```bash
./clone_and_configure.py <url-do-repositorio> <diretorio-de-destino>
```

### Exemplos

- Clonar de GitHub e configurar email:
  ```bash
  ./clone_and_configure.py \
    https://github.com/usuario/projeto.git \
    ~/projetos/projeto
  ```
  Como `urlBase` contém `github.com`, será usado o `gitEmail` definido para GitHub.

- Clonar de GitLab sem regra:
  ```bash
  ./clone_and_configure.py \
    https://bitbucket.org/usuario/outro.git \
    /dados/outro
  ```
  Se não houver correspondência em `workSpaces`, o repositório é clonado sem alterar o email.

## Detalhes de funcionamento

1. Lê `config.json`.
2. Extrai o host/base da URL do repositório.
3. Busca em `workSpaces` um `urlBase` contido no host.
4. Clona o repositório via `git clone`.
5. Se encontrou `gitEmail`, anexa seção `[user]` no `.git/config` local.