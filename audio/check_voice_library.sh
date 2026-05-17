#!/usr/bin/env bash
set -euo pipefail

# Check reference voice library completeness for batch TTS.
# Usage:
#   bash audio/check_voice_library.sh

BASE_DIR="/home/xsl/blind/audio/00_raw/tts/prompt_ref"
MANIFEST="${BASE_DIR}/ref_manifest.txt"

REQUIRED_FILES=(
  "mom_ref.wav"
  "azhe_ref.wav"
  "xiaomei_ref.wav"
  "zhounan_ref.wav"
  "hr_ref.wav"
  "anan_ref.wav"
  "dorm_a_ref.wav"
  "dorm_b_ref.wav"
  "dorm_c_ref.wav"
  "delivery_ref.wav"
)

ok() { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }
err() { echo "[ERROR] $*"; }

missing_count=0
warn_count=0

command -v ffprobe >/dev/null 2>&1 || {
  err "缺少 ffprobe（请安装 ffmpeg）"
  exit 1
}

echo "=== 角色音色库检查 ==="
echo "目录: $BASE_DIR"
echo ""

if [[ ! -f "$MANIFEST" ]]; then
  err "缺少清单文件: $MANIFEST"
  ((missing_count+=1))
fi

for f in "${REQUIRED_FILES[@]}"; do
  path="${BASE_DIR}/${f}"
  if [[ ! -f "$path" ]]; then
    err "缺少参考音频: $f"
    ((missing_count+=1))
    continue
  fi

  sample_rate="$(ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 "$path" || true)"
  channels="$(ffprobe -v error -select_streams a:0 -show_entries stream=channels -of default=noprint_wrappers=1:nokey=1 "$path" || true)"
  duration="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$path" || true)"
  duration_int="${duration%.*}"

  if [[ -z "$sample_rate" || -z "$channels" || -z "$duration" ]]; then
    warn "无法读取音频信息: $f"
    ((warn_count+=1))
    continue
  fi

  if [[ "$sample_rate" -lt 16000 ]]; then
    warn "$f 采样率 ${sample_rate}Hz，低于 16kHz"
    ((warn_count+=1))
  fi
  if [[ "$channels" -ne 1 ]]; then
    warn "$f 声道数 ${channels}，建议为单声道"
    ((warn_count+=1))
  fi
  if [[ "$duration_int" -lt 5 || "$duration_int" -gt 30 ]]; then
    warn "$f 时长 ${duration}s，建议 5-30s"
    ((warn_count+=1))
  fi

  ok "$f 通过基础检测 (${sample_rate}Hz/${channels}ch/${duration}s)"
done

echo ""
if [[ -f "$MANIFEST" ]]; then
  for f in "${REQUIRED_FILES[@]}"; do
    line="$(awk -F'|' -v file="$f" '$1 ~ file {print $0}' "$MANIFEST" | head -n 1)"
    if [[ -z "$line" ]]; then
      err "清单缺少条目: $f"
      ((missing_count+=1))
      continue
    fi

    text="$(echo "$line" | awk -F'|' '{sub(/^[ \t]+/, "", $2); sub(/[ \t]+$/, "", $2); print $2}')"
    if [[ -z "$text" || "$text" == TODO:* ]]; then
      warn "清单文本未完成: $f"
      ((warn_count+=1))
    fi
  done
fi

echo ""
echo "=== 结果 ==="
echo "缺失项: $missing_count"
echo "警告项: $warn_count"

if [[ "$missing_count" -gt 0 ]]; then
  exit 2
fi
if [[ "$warn_count" -gt 0 ]]; then
  exit 1
fi
ok "音色库完整，可进入批量 TTS。"
