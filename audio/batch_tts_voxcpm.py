#!/usr/bin/env python3
"""
《林夏》TTS 批量生产脚本 — VoxCPM2 版

用法:
  # 先确保 VoxCPM2 服务已启动:
  bash audio/check_tts_env.sh

  # 使用 voice/ 目录 (WAV) 的参考音色
  python audio/batch_tts_voxcpm.py --source voice

  # 使用 voice_mp3/ 目录 (MP3) 的参考音色
  python audio/batch_tts_voxcpm.py --source voice_mp3

  # 只生产指定角色
  python audio/batch_tts_voxcpm.py --source voice --role mom --test

  # 干跑（只看任务列表）
  python audio/batch_tts_voxcpm.py --source voice --dry-run
"""
import os
import sys
import time
import argparse
import subprocess
import tempfile
import base64
import json
import glob

import requests

# ──────────────────────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────────────────────
PROJECT_DIR = "/home/xsl/blind"
OUT_DIR = f"{PROJECT_DIR}/audio/00_raw/tts"

HOST = os.environ.get("VOXCPM_HOST", "127.0.0.1")
PORT = os.environ.get("VOXCPM_PORT", "8000")
BASE_URL = f"http://{HOST}:{PORT}"

# ──────────────────────────────────────────────────────────────
# 角色配置
# dir: voice/ 下的子目录名
# speed: 语速倍率（通过 ffmpeg atempo 后处理）
# ──────────────────────────────────────────────────────────────
ROLES = {
    "mom": {
        "dir": "mom",
        "speed": 0.92,
    },
    "azhe": {
        "dir": "azhe",
        "speed": 1.05,
    },
    "xiaomei": {
        "dir": "xiaomei",
        "speed": 1.10,
    },
    "xiaomei_drunk": {
        "dir": "xiaomei",
        "speed": 0.95,
    },
    "zhounan": {
        "dir": "zhounan",
        "speed": 0.95,
    },
    "hr": {
        "dir": "hr",
        "speed": 1.00,
    },
    "anan": {
        "dir": "anan",
        "speed": 1.15,
    },
    "dorm_a": {
        "dir": "dorm_a",
        "speed": 1.10,
    },
    "dorm_b": {
        "dir": "dorm_b",
        "speed": 1.00,
    },
    "dorm_c": {
        "dir": "dorm_c",
        "speed": 0.95,
    },
    "delivery": {
        "dir": "delivery",
        "speed": 1.20,
    },
    "self_3y": {
        "dir": "xiaomei",
        "speed": 1.15,
    },
}

