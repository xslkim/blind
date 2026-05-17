#!/usr/bin/env python3
"""
《林夏》SFX 批量生成脚本（ACE-Step 1.5）
生成环境氛围类、过渡类、结局类音效

非 ACE-Step 的短促 UI 音效（叮、咚、震动）需另行处理，
本脚本专注可由 ACE-Step 生成的 ≥5s 氛围类音效。

用法:
  conda activate acestep
  python audio/gen_sfx_acestep.py [--dry-run]
"""
import os, sys, time, argparse
import torch
torch.backends.cuda.preferred_blas_library("cublaslt")

REPO_DIR = "/home/xsl/tools/ACE-Step-1.5"
OUT_DIR  = "/home/xsl/blind/audio/00_raw/sfx"
AMB_DIR  = "/home/xsl/blind/audio/00_raw/ambience"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(AMB_DIR, exist_ok=True)

sys.path.insert(0, REPO_DIR)

# ── 氛围类音效（ACE-Step 可生成）─────────────────────────────
SFX_TRACKS = [
    # 过渡 / 转场
    {
        "filename": "sfx_transition_chapter",
        "dir": OUT_DIR,
        "duration": 8,
        "caption": "cinematic transition swell, soft orchestral, gentle rise and fall, cinematic fade",
        "note": "章节过渡轻 swell",
        "seed": 2001,
    },
    {
        "filename": "sfx_heartbeat_fast",
        "dir": OUT_DIR,
        "duration": 8,
        "caption": "human heartbeat accelerating, tension building, thumping close mic, anxiety",
        "note": "心跳加速",
        "seed": 2002,
    },
    {
        "filename": "sfx_deep_breath",
        "dir": OUT_DIR,
        "duration": 6,
        "caption": "single deep breath, calm, close mic, soft exhale, meditative",
        "note": "深呼吸",
        "seed": 2003,
    },
    {
        "filename": "sfx_rain_heavier",
        "dir": OUT_DIR,
        "duration": 8,
        "caption": "rain suddenly intensifying, window glass, urban rain, dramatic shift",
        "note": "雨势忽大",
        "seed": 2004,
    },
    {
        "filename": "sfx_rain_lighter",
        "dir": OUT_DIR,
        "duration": 8,
        "caption": "rain gradually softening, distant window, fading urban rain, peaceful",
        "note": "雨势忽小",
        "seed": 2005,
    },
    {
        "filename": "sfx_glass_shatter_short",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "glass breaking, single crash, sharp impact, quiet aftermath",
        "note": "玻璃碎一秒",
        "seed": 2006,
    },

    # 结局专用
    {
        "filename": "sfx_ending_chime",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "soft chime, title card reveal, delicate bells, warm resonance, fade out",
        "note": "字幕浮现 chime",
        "seed": 2007,
    },
    {
        "filename": "sfx_night_bus",
        "dir": OUT_DIR,
        "duration": 10,
        "caption": "late night bus passing on empty street, distant rumble, urban quiet",
        "note": "夜班车驶过",
        "seed": 2008,
    },
    {
        "filename": "sfx_cat_yowl",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "single cat yowl distant alley, late night, brief, natural",
        "note": "野猫叫一声",
        "seed": 2009,
    },
    {
        "filename": "sfx_breathing_unknown",
        "dir": OUT_DIR,
        "duration": 8,
        "caption": "quiet human breathing through phone, slightly muffled, anonymous, eerie stillness",
        "note": "未知号码呼吸",
        "seed": 2010,
    },

    # 拟音
    {
        "filename": "sfx_kettle_whistle",
        "dir": OUT_DIR,
        "duration": 6,
        "caption": "kettle whistling, close mic, small kitchen, vintage, building steam",
        "note": "烧水壶哨响",
        "seed": 2011,
    },
    {
        "filename": "sfx_water_boiling",
        "dir": OUT_DIR,
        "duration": 8,
        "caption": "water boiling in kettle, bubbling, close mic, kitchen ambience",
        "note": "水沸腾",
        "seed": 2012,
    },
    {
        "filename": "sfx_keyboard_slow",
        "dir": OUT_DIR,
        "duration": 6,
        "caption": "slow thoughtful keyboard typing, soft mechanical, contemplative rhythm",
        "note": "键盘慢打",
        "seed": 2013,
    },
    {
        "filename": "sfx_keyboard_fast",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "fast keyboard typing, mechanical, busy, rapid rhythm, office",
        "note": "键盘快打",
        "seed": 2014,
    },
    {
        "filename": "sfx_door_knock_gentle",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "gentle three knocks on apartment door, polite delivery, hallway echo",
        "note": "外卖敲门（轻）",
        "seed": 2015,
    },
    {
        "filename": "sfx_door_knock_firm",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "firm knocking on apartment door, impatient, louder, hallway",
        "note": "外卖敲门（响）",
        "seed": 2016,
    },
    {
        "filename": "sfx_phone_vibrate",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "phone vibrating on wooden bedside table, buzzing, close mic, 2 bursts",
        "note": "手机震动桌面",
        "seed": 2017,
    },
    {
        "filename": "sfx_paper_turning",
        "dir": OUT_DIR,
        "duration": 5,
        "caption": "paper pages turning, quiet desk, gentle rustling, close mic",
        "note": "纸张翻动",
        "seed": 2018,
    },
]

