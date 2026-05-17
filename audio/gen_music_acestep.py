#!/usr/bin/env python3
"""
《林夏》BGM + 角色铃声 批量生成脚本
使用 ACE-Step 1.5 本地模型

用法:
  conda activate acestep
  python audio/gen_music_acestep.py [--category bgm|ringtone|all] [--dry-run]
"""
import os, sys, time, argparse

# ── ACE-Step 修复（RTX 5090 cuBLAS）──────────────────────────
import torch
torch.backends.cuda.preferred_blas_library("cublaslt")

REPO_DIR  = "/home/xsl/tools/ACE-Step-1.5"
OUT_DIR   = "/home/xsl/blind/audio/00_raw/music"
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, REPO_DIR)

# ── BGM 四段 ─────────────────────────────────────────────────
BGM_TRACKS = [
    {
        "filename": "lv11_bgm_m1_main_loop",
        "duration": 90,
        "caption": (
            "lo-fi midnight bedroom, soft piano, light vinyl crackle, "
            "muted piano, subtle synth pad, occasional distant rain, "
            "melancholy but warm, alone but not lonely, "
            "ambient loop, no drums, no clear melody peak, 70 bpm"
        ),
        "lyrics": "",
        "steps": 20,
        "seed": 2103,
        "note": "M1 · 21:00 主题 Loop",
    },
    {
        "filename": "lv11_bgm_m2_suspense",
        "duration": 30,
        "caption": (
            "subtle ambient suspense, cinematic tension, "
            "low drone, single hanging piano note high register, sparse strings, "
            "unsettling but not horror, like a question mark, "
            "builds slowly, ends on unresolved chord, 60 bpm"
        ),
        "lyrics": "",
        "steps": 20,
        "seed": 2230,
        "note": "M2 · 22:30 悬疑过门",
    },
    {
        "filename": "lv11_bgm_m3_zhounan",
        "duration": 120,
        "caption": (
            "gentle indie folk, intimate acoustic, "
            "fingerpicked nylon guitar, wordless soft humming no lyrics just mmm, "
            "light shaker, hopeful nostalgic like reading an old letter, "
            "gradual build soft climax at 80 seconds gentle outro, 75 bpm"
        ),
        "lyrics": "",
        "steps": 25,
        "seed": 2345,
        "note": "M3 · 23:45 周南段落",
    },
    {
        "filename": "lv11_bgm_m4_ending",
        "duration": 90,
        "caption": (
            "warm cinematic piano, dawn moment, solo piano, "
            "soft string pad entering at 30 seconds, "
            "like the moment you realize you survived a hard night, "
            "single melody line, no drums, fade out, 50 bpm"
        ),
        "lyrics": "",
        "steps": 20,
        "seed": 200,
        "note": "M4 · 02:00 结尾",
    },
]

# ── 角色铃声 9 个 ──────────────────────────────────────────────
RINGTONES = [
    {
        "filename": "lv11_ring_mom",
        "duration": 6,
        "caption": "warm marimba ringtone, simple 4-note motif, old Nokia style, 70 bpm, loop",
        "note": "妈妈铃声",
        "seed": 1001,
    },
    {
        "filename": "lv11_ring_azhe",
        "duration": 5,
        "caption": "cold minimal electronic ringtone, 2 notes only, distant, 80 bpm, loop",
        "note": "阿哲铃声",
        "seed": 1002,
    },
    {
        "filename": "lv11_ring_xiaomei",
        "duration": 5,
        "caption": "cheerful pop ringtone, ukulele plucks, 4-bar phrase, energetic, 100 bpm, loop",
        "note": "小美铃声",
        "seed": 1003,
    },
    {
        "filename": "lv11_ring_zhounan",
        "duration": 5,
        "caption": "nostalgic 90s chime, soft marimba, gentle, 70 bpm, loop",
        "note": "周南铃声",
        "seed": 1004,
    },
    {
        "filename": "lv11_ring_hr",
        "duration": 5,
        "caption": "corporate professional ringtone, neutral marimba, clean, 90 bpm, loop",
        "note": "HR王姐铃声",
        "seed": 1005,
    },
    {
        "filename": "lv11_ring_anan",
        "duration": 4,
        "caption": "bouncy J-pop intro ringtone, bright, energetic, 110 bpm, loop",
        "note": "安安铃声",
        "seed": 1006,
    },
    {
        "filename": "lv11_ring_dorm_group",
        "duration": 5,
        "caption": "soft group notification chime, friendly, warm bells, 80 bpm, loop",
        "note": "寝室群铃声",
        "seed": 1007,
    },
    {
        "filename": "lv11_ring_unknown",
        "duration": 6,
        "caption": "eerie low drone ringtone, no melody, unsettling, 40 bpm, dark ambient, loop",
        "note": "未知号码铃声",
        "seed": 1008,
    },
    {
        "filename": "lv11_ring_delivery",
        "duration": 3,
        "caption": "short delivery notification beep, simple two-tone, neutral, 90 bpm",
        "note": "外卖铃声",
        "seed": 1009,
    },
]