# ──────────────────────────────────────────────────────────────
# 台词表（对应林夏.md）
# ──────────────────────────────────────────────────────────────
LINES = [
    # ── 01 · 21:03 妈妈电话 ──
    ("lv11_2103_mom_call_01",
     "mom",
     "今晚煮了你爱吃的排骨，给你拍张照啊。下周五回来一趟，你高中物理老师的儿子，挺好的。"),

    # ── 02 · 21:15 小美三连 ──
    ("lv11_2115_xiaomei_voice_01", "xiaomei", "在吗"),
    ("lv11_2115_xiaomei_voice_02", "xiaomei", "你被甩了我都听说了"),
    ("lv11_2115_xiaomei_voice_03", "xiaomei", "明天晚上喝酒，海底捞旁边那家，不许放鸽子"),

    # ── 03 · 21:20 外卖小哥 ──
    ("lv11_2120_delivery_call_01",
     "delivery",
     "你好你的麻辣烫到了，放门口可以吗？"),

    # ── 04 · 21:30 阿哲语音 ──
    ("lv11_2130_azhe_voice_01",
     "azhe",
     "嗯……夏夏。我那个AirPods充电盒，好像落你抽屉里了。"
     "你方便的时候帮我寄一下吗，工位还要用。地址我等下发你。"),

    # ── 05 · 21:45 HR 王姐 ──
    ("lv11_2145_hr_voice_01",
     "hr",
     "夏夏啊，离职流程你下周三之前办完哈，公积金那边记得跟进。"
     "辛苦啦，外面有合适的工作我帮你留意。"),

    # ── 06 · 22:00 安安 ──
    ("lv11_2200_anan_voice_01",
     "anan",
     "夏夏！我在helens！要不要过来！我请客！"),

    # ── 07 · 22:15 寝室群 ──
    ("lv11_2215_dorm_a_voice_01", "dorm_a", "哎你们看，我今天升职了！"),
    ("lv11_2215_dorm_b_voice_01", "dorm_b", "真的啊！恭喜恭喜！太厉害了！"),
    ("lv11_2215_dorm_c_voice_01", "dorm_c", "厉害！那要请客啊！"),
    ("lv11_2215_dorm_a_voice_02", "dorm_a", "哈哈哈必须的！夏夏你怎么不说话呀"),
    ("lv11_2215_dorm_b_voice_02", "dorm_b", "夏夏在忙吧，别打扰她了"),

    # ── 09 · 22:45 小美醉语音（分 4 段）──
    ("lv11_2245_xiaomei_voice_01_seg1",
     "xiaomei_drunk",
     "夏夏夏夏夏。你睡了吗？我跟你说，我跟你说啊……今天我喝多了……"),
    ("lv11_2245_xiaomei_voice_01_seg2",
     "xiaomei_drunk",
     "你别嫌我烦哈，我跟你说……其实啊……阿哲他，大三那年，他来追过我。"
     "我没答应他。我那时候就觉得他这人，呵，差点意思。"),
    ("lv11_2245_xiaomei_voice_01_seg3",
     "xiaomei_drunk",
     "你跟他在一起的时候，我没说，因为说了也没意义嘛对吧。"
     "现在他甩了你，我才敢说。"),
    ("lv11_2245_xiaomei_voice_01_seg4",
     "xiaomei_drunk",
     "夏夏，你听到了吗？你别恨我啊。……喂？算了。"),

    # ── 10 · 23:00 妈妈文字 ──
    ("lv11_2300_mom_text_01", "mom", "睡了吗？"),

    # ── 11 · 23:15 阿哲电话 ──
    ("lv11_2315_azhe_call_01", "azhe", "我能过去拿吗？就5分钟"),

    # ── 12 · 23:30 周南第一条 ──
    ("lv11_2330_zhounan_voice_01",
     "zhounan",
     "林夏，是我，周南。你应该不记得我了吧，初三坐你后桌那个"),

    # ── 13 · 23:45 周南长讲述（4 段）──
    ("lv11_2345_zhounan_voice_01",
     "zhounan",
     "其实我一直想找机会跟你说声谢谢。初三那年你借我笔记，那次考试我才没挂科。"),
    ("lv11_2345_zhounan_voice_02",
     "zhounan",
     "后来高考，我没考好。复读了一年，去了一个二本。然后就回老家了，没什么好说的。"),
    ("lv11_2345_zhounan_voice_03",
     "zhounan",
     "今年第一次来北京出差。来之前我想着，要不要找你。找了很久，才在一个校友群里看到你。"
     "你现在过得怎么样？"),
    ("lv11_2345_zhounan_voice_04",
     "zhounan",
     "今天我生日。本来就想跟你说一声，对不起这么晚。"),

    # ── 14 · 00:15 妈妈电话 ──
    ("lv11_0015_mom_call_01",
     "mom",
     "夏夏，你不接电话我有点担心。妈妈知道你工作忙，你早点睡。"),

    # ── 16 · 02:00 妈妈长语音（分 8 段）──
    ("lv11_0200_mom_voice_01_seg1",
     "mom",
     "夏夏。妈妈知道你今天电话不接。妈妈不催你，就是想跟你说一件事。"),
    ("lv11_0200_mom_voice_01_seg2",
     "mom",
     "你24了对吧。妈妈24那年——你应该没听我说过——"),
    ("lv11_0200_mom_voice_01_seg3",
     "mom",
     "那时候妈妈在广州，给一个香港老板做秘书，1995年。"
     "那年我也被分手过。也被开除过。一模一样的春天。"),
    ("lv11_0200_mom_voice_01_seg4",
     "mom",
     "那年我哭得特别难看。后来呢？后来就没什么后来了。"
     "我回了老家，认识了你爸，生了你。"),
    ("lv11_0200_mom_voice_01_seg5",
     "mom",
     "我跟你说这个不是想跟你说什么都会过去——"
     "我想跟你说，那年夏天我没死，是因为我外婆每天晚上都给我打一个电话。"),
    ("lv11_0200_mom_voice_01_seg6",
     "mom",
     "她不说什么，就问我今天吃饭了没。"),
    ("lv11_0200_mom_voice_01_seg7",
     "mom",
     "我现在打给你，你不接也没事。妈妈给你发个语音，你什么时候想听就听。你不用回我。"),
    ("lv11_0200_mom_voice_01_seg8",
     "mom",
     "你今天接了好多电话吧。妈妈不打扰你了。晚安。"),

    # ── self-3y 三版（台词待编剧定稿）──
    # ("lv11_0030_self-3y_voice_01", "self_3y", "（明朗版台词）"),
    # ("lv11_0030_self-3y_voice_02", "self_3y", "（迷茫版台词）"),
    # ("lv11_0030_self-3y_voice_03", "self_3y", "（温柔版台词）"),
]


