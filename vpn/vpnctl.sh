#!/usr/bin/env bash
#
# vpnctl.sh — alterna entre múltiplas conexões NetExtender e o Tailscale,
# garantindo que apenas uma esteja ativa por vez.
#
# Uso: vpnctl.sh <ação> [--yes]
#   Ações: ne1-up | ne1-down | ne2-up | ne2-down | ts-up | ts-down
#   --yes  : não pergunta, desconecta a outra VPN automaticamente se necessário
#            (uso pensado para chamadas não-interativas, ex: cron)
#
# Requisitos:
#   - NetExtender CLI (nxcli/netExtender) instalado e configurado
#   - Tailscale instalado
#   - Um arquivo de configuração com os dados das suas conexões (veja README.md)

set -uo pipefail   # sem -e: tratamos erros nós mesmos e seguimos interativos

# --- Configuração ---

VPNCTL_CONFIG="${VPNCTL_CONFIG:-$HOME/.config/vpnctl/vpnctl.conf}"

if [[ ! -f "$VPNCTL_CONFIG" ]]; then
  echo "Arquivo de configuração não encontrado: $VPNCTL_CONFIG" >&2
  echo "Copie vpnctl.conf.example para esse caminho e preencha com seus dados." >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$VPNCTL_CONFIG"

for var in NE1_CLIENT_NAME NE1_CONNECTION_NAME NE1_SERVER_PATTERN NE2_CLIENT_NAME NE2_CONNECTION_NAME NE2_SERVER_PATTERN; do
  if [[ -z "${!var:-}" ]]; then
    echo "Variável obrigatória '$var' não definida em $VPNCTL_CONFIG" >&2
    exit 1
  fi
done

AUTO_YES=false

# --- Detecção de status ---

_is_netextender_connected_to() {
  local pattern="$1"
  nxcli status 2>/dev/null | grep -qi "$pattern"
}

is_netextender1_connected() { _is_netextender_connected_to "$NE1_SERVER_PATTERN"; }
is_netextender2_connected() { _is_netextender_connected_to "$NE2_SERVER_PATTERN"; }

is_tailscale_connected() {
  tailscale status --json 2>/dev/null | grep -q '"BackendState": *"Running"'
}

# --- Ações ---

nx_connect() {
  local connection_name="$1" label="$2"
  echo "Conectando à $label..."
  netExtender connect "$connection_name"
}

nx_disconnect() {
  echo "Desconectando do NetExtender..."
  nxcli disconnect
}

tailscale_connect() {
  echo "Conectando ao Tailscale (pode solicitar senha sudo)..."
  sudo tailscale up
}

tailscale_disconnect() {
  echo "Desconectando do Tailscale (pode solicitar senha sudo)..."
  sudo tailscale down
}

# --- Exclusividade mútua ---

confirm_and_disconnect_other() {
  local other_name="$1"
  local disconnect_fn="$2"

  if [[ "$AUTO_YES" == true ]]; then
    echo "Conexão com $other_name está ativo. --yes informado, desconectando automaticamente."
    "$disconnect_fn"
    return
  fi

  if [[ ! -t 0 ]]; then
    echo "Conexão com $other_name está ativo e não há terminal interativo disponível (stdin não é um TTY)."
    echo "Abortando por segurança. Use --yes se quiser permitir troca automática nesse contexto."
    exit 1
  fi

  read -r -p "Conexão com $other_name está ativo. Deseja desconectá-lo agora para continuar? [s/N] " resp
  case "$resp" in
    [sS]|[sS][iI][mM])
      "$disconnect_fn"
      ;;
    *)
      echo "Operação abortada."
      exit 1
      ;;
  esac
}

ensure_tailscale_disconnected_if_active() {
  if is_tailscale_connected; then
    confirm_and_disconnect_other "Tailscale" tailscale_disconnect
  fi
}

ensure_netextender_disconnected_if_active() {
  local label="$1" check_fn="$2"
  if "$check_fn"; then
    confirm_and_disconnect_other "$label" nx_disconnect
  fi
}

# --- Parse de argumentos ---

usage() {
  echo "Uso: $(basename "$0") <ação> [--yes]" >&2
  echo "Ações: ne1-up | ne1-down | ne2-up | ne2-down | ts-up | ts-down" >&2
}

ACTION=""
for arg in "$@"; do
  case "$arg" in
    --yes) AUTO_YES=true ;;
    -h|--help) usage; exit 0 ;;
    ne1-up|ne1-down|ne2-up|ne2-down|ts-up|ts-down) ACTION="$arg" ;;
    *) echo "Argumento desconhecido: $arg" >&2; usage; exit 1 ;;
  esac
done

# --- Main ---

case "$ACTION" in
  ne1-up)
    ensure_tailscale_disconnected_if_active
    ensure_netextender_disconnected_if_active "$NE2_CLIENT_NAME" is_netextender2_connected
    nx_connect "$NE1_CONNECTION_NAME" "$NE1_CLIENT_NAME"
    ;;
  ne1-down)
    nx_disconnect
    ;;
  ne2-up)
    ensure_tailscale_disconnected_if_active
    ensure_netextender_disconnected_if_active "$NE1_CLIENT_NAME" is_netextender1_connected
    nx_connect "$NE2_CONNECTION_NAME" "$NE2_CLIENT_NAME"
    ;;
  ne2-down)
    nx_disconnect
    ;;
  ts-up)
    if is_netextender1_connected || is_netextender2_connected; then
      confirm_and_disconnect_other "NetExtender" nx_disconnect
    fi
    tailscale_connect
    ;;
  ts-down)
    tailscale_disconnect
    ;;
  *)
    usage
    exit 1
    ;;
esac