def load_handler():
    """初始化 ACE-Step handler（带 cublaslt 修复）"""
    from acestep.handler import AceStepHandler
    print("正在加载 ACE-Step 模型...", end=" ", flush=True)
    t0 = time.time()
    handler = AceStepHandler()
    handler.initialize_service(
        project_root=REPO_DIR,
        config_path="acestep-v15-turbo",
        device="cuda",
    )
    print(f"就绪 ({time.time()-t0:.1f}s)  dtype={handler.dtype}")
    return handler


def generate_one(handler, track, is_ringtone=False):
    """生成单条音频，返回输出路径或 None"""
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    filename = track["filename"]
    out_path = os.path.join(OUT_DIR, f"{filename}_v1.wav")

    if os.path.exists(out_path):
        print(f"  [跳过] {filename}（已存在）")
        return out_path

    note = track.get("note", "")
    print(f"  生成: {filename}  [{note}]  {track['duration']}s ...", end=" ", flush=True)

    params = GenerationParams(
        caption=track["caption"],
        lyrics=track.get("lyrics", ""),
        duration=track["duration"],
        instrumental=True,
        inference_steps=track.get("steps", 20),
        seed=track.get("seed", 42),
    )
    from acestep.inference import GenerationConfig
    config = GenerationConfig(batch_size=1, audio_format="wav")

    t0 = time.time()
    try:
        result = generate_music(handler, None, params, config, save_dir=OUT_DIR)
        elapsed = time.time() - t0
        if result.success:
            gen_path = result.audios[0]["path"]
            # 重命名为规范名称
            if gen_path != out_path:
                os.rename(gen_path, out_path)
            print(f"✓ {elapsed:.1f}s  → {os.path.basename(out_path)}")
            return out_path
        else:
            print(f"✗ {result.error}")
            return None
    except Exception as e:
        print(f"✗ {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["bgm", "ringtone", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    all_tracks = []
    if args.category in ("bgm", "all"):
        all_tracks += [("bgm", t) for t in BGM_TRACKS]
    if args.category in ("ringtone", "all"):
        all_tracks += [("ringtone", t) for t in RINGTONES]

    print(f"\n{'='*60}")
    print(f"《林夏》音乐生成  共 {len(all_tracks)} 条")
    print(f"输出目录: {OUT_DIR}")
    print(f"{'='*60}")

    if args.dry_run:
        for cat, t in all_tracks:
            exists = "✓" if os.path.exists(os.path.join(OUT_DIR, f"{t['filename']}_v1.wav")) else "○"
            print(f"  [{exists}][{cat}] {t['filename']}  {t['duration']}s  {t.get('note','')}")
        return

    handler = load_handler()

    ok, skip, fail = 0, 0, 0
    for cat, track in all_tracks:
        result = generate_one(handler, track, is_ringtone=(cat == "ringtone"))
        if result is None:
            fail += 1
        elif "跳过" in str(result):
            skip += 1
        else:
            ok += 1

    print(f"\n{'='*60}")
    print(f"完成 {ok}  跳过 {skip}  失败 {fail}")
    print(f"输出: {OUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