# ──────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────

def find_ref_audio(source_dir, role_key):
    """在 source_dir/{dir}/ 下找到第一个音频文件作为参考音色"""
    role_dir = os.path.join(source_dir, ROLES[role_key]["dir"])
    if not os.path.isdir(role_dir):
        return None
    exts = ("*.wav", "*.mp3", "*.flac", "*.ogg")
    for ext in exts:
        files = sorted(glob.glob(os.path.join(role_dir, ext)))
        if files:
            return files[0]
    return None


def wav_to_base64(wav_path):
    """读取 WAV 文件并转 base64"""
    with open(wav_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def convert_to_wav(src_path, dst_path):
    """用 ffmpeg 把任意音频转为 16kHz mono WAV"""
    cmd = [
        "ffmpeg", "-y", "-i", src_path,
        "-ar", "16000", "-ac", "1",
        "-acodec", "pcm_s16le",
        dst_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def apply_speed(wav_path, speed, out_path):
    """用 ffmpeg atempo 调整语速"""
    if abs(speed - 1.0) < 0.01:
        # speed ≈ 1.0，直接复制
        if wav_path != out_path:
            import shutil
            shutil.copy2(wav_path, out_path)
        return
    cmd = [
        "ffmpeg", "-y", "-i", wav_path,
        "-filter:a", f"atempo={speed}",
        "-acodec", "pcm_s16le",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def check_server():
    """检查 VoxCPM 服务是否就绪"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def register_voice(audio_path):
    """向 VoxCPM 注册参考音色，返回 voice_id"""
    b64 = wav_to_base64(audio_path)
    r = requests.post(
        f"{BASE_URL}/v1/voices",
        json={"wav_base64": b64},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["voice_id"]


def synthesize(voice_id, text, cfg_value=2.0, inference_timesteps=10):
    """调用 VoxCPM 合成语音，返回 WAV bytes"""
    r = requests.post(
        f"{BASE_URL}/v1/speech",
        json={
            "text": text,
            "voice_id": voice_id,
            "cfg_value": cfg_value,
            "inference_timesteps": inference_timesteps,
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.content


# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="《林夏》TTS 批量生产 — VoxCPM2 版")
    parser.add_argument("--source", choices=["voice", "voice_mp3"], default="voice",
                        help="音色来源目录 (默认: voice)")
    parser.add_argument("--role", help="只合成指定角色")
    parser.add_argument("--test", action="store_true", help="只合成第一条")
    parser.add_argument("--dry-run", action="store_true", help="只打印任务列表")
    parser.add_argument("--cfg", type=float, default=2.0, help="VoxCPM cfg_value (默认: 2.0)")
    parser.add_argument("--steps", type=int, default=10, help="VoxCPM inference_timesteps (默认: 10)")
    args = parser.parse_args()

    source_dir = os.path.join(PROJECT_DIR, args.source)
    source_tag = "wav" if args.source == "voice" else "mp3"

    lines = LINES
    if args.role:
        lines = [(f, r, t) for f, r, t in lines if r == args.role or r.startswith(args.role)]
    if args.test:
        lines = lines[:1]

    print(f"\n{'=' * 60}")
    print(f" 《林夏》TTS 批量合成 — VoxCPM2")
    print(f" 音色源: {args.source}/ ({source_tag})")
    print(f" 共 {len(lines)} 条")
    print(f"{'=' * 60}")

    # dry-run: 只打印任务
    if args.dry_run:
        voice_cache = {}
        for f, r, t in lines:
            ref = find_ref_audio(source_dir, r)
            if ref is None:
                print(f"  [✗缺参考] {f}  [{r}]  {t[:30]}...")
                continue
            if r not in voice_cache:
                voice_cache[r] = ref
                count = len(glob.glob(os.path.join(source_dir, ROLES[r]["dir"], "*")))
                extra = f" (目录有 {count} 个文件)" if count > 1 else ""
                print(f"  [✓] {f}  [{r}]  ref={os.path.basename(ref)}{extra}  speed={ROLES[r]['speed']}")
            else:
                print(f"  [✓] {f}  [{r}]  {t[:30]}...")
        return

    # 检查服务
    if not check_server():
        print(f"\n[错误] VoxCPM 服务未就绪: {BASE_URL}/health")
        print(f"请先启动服务:")
        print(f"  bash audio/check_tts_env.sh")
        print(f"  或手动启动:")
        print(f"  bash /home/xsl/AutoVideo/start-voxcpm.sh")
        sys.exit(1)

    print(f"  服务就绪: {BASE_URL}/health\n")

    # 预处理：转换 MP3 → WAV，注册音色
    voice_ids = {}   # role_key → voice_id
    tmp_wav_dir = tempfile.mkdtemp(prefix="voxcpm_ref_")

    for role_key in set(r for _, r, _ in lines):
        ref_path = find_ref_audio(source_dir, role_key)
        if ref_path is None:
            print(f"  [跳过] {role_key}: 未找到参考音频 ({source_dir}/{ROLES[role_key]['dir']}/)")
            continue

        # 如果是 MP3 或其他格式，先转为 WAV
        if ref_path.lower().endswith(".wav"):
            wav_path = ref_path
        else:
            wav_path = os.path.join(tmp_wav_dir, f"{role_key}_ref.wav")
            print(f"  转换参考音频: {os.path.basename(ref_path)} → WAV ...", end=" ", flush=True)
            convert_to_wav(ref_path, wav_path)
            print("ok")

        # 注册音色
        print(f"  注册音色: {role_key} ({os.path.basename(ref_path)}) ...", end=" ", flush=True)
        try:
            vid = register_voice(wav_path)
            voice_ids[role_key] = vid
            print(f"ok  voice_id={vid}")
        except Exception as e:
            print(f"失败: {e}")

    print()

    # 合成
    ok_count, skip_count, fail_count = 0, 0, 0
    os.makedirs(OUT_DIR, exist_ok=True)

    for i, (filename, role_key, text) in enumerate(lines, 1):
        out_path = os.path.join(OUT_DIR, f"{filename}_{source_tag}_v1.wav")

        if os.path.exists(out_path):
            print(f"  [{i}/{len(lines)}] [跳过，已存在] {filename}")
            ok_count += 1
            continue

        if role_key not in voice_ids:
            print(f"  [{i}/{len(lines)}] [跳过，无音色] {role_key}: {filename}")
            skip_count += 1
            continue

        print(f"  [{i}/{len(lines)}] {filename} [{role_key}] ...", end=" ", flush=True)
        t0 = time.time()

        try:
            wav_bytes = synthesize(
                voice_ids[role_key], text,
                cfg_value=args.cfg,
                inference_timesteps=args.steps,
            )

            # 先写原始合成结果到临时文件
            tmp_out = out_path + ".raw.wav"
            with open(tmp_out, "wb") as f:
                f.write(wav_bytes)

            # 语速调整
            speed = ROLES[role_key]["speed"]
            apply_speed(tmp_out, speed, out_path)

            # 清理临时文件
            if os.path.exists(tmp_out) and tmp_out != out_path:
                os.remove(tmp_out)

            elapsed = time.time() - t0
            duration = len(wav_bytes) / 48000 / 2  # 粗估 48kHz 16bit
            print(f"✓ {elapsed:.1f}s  speed={speed}")

            ok_count += 1

        except Exception as e:
            print(f"✗ {e}")
            fail_count += 1

    # 清理临时 WAV
    import shutil
    shutil.rmtree(tmp_wav_dir, ignore_errors=True)

    print(f"\n{'=' * 60}")
    print(f" 完成：{ok_count} 条  跳过：{skip_count} 条  失败：{fail_count} 条")
    print(f" 输出目录：{OUT_DIR}")
    print(f" 文件标记：*_{source_tag}_v1.wav")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
