#!/usr/bin/env python3
"""
生成缺失的 TTS 资产：
  - self-3y 三个版本（明朗/迷茫/温柔）
  - system 系统提示音 TTS
使用 VoxCPM2 API (http://127.0.0.1:8000)
"""
import os, sys, time, glob, base64, subprocess, tempfile, shutil
import requests

PROJECT_DIR = "/home/xsl/blind"
OUT_DIR     = f"{PROJECT_DIR}/audio/00_raw/tts"
VOICE_DIR   = f"{PROJECT_DIR}/voice"
BASE_URL    = "http://127.0.0.1:8000"

os.makedirs(OUT_DIR, exist_ok=True)

# ── 台词定义 ──────────────────────────────────────────────────

MISSING_LINES = [
    # self-3y 明朗版（23岁刚来北京，对一切新鲜）
    ("lv11_0030_self3y_voice_01",  # filename（不含后缀）
     "xiaomei",                    # 音色来源目录（同xiaomei基底+调整）
     0.95,                         # speed（比正常略快，体现23岁轻盈）
     "哦对，今天是我来北京的第一百天。妈，我没跟你说，我自己数的。"
     "这个城市好大。我走了很多路，见了很多人。我觉得我还没准备好，"
     "但我又觉得好像准备了很久很久了。你们不用担心我。我很好。"
     "以后的我，如果你听到这条，记得要好好的。"),

    # self-3y 迷茫版（其实已经很累了，只是没说）
    ("lv11_0030_self3y_voice_02",
     "xiaomei",
     1.00,
     "我今天又没睡好。不是失眠，就是睡不踏实。"
     "北京这个地方，它会让你觉得你随时都要更好，随时都要更努力。"
     "我在努力。但我不知道在努力什么。"
     "我就想留下一条记录。今天，今天是……算了，就今天吧。"),

    # self-3y 温柔版（对未来的自己说撑住）
    ("lv11_0030_self3y_voice_03",
     "xiaomei",
     1.00,
     "是我。23岁的我。我设了三年后打开。"
     "我不知道那时候的你怎么样了。如果你很好，就当我多虑了。"
     "如果你不好——你看，你熬过来了对不对。"
     "你23岁的时候，也觉得很难。但你还是过来了。"
     "所以……撑住啊。"),

    # system TTS — 游戏系统提示
    ("lv11_sys_battery_01",   "xiaomei", 1.00, "电量百分之一"),
    ("lv11_sys_battery_02",   "xiaomei", 1.00, "电量不足，请及时充电"),
    ("lv11_sys_unread_01",    "xiaomei", 1.00, "您有一条未读消息"),
    ("lv11_sys_unread_multi", "xiaomei", 1.00, "您有多条未读消息"),
    ("lv11_sys_memo_01",      "xiaomei", 1.00, "三年前今天，一条未听的录音"),
    ("lv11_sys_goodnight",    "xiaomei", 1.00, "晚安"),
]

# ── 工具函数 ──────────────────────────────────────────────────

def find_ref(voice_dir_name):
    d = os.path.join(VOICE_DIR, voice_dir_name)
    for ext in ("*.wav", "*.mp3", "*.flac"):
        files = sorted(glob.glob(os.path.join(d, ext)))
        if files:
            return files[0]
    return None

def to_wav(src, dst):
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", dst],
        check=True, capture_output=True
    )

def apply_speed(src, speed, dst):
    if abs(speed - 1.0) < 0.01:
        shutil.copy2(src, dst)
        return
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-filter:a", f"atempo={speed}", "-acodec", "pcm_s16le", dst],
        check=True, capture_output=True
    )

def register_voice(wav_path):
    with open(wav_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post(f"{BASE_URL}/v1/voices", json={"wav_base64": b64}, timeout=60)
    r.raise_for_status()
    return r.json()["voice_id"]

def synthesize(voice_id, text):
    r = requests.post(f"{BASE_URL}/v1/speech",
                      json={"text": text, "voice_id": voice_id, "cfg_value": 2.0, "inference_timesteps": 10},
                      timeout=180)
    r.raise_for_status()
    return r.content

# ── 主流程 ────────────────────────────────────────────────────

def main():
    # 健康检查
    try:
        requests.get(f"{BASE_URL}/health", timeout=5).raise_for_status()
        print(f"VoxCPM 服务就绪: {BASE_URL}")
    except Exception as e:
        print(f"[错误] VoxCPM 服务不可用: {e}")
        sys.exit(1)

    tmp_dir = tempfile.mkdtemp(prefix="tts_missing_")
    voice_cache = {}   # dir_name → voice_id

    print(f"\n共 {len(MISSING_LINES)} 条待合成\n{'='*50}")

    ok, skip, fail = 0, 0, 0
    for filename, voice_dir, speed, text in MISSING_LINES:
        out_path = os.path.join(OUT_DIR, f"{filename}_wav_v1.wav")
        if os.path.exists(out_path):
            print(f"  [跳过已存在] {filename}")
            skip += 1
            continue

        # 注册音色（缓存）
        if voice_dir not in voice_cache:
            ref = find_ref(voice_dir)
            if not ref:
                print(f"  [✗无参考] {voice_dir}: {filename}")
                fail += 1
                continue
            wav_ref = os.path.join(tmp_dir, f"{voice_dir}_ref.wav")
            if not ref.endswith(".wav"):
                to_wav(ref, wav_ref)
            else:
                shutil.copy2(ref, wav_ref)
            print(f"  注册音色 [{voice_dir}] ...", end=" ", flush=True)
            vid = register_voice(wav_ref)
            voice_cache[voice_dir] = vid
            print(f"ok ({vid[:8]}…)")

        print(f"  合成: {filename} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            raw_bytes = synthesize(voice_cache[voice_dir], text)
            tmp_raw = os.path.join(tmp_dir, f"{filename}.raw.wav")
            with open(tmp_raw, "wb") as f:
                f.write(raw_bytes)
            apply_speed(tmp_raw, speed, out_path)
            print(f"✓ {time.time()-t0:.1f}s  → {os.path.basename(out_path)}")
            ok += 1
        except Exception as e:
            print(f"✗ {e}")
            fail += 1

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\n{'='*50}")
    print(f"完成 {ok}  跳过 {skip}  失败 {fail}")
    print(f"输出: {OUT_DIR}")

if __name__ == "__main__":
    main()
