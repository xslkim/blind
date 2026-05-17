#!/bin/bash
# 《林夏》音频后期批量处理脚本
# 用法: bash audio/process_audio.sh [tts|music|sfx|ambience|all]
# 执行前需要先跑 batch_tts.py 生产原始音频

set -e
cd /home/xsl/blind

TYPE="${1:-all}"

# ──────────────────────────────────────────────────────────────
# TTS 后期处理: 00_raw/tts → 01_processed/tts
# ──────────────────────────────────────────────────────────────
process_tts() {
  echo "=== TTS 后期处理 ==="
  local count=0
  for f in audio/00_raw/tts/lv11_*.wav; do
    [ -f "$f" ] || continue
    local base=$(basename "$f")
    local out="audio/01_processed/tts/$base"
    [ -f "$out" ] && echo "  跳过: $base" && continue

    # 判断是否为电话/语音形态（需要加听筒效果）
    local apply_phone=0
    [[ "$base" == *_call_* ]] && apply_phone=1
    [[ "$base" == *_voice_* ]] && apply_phone=1
    # 例外: mom 第 16 条长语音不加听筒效果
    [[ "$base" == *lv11_0200_mom_voice*  ]] && apply_phone=0

    if [ "$apply_phone" -eq 1 ]; then
      # 加听筒效果
      ffmpeg -i "$f" \
        -af "highpass=f=80,\
acompressor=threshold=-18dB:ratio=4:attack=20:release=250,\
highpass=f=300:poles=2,lowpass=f=3400:poles=2,\
equalizer=f=1500:t=q:w=1:g=1,\
loudnorm=I=-16:TP=-1:LRA=11" \
        -ar 48000 -sample_fmt s16 -ac 1 \
        -y "$out" 2>/dev/null
    else
      # 普通处理（文字/系统/长语音）
      ffmpeg -i "$f" \
        -af "highpass=f=80,\
acompressor=threshold=-18dB:ratio=4:attack=20:release=250,\
loudnorm=I=-16:TP=-1:LRA=11" \
        -ar 48000 -sample_fmt s16 -ac 1 \
        -y "$out" 2>/dev/null
    fi

    echo "  ✓ $base"
    ((count++))
  done
  echo "  处理完成 $count 条"
}

