#!/usr/bin/env bash
set -euo pipefail

# VoxCPM TTS chain health check for blind/audio workflow.
# Usage:
#   bash audio/check_tts_env.sh          # quick check
#   bash audio/check_tts_env.sh --full   # quick check + test synthesis

HOST="${VOXCPM_HOST:-127.0.0.1}"
PORT="${VOXCPM_PORT:-8000}"
HEALTH_URL="http://${HOST}:${PORT}/health"
START_SCRIPT="${VOXCPM_START_SCRIPT:-/home/xsl/AutoVideo/start-voxcpm.sh}"
MODEL_DIR="${VOXCPM_MODEL_DIR:-/home/xsl/models/VoxCPM2}"
VENV_PYTHON="${VOXCPM_PYTHON:-/home/xsl/tts-server/.venv/bin/python}"
LOG_FILE="${VOXCPM_LOG_FILE:-/tmp/voxcpm-server.log}"
FULL_CHECK=0

if [[ "${1:-}" == "--full" ]]; then
  FULL_CHECK=1
fi

ok() { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }
err() { echo "[ERROR] $*"; exit 1; }

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || err "缺少命令: $cmd"
}

wait_health() {
  local max_retry="${1:-30}"
  local i=1
  while [[ "$i" -le "$max_retry" ]]; do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    ((i++))
  done
  return 1
}

print_startup_hint() {
  [[ -f "$LOG_FILE" ]] || return 0
  if grep -q "speech_zipenhancer_ans_multiloss_16k_base" "$LOG_FILE"; then
    warn "检测到降噪模型下载失败（ModelScope），常见原因是 DNS/网络不可达。"
    warn "建议：先确保可访问 modelscope，或在服务端改为可关闭 denoiser。"
  elif grep -q "ConnectionError" "$LOG_FILE"; then
    warn "检测到网络连接错误，请检查当前网络和 DNS。"
  fi
}

start_server() {
  local denoiser="${1:-1}"
  VOXCPM_ENABLE_DENOISER="$denoiser" nohup "$START_SCRIPT" >"$LOG_FILE" 2>&1 &
  local pid=$!
  ok "已发起启动，PID=$pid，日志: $LOG_FILE (denoiser=$denoiser)"
  if wait_health 90; then
    ok "服务启动成功: $HEALTH_URL"
    return 0
  fi
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
  fi
  return 1
}

is_port_busy() {
  ss -lnt | awk '{print $4}' | grep -qE "(^|:)${PORT}$"
}

quick_checks() {
  echo "=== VoxCPM 快速环境检查 ==="
  require_cmd curl
  require_cmd ffmpeg
  require_cmd python3
  require_cmd ss

  [[ -f "$VENV_PYTHON" ]] || err "Python 虚拟环境不存在: $VENV_PYTHON"
  [[ -x "$START_SCRIPT" ]] || warn "启动脚本不可执行，建议: chmod +x $START_SCRIPT"
  [[ -f "$START_SCRIPT" ]] || err "启动脚本不存在: $START_SCRIPT"
  [[ -d "$MODEL_DIR" ]] || err "模型目录不存在: $MODEL_DIR"

  ffmpeg -version >/dev/null 2>&1 || err "FFmpeg 不可用"
  ok "基础依赖可用（curl / ffmpeg / python3 / ss）"
  ok "模型目录存在: $MODEL_DIR"
  ok "虚拟环境存在: $VENV_PYTHON"
}

ensure_server() {
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    ok "TTS 服务已运行: $HEALTH_URL"
    return 0
  fi

  warn "服务未就绪，尝试启动: $START_SCRIPT"
  if is_port_busy; then
    warn "端口 $PORT 已被占用，但 /health 不可达，请检查占用进程"
  fi

  if start_server 1; then
    return 0
  fi

  print_startup_hint
  if grep -q "speech_zipenhancer_ans_multiloss_16k_base" "$LOG_FILE"; then
    warn "检测到 denoiser 远端依赖失败，自动回退到 denoiser=0 重试。"
    if start_server 0; then
      warn "当前服务以 denoiser=0 运行（更稳，降噪关闭）。"
      return 0
    fi
  fi

  print_startup_hint
  err "服务启动超时，查看日志: $LOG_FILE"
}

full_check() {
  echo "=== VoxCPM 全链路测试（注册音色 + 合成） ==="
  local ref_wav="/tmp/voxcpm_check_ref.wav"
  local out_wav="/tmp/voxcpm_check_tts.wav"

  ffmpeg -f lavfi -i "sine=frequency=220:duration=3" -ar 16000 -ac 1 -y "$ref_wav" >/dev/null 2>&1
  ok "生成测试参考音频: $ref_wav"

  local payload
  payload="$(python3 - <<'PY'
import base64, json
with open("/tmp/voxcpm_check_ref.wav", "rb") as f:
    print(json.dumps({"wav_base64": base64.b64encode(f.read()).decode("utf-8")}))
PY
)"

  local voice_resp
  voice_resp="$(curl -fsS -X POST "http://${HOST}:${PORT}/v1/voices" \
    -H "Content-Type: application/json" \
    -d "$payload")"

  local voice_id
  voice_id="$(VOICE_RESP="$voice_resp" python3 - <<'PY'
import json, os
resp = json.loads(os.environ["VOICE_RESP"])
print(resp.get("voice_id", ""))
PY
)"
  [[ -n "$voice_id" ]] || err "注册音色失败: $voice_resp"
  ok "注册测试音色成功: $voice_id"

  local speech_payload
  speech_payload="$(VOICE_ID="$voice_id" python3 - <<'PY'
import json, os
print(json.dumps({
    "text": "这是 VoxCPM 环境自检音频。",
    "voice_id": os.environ["VOICE_ID"],
    "cfg_value": 2.0,
    "inference_timesteps": 10
}))
PY
)"

  local status_code
  status_code="$(curl -sS -o "$out_wav" -w "%{http_code}" \
    -X POST "http://${HOST}:${PORT}/v1/speech" \
    -H "Content-Type: application/json" \
    -d "$speech_payload")"

  [[ "$status_code" == "200" ]] || err "语音合成失败，HTTP $status_code"
  [[ -s "$out_wav" ]] || err "语音合成输出为空: $out_wav"
  ok "语音合成成功: $out_wav"
}

quick_checks
ensure_server
if [[ "$FULL_CHECK" -eq 1 ]]; then
  full_check
fi

echo "=== 检查完成：可开始生产 ==="