# ── 环境底噪（单独输出到 ambience/）────────────────────────────
AMBIENCE_TRACKS = [
    {
        "filename": "amb_apartment_night_01",
        "dir": AMB_DIR,
        "duration": 120,
        "caption": (
            "late night apartment ambience, very quiet, distant traffic, "
            "refrigerator hum, occasional water pipe, urban residential, "
            "stereo, immersive, Beijing night"
        ),
        "note": "合租屋夜晚底噪 (2min loop段)",
        "seed": 3001,
    },
    {
        "filename": "amb_apartment_night_02",
        "dir": AMB_DIR,
        "duration": 120,
        "caption": (
            "quiet Beijing apartment at night, minimal sounds, "
            "faint city noise, soft hum, occasional distant car, "
            "late 2020s urban residential night ambience"
        ),
        "note": "合租屋夜晚底噪备用",
        "seed": 3002,
    },
    {
        "filename": "amb_bar_loud_01",
        "dir": AMB_DIR,
        "duration": 60,
        "caption": (
            "crowded bar ambience, people talking laughing, "
            "background electronic music, glasses clinking, "
            "busy nightclub atmosphere, lively"
        ),
        "note": "酒吧嘈杂环境",
        "seed": 3003,
    },
    {
        "filename": "amb_rain_window_01",
        "dir": AMB_DIR,
        "duration": 120,
        "caption": (
            "gentle rain on window, soft steady patter, "
            "cozy indoor feeling, night rain, Beijing apartment, "
            "stereo, immersive"
        ),
        "note": "窗外细雨（BGM M1 衬底）",
        "seed": 3004,
    },
    {
        "filename": "amb_kitchen_morning",
        "dir": AMB_DIR,
        "duration": 60,
        "caption": (
            "morning kitchen sounds, water dripping tap, "
            "refrigerator hum, quiet domestic morning, "
            "natural, realistic"
        ),
        "note": "厨房晨间（结局A）",
        "seed": 3005,
    },
    {
        "filename": "amb_dawn_birds",
        "dir": AMB_DIR,
        "duration": 30,
        "caption": (
            "dawn birds chirping, urban morning, early light, "
            "sparse birdsong, peaceful city dawn"
        ),
        "note": "清晨鸟叫（结局D）",
        "seed": 3006,
    },
]

ALL_TRACKS = SFX_TRACKS + AMBIENCE_TRACKS


def load_handler():
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


def generate_one(handler, track):
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    out_dir = track["dir"]
    filename = track["filename"]
    out_path = os.path.join(out_dir, f"{filename}_v1.wav")

    if os.path.exists(out_path):
        print(f"  [跳过] {filename}")
        return "skip"

    note = track.get("note", "")
    print(f"  {filename} [{note}] {track['duration']}s ...", end=" ", flush=True)

    params = GenerationParams(
        caption=track["caption"],
        lyrics="",
        duration=track["duration"],
        instrumental=True,
        inference_steps=20,
        seed=track.get("seed", 42),
    )
    config = GenerationConfig(batch_size=1, audio_format="wav")

    t0 = time.time()
    try:
        result = generate_music(handler, None, params, config, save_dir=out_dir)
        if result.success:
            gen_path = result.audios[0]["path"]
            if gen_path != out_path:
                os.rename(gen_path, out_path)
            print(f"✓ {time.time()-t0:.1f}s")
            return "ok"
        else:
            print(f"✗ {result.error}")
            return "fail"
    except Exception as e:
        print(f"✗ {e}")
        return "fail"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--category", choices=["sfx", "ambience", "all"], default="all")
    args = parser.parse_args()

    tracks = []
    if args.category in ("sfx", "all"):
        tracks += SFX_TRACKS
    if args.category in ("ambience", "all"):
        tracks += AMBIENCE_TRACKS

    print(f"\n{'='*60}")
    print(f"《林夏》SFX + 环境底噪生成  共 {len(tracks)} 条")
    print(f"SFX 输出: {OUT_DIR}")
    print(f"环境 输出: {AMB_DIR}")
    print(f"{'='*60}")

    if args.dry_run:
        for t in tracks:
            out = os.path.join(t["dir"], f"{t['filename']}_v1.wav")
            flag = "✓" if os.path.exists(out) else "○"
            print(f"  [{flag}] {t['filename']}  {t['duration']}s  {t.get('note','')}")
        return

    handler = load_handler()

    ok = skip = fail = 0
    for track in tracks:
        r = generate_one(handler, track)
        if r == "ok":   ok += 1
        elif r == "skip": skip += 1
        else:           fail += 1

    print(f"\n{'='*60}")
    print(f"完成 {ok}  跳过 {skip}  失败 {fail}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