# ──────────────────────────────────────────────────────────────
# 拼接分段长戏
# ──────────────────────────────────────────────────────────────
concat_segments() {
  echo "=== 拼接分段长戏 ==="

  # 妈妈 4'17" (8 段)
  local mom_segs=()
  for i in $(seq 1 8); do
    local seg="audio/01_processed/tts/lv11_0200_mom_voice_01_seg${i}_v1.wav"
    [ -f "$seg" ] && mom_segs+=("$seg")
  done
  if [ ${#mom_segs[@]} -eq 8 ]; then
    printf "file '%s'\n" "${mom_segs[@]}" > /tmp/mom_concat.txt
    ffmpeg -f concat -safe 0 -i /tmp/mom_concat.txt \
      -c copy -y audio/01_processed/tts/lv11_0200_mom_voice_01_full.wav 2>/dev/null
    echo "  ✓ 妈妈长语音拼接完成"
  else
    echo "  跳过妈妈拼接（只有 ${#mom_segs[@]}/8 段）"
  fi

  # 小美醉语音 (4 段)
  local xiaomei_segs=()
  for i in $(seq 1 4); do
    local seg="audio/01_processed/tts/lv11_2245_xiaomei_voice_01_seg${i}_v1.wav"
    [ -f "$seg" ] && xiaomei_segs+=("$seg")
  done
  if [ ${#xiaomei_segs[@]} -eq 4 ]; then
    printf "file '%s'\n" "${xiaomei_segs[@]}" > /tmp/xiaomei_concat.txt
    ffmpeg -f concat -safe 0 -i /tmp/xiaomei_concat.txt \
      -c copy -y audio/01_processed/tts/lv11_2245_xiaomei_voice_01_full.wav 2>/dev/null
    echo "  ✓ 小美醉语音拼接完成"
  else
    echo "  跳过小美拼接（只有 ${#xiaomei_segs[@]}/4 段）"
  fi
}

# ──────────────────────────────────────────────────────────────
# 音乐后期: 00_raw/music → 01_processed/music
# ──────────────────────────────────────────────────────────────
process_music() {
  echo "=== 音乐后期处理 ==="
  local count=0
  for f in audio/00_raw/music/*.wav audio/00_raw/music/*.mp3; do
    [ -f "$f" ] || continue
    local base=$(basename "${f%.*}.wav")
    local out="audio/01_processed/music/$base"
    [ -f "$out" ] && echo "  跳过: $base" && continue

    ffmpeg -i "$f" \
      -af "equalizer=f=350:t=q:w=1.5:g=-2,\
loudnorm=I=-18:TP=-1:LRA=11" \
      -ar 48000 -ac 2 \
      -y "$out" 2>/dev/null
    echo "  ✓ $base"
    ((count++))
  done
  echo "  处理完成 $count 条"
}

# ──────────────────────────────────────────────────────────────
# 音效后期: 00_raw/sfx → 01_processed/sfx
# ──────────────────────────────────────────────────────────────
process_sfx() {
  echo "=== 音效后期处理 ==="
  local count=0
  for f in audio/00_raw/sfx/*.wav audio/00_raw/sfx/*.mp3; do
    [ -f "$f" ] || continue
    local base=$(basename "${f%.*}.wav")
    local out="audio/01_processed/sfx/$base"
    [ -f "$out" ] && continue

    ffmpeg -i "$f" \
      -af "loudnorm=I=-14:TP=-1:LRA=11" \
      -ar 48000 \
      -y "$out" 2>/dev/null
    echo "  ✓ $base"
    ((count++))
  done
  echo "  处理完成 $count 条"
}

# ──────────────────────────────────────────────────────────────
# 环境底噪后期: 00_raw/ambience → 01_processed/ambience
# ──────────────────────────────────────────────────────────────
process_ambience() {
  echo "=== 环境底噪后期处理 ==="
  local count=0
  for f in audio/00_raw/ambience/*.wav; do
    [ -f "$f" ] || continue
    local base=$(basename "$f")
    local out="audio/01_processed/ambience/$base"
    [ -f "$out" ] && continue

    local channels=$(ffprobe -v quiet -select_streams a:0 \
      -show_entries stream=channels -of csv=p=0 "$f" 2>/dev/null)

    if [ "$channels" -eq 1 ] 2>/dev/null; then
      # 单声道→假性立体声
      ffmpeg -i "$f" \
        -filter_complex "[0:a]asplit=2[L][Rc];[Rc]adelay=12|12[R];[L][R]amerge=inputs=2[out]" \
        -map "[out]" -ac 2 \
        -af "highpass=f=60,lowpass=f=12000,loudnorm=I=-22:TP=-3:LRA=11" \
        -ar 48000 -y "$out" 2>/dev/null
    else
      ffmpeg -i "$f" \
        -af "highpass=f=60,lowpass=f=12000,loudnorm=I=-22:TP=-3:LRA=11" \
        -ar 48000 -ac 2 -y "$out" 2>/dev/null
    fi
    echo "  ✓ $base"
    ((count++))
  done
  echo "  处理完成 $count 条"
}

# ──────────────────────────────────────────────────────────────
# 最终打包: 01_processed → 02_final (.ogg)
# ──────────────────────────────────────────────────────────────
pack_final() {
  echo "=== 最终打包 wav → ogg ==="
  for subdir in tts music sfx ambience; do
    local count=0
    for f in audio/01_processed/$subdir/*.wav; do
      [ -f "$f" ] || continue
      local base=$(basename "${f%.wav}.ogg")
      local out="audio/02_final/$subdir/$base"
      [ -f "$out" ] && continue
      ffmpeg -i "$f" -c:a libvorbis -q:a 5 -y "$out" 2>/dev/null
      ((count++))
    done
    [ $count -gt 0 ] && echo "  ✓ $subdir: $count 条"
  done
  echo "  打包完成"
}

# ──────────────────────────────────────────────────────────────
# 响度验收报告
# ──────────────────────────────────────────────────────────────
qa_loudness() {
  echo "=== 响度验收 ==="
  local pass=0 fail=0

  check_dir() {
    local dir="$1" target="$2" label="$3"
    for f in audio/01_processed/$dir/*.wav; do
      [ -f "$f" ] || continue
      local lufs=$(ffmpeg -i "$f" -af loudnorm=print_format=json -f null - 2>&1 | \
        python3 -c "
import sys, json, re
out = sys.stdin.read()
m = re.search(r'\"input_i\"\s*:\s*\"(-?\d+\.?\d*)\"', out)
print(m.group(1) if m else 'err')
")
      local diff=$(echo "$lufs $target" | awk '{d=$1-$2; if(d<0)d=-d; print d}')
      local ok=$(echo "$diff" | awk '{print ($1 <= 1.5) ? "pass" : "FAIL"}')
      printf "  %-50s %s LUFS  [%s]\n" "$(basename $f)" "$lufs" "$ok"
      [ "$ok" = "pass" ] && ((pass++)) || ((fail++))
    done
  }

  check_dir tts -16 "角色语音"
  check_dir music -18 "音乐"
  check_dir ambience -22 "环境底噪"

  echo ""
  echo "  通过: $pass  不通过: $fail"
}

# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────
echo "《林夏》音频后期处理  $(date '+%Y-%m-%d %H:%M')"
echo "执行类型: $TYPE"
echo ""

case "$TYPE" in
  tts)      process_tts; concat_segments ;;
  music)    process_music ;;
  sfx)      process_sfx ;;
  ambience) process_ambience ;;
  pack)     pack_final ;;
  qa)       qa_loudness ;;
  all)
    process_tts
    concat_segments
    process_music
    process_sfx
    process_ambience
    pack_final
    ;;
  *)
    echo "用法: bash audio/process_audio.sh [tts|music|sfx|ambience|pack|qa|all]"
    exit 1 ;;
esac

echo ""
echo "完成  $(date '+%H:%M:%S')"
