# clone_and_configure.py

Este script em Python clona um repositório Git e, opcionalmente, aplica configurações
locais de nome e email de usuário com base em um cliente especificado via linha de comando.
O objetivo é facilitar a configuração correta da identidade Git para diferentes contextos
(clientes, projetos pessoais, etc.) sem interferir na configuração global.

## Pré-requisitos

- Python 3.6+ instalado
- Git disponível no PATH
- Arquivo `config.json` na mesma pasta do script (necessário apenas se for usar a funcionalidade de cliente)

## Estrutura do `config.json`

Crie um arquivo chamado `config.json` no mesmo diretório do script `clone_and_configure.py`.
A estrutura esperada para este arquivo é a seguinte:

```json
{
	"gitUserName": "Seu Nome de Usuário Git",
	"clientes": {
		"nome_cliente_1": {
			"gitEmail": "email_cliente_1@example.com"
		},
		"nome_cliente_2": {
			"gitEmail": "email_cliente_2@example.com"
		},
		"pessoal": {
			"gitEmail": "seu_email_pessoal@example.com"
		}
	}
}
```

- `gitUserName`: O nome de usuário Git que será configurado localmente no repositório clonado quando um cliente for especificado.
- `clientes`: Um objeto JSON onde cada chave é um identificador único para um cliente ou contexto (ex: "cliente1", "empresaX", "pessoal").
  - Cada objeto de cliente deve conter a chave `gitEmail` com o endereço de email correspondente a ser usado para aquele contexto.

## Tornando o script executável e acessível (Opcional)

Para facilitar o uso, você pode tornar o script executável e criar um link simbólico para ele em um diretório que 
esteja no seu PATH.

1.  **Dê permissão de execução:**
    ```bash
    chmod +x /caminho/completo/para/clone_and_configure.py
    ```

2.  **Crie um link simbólico (exemplo usando `/usr/local/bin`):**
    ```bash
    sudo ln -s /caminho/completo/para/clone_and_configure.py /usr/local/bin/gitclone
    ```
    *Substitua `/caminho/completo/para/` pelo caminho real onde o script está localizado.*

3.  **Verifique se o link foi criado e está acessível:**
    ```bash
    which gitclone
    ```

Após esses passos, você poderá chamar o script usando apenas `gitclone` em vez do caminho completo.

## Uso

O script aceita os seguintes argumentos:

```bash
python clone_and_configure.py [opções] <url-do-repositorio> <diretorio-de-destino>
# Ou, se você criou o link simbólico:
gitclone [opções] <url-do-repositorio> <diretorio-de-destino>
```

**Argumentos Obrigatórios:**

- `<url-do-repositorio>`: A URL do repositório Git que você deseja clonar (ex: `https://github.com/usuario/projeto.git`).
- `<diretorio-de-destino>`: O caminho da pasta local onde o repositório será clonado (ex: `~/projetos/meu-projeto`).

**Opções:**

- `-c NOME_CLIENTE`, `--cliente NOME_CLIENTE`: Especifica o nome do cliente (a chave usada no objeto `clientes` dentro do `config.json`). Se esta opção for usada, o script tentará carregar o `config.json`, encontrar o cliente e aplicar o `gitUserName` e o `gitEmail` correspondente nas configurações locais do repositório clonado (`.git/config`).

### Exemplos

**1. Clonar e configurar para "cliente1" (usando o link `gitclone`):**

Supondo que seu `config.json` contenha:
```json
{
  "gitUserName": "Gustavo L.",
  "clientes": {
    "cliente1": { "gitEmail": "gustavo.cliente1@exemplo.com" }
  }
}
```

Comando:
```bash
gitclone --cliente cliente1 https://github.com/cliente1/projeto-secreto.git /home/gustavo/projetos/cliente1/projeto-secreto
```
Resultado: O repositório será clonado em `/home/gustavo/projetos/cliente1/projeto-secreto`, e o arquivo `.git/config` 
dentro dele terá as seguintes configurações locais:
```ini
[user]
    name = Gustavo L.
    email = gustavo.cliente1@exemplo.com
```

**2. Clonar sem especificar um cliente (usando python diretamente):**

Comando:
```bash
python /caminho/para/clone_and_configure.py https://github.com/usuario/projeto-publico.git ~/dev/projeto-publico
```
Resultado: O repositório será clonado em `~/dev/projeto-publico`. Nenhuma configuração local de `user.name` ou 
`user.email` será aplicada pelo script. O Git usará as configurações globais ou do sistema, se existirem.

**3. Tentativa de clonar com cliente inexistente:**

Comando:
```bash
gitclone -c cliente_fantasma https://gitlab.com/outro/repo.git /tmp/repo
```
Resultado: O script clonará o repositório, mas depois exibirá uma mensagem de erro informando que o cliente "cliente_fantasma" não foi encontrado no `config.json`, e a configuração local não será aplicada.

## Detalhes de Funcionamento

1.  O script parseia os argumentos da linha de comando (`--cliente`, `url-do-repositorio`, `diretorio-de-destino`).
2.  Executa o comando `git clone` para baixar o repositório para o diretório de destino especificado.
3.  Se o argumento `--cliente` foi fornecido:
    a.  Tenta carregar e parsear o arquivo `config.json` localizado no mesmo diretório do script.
    b.  Busca pelo `gitUserName` global e pelas informações do cliente especificado (principalmente `gitEmail`) dentro da estrutura `clientes`.
    c.  Se encontrar ambos, executa os comandos `git config --local user.name "Nome Do Usuário"` e `git config --local user.email "email@exemplo.com"` dentro do diretório do repositório clonado para definir as configurações locais.
    d.  Se o `config.json` não for encontrado, for inválido, ou o cliente/email não for encontrado, exibe uma mensagem de erro apropriada.
4.  Se o argumento `--cliente` não foi fornecido, o script informa que o clone foi realizado sem aplicar configurações locais.

