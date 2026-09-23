# NetExtender Split-DNS helper (systemd-resolved + NetworkManager)

Script de dispatcher do NetworkManager que configura **split-DNS** de forma segura quando você se conecta via
**SonicWall NetExtender** no Linux.

O objetivo é:

- Manter o DNS **público** (Google, Cloudflare, etc.) fora do túnel (split-tunnel real).
- Usar os DNS **internos** de cada cliente **somente** para os domínios daquele cliente.
- Suportar **múltiplos clientes** NetExtender sem conflito.

---

## Requisitos

- Linux com **NetworkManager** + **systemd-resolved** (Fedora, Ubuntu recente, etc.)
- Cliente **SonicWall NetExtender**
- Interface da VPN normalmente aparece como `snwl*` ou `*ssltunnel*`

---

## Arquivos

| Arquivo              | Descrição            |
|----------------------|----------------------|
| `99-netextender-dns` | Script do dispatcher |
| `README.md`          | Este arquivo         |

---

## Instalação rápida

1. **Configure o DNS global** (recomendado – fica fora do túnel):

   Edite `/etc/systemd/resolved.conf`:

   ```ini
   [Resolve]
   DNS=8.8.8.8 1.1.1.1
   FallbackDNS=
   Domains=~.
   ```

   Depois:

   ```bash
   sudo systemctl restart systemd-resolved
   ```
   
   > Esta etapa pode variar entre distribuições linux. Qualquer problema consulte o manual de sua distribuição.

2. **Instale o script**:

   ```bash
   sudo cp 99-netextender-dns /etc/NetworkManager/dispatcher.d/
   sudo chmod +x /etc/NetworkManager/dispatcher.d/99-netextender-dns
   ```

3. **Personalize o script** com os dados reais de cada cliente (veja seção abaixo).

4. Reconecte a VPN ou reinicie o NetworkManager:

   ```bash
   sudo systemctl restart NetworkManager
   ```

---

## Como personalizar para seus clientes

Abra o arquivo `/etc/NetworkManager/dispatcher.d/99-netextender-dns` e substitua os placeholders:

### 1. Detecção do cliente

O script identifica o cliente pelos **DNS que o NetExtender empurrou**.

Exemplo para o Cliente 1:

```bash
if echo "$DNS_LIST" | grep -qE '10\.x\.x\.10|10\.x\.x\.11'; then
```

### 2. DNS e domínios do cliente

```bash
resolvectl dns "$INTERFACE" 10.x.x.10 10.x.x.11
resolvectl domain "$INTERFACE" empresa.com.br interno.empresa
```

Repita o bloco `elif` para quantos clientes precisar.

### 3. Descobrindo os valores corretos

Com a VPN já conectada, execute:

```bash
resolvectl status
```

Anote:

- Nome da interface (geralmente `snwl_ssltunnel` ou similar)
- `DNS Servers` daquela interface → use esses IPs na detecção e no `resolvectl dns`
- Domínios internos que você realmente precisa resolver através da VPN

---

## Como funciona

1. O NetworkManager detecta que a interface da VPN subiu.
2. O script espera 3 segundos para a interface estabilizar.
3. Lê os DNS que o NetExtender acabou de empurrar.
4. Compara com os padrões conhecidos de cada cliente.
5. Aplica:
    - DNS internos **somente** na interface da VPN
    - Domínios de busca/roteamento **somente** para aquele cliente
6. Faz `flush-caches` para garantir que a nova configuração seja usada imediatamente.

Consultas para domínios públicos continuam usando o DNS global (fora do túnel).  
Consultas para os domínios configurados usam o DNS interno (dentro do túnel).

---

## Testes recomendados

Com a VPN conectada:

```bash
# Ver a configuração atual
resolvectl status

# Query pública (deve sair pela interface física)
resolvectl query google.com

# Query interna do cliente (deve usar a interface da VPN)
resolvectl query site-interno.cliente.tld

# Verificar rota dos pacotes DNS públicos
ip route get 8.8.8.8
```

O `dig` sempre mostrará `SERVER: 127.0.0.53` — isso é normal com systemd-resolved.  
O importante é o que o `resolvectl query` e o `ip route get` mostram.

---

## Logs

O script envia mensagens para o journal:

```bash
journalctl -t netextender-dns -b
```

---

## Desativando temporariamente

```bash
sudo mv /etc/NetworkManager/dispatcher.d/99-netextender-dns \
        /etc/NetworkManager/dispatcher.d/99-netextender-dns.disabled
```

Para reativar, renomeie de volta e reconecte a VPN.

---

## Notas importantes

- O script **não** altera o DNS global. Ele só configura a **interface da VPN**.
- Funciona bem com split-tunnel nativo do NetExtender.
- Se você adicionar um terceiro cliente, basta incluir mais um bloco `elif`.
