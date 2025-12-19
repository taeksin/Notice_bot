#!/usr/bin/env bash
set -euo pipefail

# Notice_bot daemon helper
# - 시작 명령은 반드시: nohup uv run work_notice.py &

APP_NAME="work_notice"
SCRIPT_FILE="work_notice.py"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
PID_FILE="${ROOT_DIR}/${APP_NAME}.pid"
APP_LOG_FILE="${LOG_DIR}/app.log"
NOHUP_LOG_FILE="${LOG_DIR}/nohup.log"

ensure_dirs() {
  mkdir -p "${LOG_DIR}"
}

is_running() {
  if [[ -f "${PID_FILE}" ]]; then
    local pid
    pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

start() {
  ensure_dirs
  cd "${ROOT_DIR}"

  if is_running; then
    echo "[${APP_NAME}] already running (pid=$(cat "${PID_FILE}"))"
    exit 0
  fi

  if [[ ! -f "${ROOT_DIR}/${SCRIPT_FILE}" ]]; then
    echo "[${APP_NAME}] ERROR: ${SCRIPT_FILE} not found in ${ROOT_DIR}"
    exit 1
  fi

  echo "[${APP_NAME}] starting..."
  # 요청 사항: 프로그램을 켤 때는 아래 형태를 사용해야 함
  # 주의: custom_logger가 logs/app.log로도 기록하므로,
  # nohup 리다이렉트는 별도 파일로 분리(중복 방지)
  nohup uv run "${SCRIPT_FILE}" >>"${NOHUP_LOG_FILE}" 2>&1 &
  echo $! > "${PID_FILE}"
  echo "[${APP_NAME}] started (pid=$(cat "${PID_FILE}")), app_log=${APP_LOG_FILE}, nohup_log=${NOHUP_LOG_FILE}"
}

stop() {
  if [[ ! -f "${PID_FILE}" ]]; then
    echo "[${APP_NAME}] not running (no pid file)"
    exit 0
  fi

  local pid
  pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
  if [[ -z "${pid}" ]]; then
    rm -f "${PID_FILE}"
    echo "[${APP_NAME}] not running (empty pid file)"
    exit 0
  fi

  if ! kill -0 "${pid}" 2>/dev/null; then
    rm -f "${PID_FILE}"
    echo "[${APP_NAME}] not running (stale pid=${pid})"
    exit 0
  fi

  echo "[${APP_NAME}] stopping (pid=${pid})..."

  # 자식 프로세스가 있을 수 있으니(uv run -> python), 먼저 자식에 TERM 시도
  if command -v pkill >/dev/null 2>&1; then
    pkill -TERM -P "${pid}" >/dev/null 2>&1 || true
  fi

  kill -TERM "${pid}" 2>/dev/null || true

  # 종료 대기 (최대 10초)
  for _ in {1..10}; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      rm -f "${PID_FILE}"
      echo "[${APP_NAME}] stopped"
      exit 0
    fi
    sleep 1
  done

  echo "[${APP_NAME}] still running, force kill..."
  if command -v pkill >/dev/null 2>&1; then
    pkill -KILL -P "${pid}" >/dev/null 2>&1 || true
  fi
  kill -KILL "${pid}" 2>/dev/null || true
  rm -f "${PID_FILE}"
  echo "[${APP_NAME}] stopped (forced)"
}

status() {
  if is_running; then
    echo "[${APP_NAME}] running (pid=$(cat "${PID_FILE}")), app_log=${APP_LOG_FILE}, nohup_log=${NOHUP_LOG_FILE}"
  else
    echo "[${APP_NAME}] not running"
  fi
}

restart() {
  stop || true
  start
}

logf() {
  ensure_dirs
  touch "${APP_LOG_FILE}" "${NOHUP_LOG_FILE}"

  local target="app"
  local lines="200"

  # ./daemon.sh log 500
  if [[ "${2:-}" =~ ^[0-9]+$ ]]; then
    lines="${2}"
  # ./daemon.sh log nohup [500]
  elif [[ "${2:-}" == "nohup" || "${2:-}" == "app" ]]; then
    target="${2}"
    if [[ "${3:-}" =~ ^[0-9]+$ ]]; then
      lines="${3}"
    fi
  fi

  local file="${APP_LOG_FILE}"
  if [[ "${target}" == "nohup" ]]; then
    file="${NOHUP_LOG_FILE}"
  fi

  echo "[${APP_NAME}] tail -n ${lines} -f ${file}"
  tail -n "${lines}" -f "${file}"
}

usage() {
  cat <<EOF
Usage: ./daemon.sh <command>

Commands:
  start     Start using: nohup uv run ${SCRIPT_FILE} &
  stop      Stop
  restart   Restart
  status    Show status
  log       Tail app log (default: last 200 lines)
            - ./daemon.sh log nohup [LINES]  (tail nohup redirect log)
EOF
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  log) logf "${@}" ;;
  *) usage; exit 1 ;;
esac


