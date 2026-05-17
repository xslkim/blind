#!/usr/bin/env python3
"""
《林夏》TTS 批量生产脚本
用法:
  conda activate cosyvoice
  cd /home/xsl/blind
  python audio/batch_tts.py [--role mom] [--test]

参数:
  --role ROLE   只生产指定角色（不指定则全部）
  --test        只合成第一条，用于快速验证环境
  --dry-run     只打印任务列表，不实际合成
"""
import os, sys, time, argparse, warnings
import torch
import soundfile as sf  # torchaudio nightly requires torchcodec; use soundfile instead

warnings.filterwarnings("ignore")

COSYVOICE_DIR = "/home/xsl/tools/CosyVoice"
PROJECT_DIR   = "/home/xsl/blind"
REF_DIR       = f"{PROJECT_DIR}/audio/00_raw/tts/prompt_ref"
OUT_DIR       = f"{PROJECT_DIR}/audio/00_raw/tts"

sys.path.insert(0, COSYVOICE_DIR)
sys.path.insert(0, f"{COSYVOICE_DIR}/third_party/Matcha-TTS")
os.chdir(COSYVOICE_DIR)

# ──────────────────────────────────────────────────────────────
# 角色配置（对应 SOP §4.2）
# ref_wav / ref_text 在参考音频备齐前先留空
# ──────────────────────────────────────────────────────────────
ROLES = {
    "mom": {
        "speed": 0.92,
        "ref_wav":  f"{REF_DIR}/mom_ref.wav",
        "ref_text": "",   # ← 参考音频对应文字，备齐后填入
    },
    "azhe": {
        "speed": 1.05,
        "ref_wav":  f"{REF_DIR}/azhe_ref.wav",
        "ref_text": "",
    },
    "xiaomei": {
        "speed": 1.10,
        "ref_wav":  f"{REF_DIR}/xiaomei_ref.wav",
        "ref_text": "",
    },
    "xiaomei_drunk": {           # 醉语音用同参考，speed 调慢
        "speed": 0.95,
        "ref_wav":  f"{REF_DIR}/xiaomei_ref.wav",
        "ref_text": "",
    },
    "zhounan": {
        "speed": 0.95,
        "ref_wav":  f"{REF_DIR}/zhounan_ref.wav",
        "ref_text": "",
    },
    "hr": {
        "speed": 1.00,
        "ref_wav":  f"{REF_DIR}/hr_ref.wav",
        "ref_text": "",
    },
    "anan": {
        "speed": 1.15,
        "ref_wav":  f"{REF_DIR}/anan_ref.wav",
        "ref_text": "",
    },
    "dorm_a": {
        "speed": 1.10,
        "ref_wav":  f"{REF_DIR}/dorm_a_ref.wav",
        "ref_text": "",
    },
    "dorm_b": {
        "speed": 1.00,
        "ref_wav":  f"{REF_DIR}/dorm_b_ref.wav",
        "ref_text": "",
    },
    "dorm_c": {
        "speed": 0.95,
        "ref_wav":  f"{REF_DIR}/dorm_c_ref.wav",
        "ref_text": "",
    },
    "delivery": {
        "speed": 1.20,
        "ref_wav":  f"{REF_DIR}/delivery_ref.wav",
        "ref_text": "",
    },
    "self_3y": {                 # 复用 xiaomei，speed +0.05
        "speed": 1.15,
        "ref_wav":  f"{REF_DIR}/xiaomei_ref.wav",
        "ref_text": "",
    },
    # system 用预训练音色，不在这里
}

# ──────────────────────────────────────────────────────────────
# 台词表（对应林夏.md §3 + §5）
# 格式: (输出文件前缀, 角色key, 台词)
# 长戏（≥30s）已按 SOP §5.3 拆分为分段
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


def load_model():
    from cosyvoice.cli.cosyvoice import CosyVoice2
    print("加载 CosyVoice2 模型...")
    model = CosyVoice2("pretrained_models/CosyVoice2-0.5B")
    print(f"模型就绪，采样率 {model.sample_rate}Hz")
    return model


def load_ref(role_cfg):
    from cosyvoice.utils.file_utils import load_wav
    wav_path = role_cfg["ref_wav"]
    if not os.path.exists(wav_path):
        return None, None
    wav = load_wav(wav_path, 16000)
    # 裁到 30s 以内
    max_samples = 16000 * 30
    if wav.shape[1] > max_samples:
        wav = wav[:, :max_samples]
    return wav, role_cfg["ref_text"]


def synthesize(model, filename, role_key, text):
    role_cfg = ROLES[role_key]
    ref_wav, ref_text = load_ref(role_cfg)

    out_path = f"{OUT_DIR}/{filename}_v1.wav"
    if os.path.exists(out_path):
        print(f"  [跳过，已存在] {filename}")
        return True

    if ref_wav is None:
        print(f"  [跳过，缺参考音频] {role_key}: {role_cfg['ref_wav']}")
        return False

    if not ref_text.strip():
        print(f"  [跳过，ref_text 未填] {role_key}")
        return False

    t0 = time.time()
    chunks = []
    for chunk in model.inference_zero_shot(
        tts_text=text,
        prompt_text=ref_text,
        prompt_speech_16k=ref_wav,
        stream=False,
        speed=role_cfg["speed"],
    ):
        chunks.append(chunk["tts_speech"])

    if not chunks:
        print(f"  [失败，无输出] {filename}")
        return False

    audio = torch.concat(chunks, dim=1)
    duration = audio.shape[1] / model.sample_rate
    sf.write(out_path, audio.squeeze().cpu().numpy(), model.sample_rate)

    elapsed = time.time() - t0
    rtf = elapsed / duration if duration > 0 else 0
    print(f"  ✓ {filename}  {duration:.1f}s 音频  {elapsed:.1f}s 耗时  RTF={rtf:.3f}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role",    help="只合成指定角色")
    parser.add_argument("--test",    action="store_true", help="只合成第一条")
    parser.add_argument("--dry-run", action="store_true", help="只打印任务")
    args = parser.parse_args()

    lines = LINES
    if args.role:
        lines = [(f, r, t) for f, r, t in lines if r == args.role or r.startswith(args.role)]
    if args.test:
        lines = lines[:1]

    print(f"\n{'='*60}")
    print(f" 《林夏》TTS 批量合成  共 {len(lines)} 条")
    print(f"{'='*60}")

    if args.dry_run:
        for f, r, t in lines:
            ref_exists = "✓" if os.path.exists(ROLES.get(r, {}).get("ref_wav", "")) else "✗缺参考"
            print(f"  [{ref_exists}] {f}  [{r}]  {t[:30]}...")
        return

    model = load_model()
    ok, skip, fail = 0, 0, 0
    for i, (filename, role_key, text) in enumerate(lines, 1):
        print(f"\n[{i}/{len(lines)}] {filename}")
        result = synthesize(model, filename, role_key, text)
        if result is True:  ok += 1
        elif result is None: skip += 1
        else: fail += 1

    print(f"\n{'='*60}")
    print(f" 完成：{ok} 条  跳过：{skip} 条  失败：{fail} 条")
    print(f" 输出目录：{OUT_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
