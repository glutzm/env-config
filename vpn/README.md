# vpnctl

Script para alternar entre múltiplas conexões [NetExtender](https://www.sonicwall.com/) e
o [Tailscale](https://tailscale.com/), garantindo que apenas uma conexão fique ativa por vez.

## Por que existe

Se você usa NetExtender para se conectar a redes de trabalho/clientes e Tailscale para outros fins (ex: acesso pessoal),
em momentos diferentes no mesmo computador, este script evita o incômodo de lembrar manualmente de derrubar uma conexão
antes de subir a outra — e pergunta antes de fazer a troca, para você não perder uma sessão ativa sem querer.

## Requisitos

- `nxcli` / `netExtender` v10.3.0 (21)+ (SonicWall NetExtender CLI) instalado e com os perfis de conexão já configurados
- `tailscale` 1.102.4+ instalado
- Bash 4+

## Instalação

1. Clone o repositório em um local de sua preferência:
   ```bash
   git clone <url-do-repositorio> ~/personal-projects/vpnctl
   cd ~/personal-projects/vpnctl
   ```

2. Dê permissão de execução ao script:
   ```bash
   chmod +x vpnctl.sh
   ```

3. Crie um link simbólico em `/usr/local/bin` (requer sudo, mas o script em si continua rodando com as permissões do seu
   usuário — o `sudo` só afeta a criação do link):
   ```bash
   sudo ln -s "$(pwd)/vpnctl.sh" /usr/local/bin/vpnctl
   ```
   A partir daqui, o comando `vpnctl` fica disponível em qualquer diretório, para qualquer usuário do sistema — sem
   precisar do caminho completo.

4. Configure suas conexões (veja a seção seguinte).

## Configuração

O script não guarda nenhum dado sensível (nome de conexão, servidor) no código-fonte — tudo vem de um arquivo de
configuração local, que **não deve** ser versionado.

1. Copie o arquivo de exemplo:
   ```bash
   mkdir -p ~/.config/vpnctl
   cp vpnctl.conf.example ~/.config/vpnctl/vpnctl.conf
   ```

2. Edite `~/.config/vpnctl/vpnctl.conf` com os dados reais das suas conexões:
   ```bash
   NE1_CLIENT_NAME="cliente-1"
   NE1_CONNECTION_NAME="nome-da-conexao-1"
   NE1_SERVER_PATTERN="servidor1.exemplo.com"

   NE2_CLIENT_NAME="cliente-2"
   NE2_CONNECTION_NAME="nome-da-conexao-2"
   NE2_SERVER_PATTERN="servidor2.exemplo.com"
   ```

   `NE*_SERVER_PATTERN` é usado para identificar, a partir da saída de `nxcli status`, qual das duas conexões está ativa
   no momento. Para descobrir o valor certo, conecte-se manualmente a cada VPN e rode `nxcli status` — copie o trecho da
   linha "Server" (host ou IP) que aparece.

3. (Opcional) Use um caminho de configuração diferente definindo a variável de ambiente `VPNCTL_CONFIG` antes de chamar
   o script:
   ```bash
   export VPNCTL_CONFIG="$HOME/algum-outro-lugar/vpnctl.conf"
   ```

O arquivo `vpnctl.conf` real fica de fora do git graças ao `.gitignore` incluído no repositório.

## Uso

```bash
vpnctl <ação> [--yes]
```

| Ação       | Efeito                                          |
|------------|-------------------------------------------------|
| `ne1-up`   | Conecta à Conexão 1 do NetExtender              |
| `ne1-down` | Desconecta do NetExtender                       |
| `ne2-up`   | Conecta à Conexão 2 do NetExtender              |
| `ne2-down` | Desconecta do NetExtender                       |
| `ts-up`    | Conecta ao Tailscale (`sudo tailscale up`)      |
| `ts-down`  | Desconecta do Tailscale (`sudo tailscale down`) |

Se você tentar subir uma conexão enquanto outra já está ativa, o script pergunta interativamente se deve desconectá-la
antes de prosseguir. Responder qualquer coisa diferente de `s`/`sim` aborta a operação sem mexer em nada.

### Flag `--yes`

Pula a pergunta interativa e desconecta a outra VPN automaticamente. Pensado para uso em contextos não-interativos, como
cron — onde não existe ninguém para responder ao prompt (e o script aborta por segurança se detectar que não há terminal
disponível e `--yes` não foi passado).

```bash
vpnctl ts-up --yes
```

## Alias no Bash

Para atalhos ainda mais curtos, adicione ao seu `~/.bashrc`:

```bash
alias ne1='vpnctl ne1-up'
alias ne1off='vpnctl ne1-down'
alias ne2='vpnctl ne2-up'
alias ne2off='vpnctl ne2-down'
alias ts='vpnctl ts-up'
alias tsoff='vpnctl ts-down'
```

Depois, recarregue o shell:

```bash
source ~/.bashrc
```

## Uso em cron

Como o `vpnctl` pede confirmação interativa por padrão, chamadas via cron **precisam** da flag `--yes` para funcionar
(senão o script detecta a ausência de terminal e aborta por segurança):

```cron
0 19 * * 1-4 root /usr/local/bin/vpnctl ts-up --yes >> /var/log/vpnctl/vpnctl.log 2>&1
```

> Se estiver usando `/etc/cron.d/`, lembre-se da coluna extra de usuário no formato
> (`MIN HORA DIA MÊS DIA_SEMANA USUÁRIO COMANDO`).

## Segurança

- O script nunca lida com senhas diretamente — tanto o `netExtender connect` quanto o `sudo tailscale up/down` usam os
  prompts interativos das próprias ferramentas, o que evita expor credenciais em `ps`, histórico do shell ou logs.
- `sudo` é necessário apenas para os comandos do Tailscale. Se quiser evitar o prompt de senha em uso interativo,
  configure uma regra específica no `visudo` para `tailscale up`/`tailscale down` — evite liberar `NOPASSWD` para o
  comando inteiro `sudo` de forma genérica.

---

# Bônus

Caso queira otimizar consultas DNS dentro das conexões com NetExtender configuradas com split-tunnel
siga para o tutorial [NetExtender Split-DNS helper (systemd-resolved + NetworkManager)](split-dns/README.md).