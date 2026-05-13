# AI 音频生产 SOP · v1.0

> **适用项目**：《语音 99+》（11_语音99+.md），同时可复用于本系列其他黑屏耳机项目。
> **使用对象**：项目主控 1 人 + 音频执行 1–2 人，无需专业录音棚。
> **预期产出**：约 30 分钟净时长的角色语音 + 4 段 BGM + 60+ 短音效 + 8 段环境底噪。
> **预期工时**：4 周（含 1 周返工窗口）。
> **预期音频成本**：¥800–1200。

---

## 0. 文档使用方法

- 第 1–3 章是**总规约**：所有人开工前必读。
- 第 4 章是**项目专用配置**：每开新项目要复制一份重新填写。
- 第 5–8 章是**四类资产的生产 SOP**：执行人按章节对照操作即可。
- 第 9–10 章是**后期与验收**：产出每一批资产后强制走一遍。
- 第 11 章是**版权归档**：每个文件都要登记。
- 附录是**复用资源**：Prompt 模板库 / 命名词典 / 验收清单 PDF 版。

---

## 1. Pipeline 总览

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  T0  脚本定稿     │ → │  T1  音频拆条    │ → │  T2  生产排期     │
│  (编剧)          │   │  (音频主控)       │   │  (音频主控)       │
└──────────────────┘   └──────────────────┘   └──────────────────┘
                                                       ↓
       ┌───────────────────────────┬───────────────────┬────────────────┐
       ↓                           ↓                   ↓                ↓
┌─────────────┐           ┌─────────────┐    ┌─────────────┐   ┌─────────────┐
│ T3a TTS生产  │           │ T3b 音乐生产 │    │ T3c 音效生产 │   │ T3d 环境采样 │
│ MiniMax/豆包 │           │   Suno V4    │    │ ElevenLabs  │   │  Freesound  │
└─────────────┘           └─────────────┘    └─────────────┘   └─────────────┘
       ↓                           ↓                   ↓                ↓
       └───────────────────────────┴───────────────────┴────────────────┘
                                       ↓
                          ┌─────────────────────────┐
                          │ T4  后期统一处理        │
                          │ (响度/降噪/淡入淡出)    │
                          └─────────────────────────┘
                                       ↓
                          ┌─────────────────────────┐
                          │ T5  QA 验收             │
                          │ (3 副耳机盲听)          │
                          └─────────────────────────┘
                                       ↓
                          ┌─────────────────────────┐
                          │ T6  入库 + 交付         │
                          │ (Git LFS + 版权登记)    │
                          └─────────────────────────┘
```

---

## 2. 工具栈与账号清单

### 2.1 必备工具表

| 用途 | 工具 | 版本/方案 | 月费 | 国内访问 | 备注 |
|---|---|---|---|---|---|
| **中文 TTS 主力** | MiniMax Speech 02 (HD) | API | 按字数 ¥200–500 | ✅ 直连 | 中文情绪戏首选 |
| **中文 TTS 备用** | 字节豆包 Voice | API | ¥100–300 | ✅ 直连 | 系统女声 + 男声补位 |
| **TTS 兜底** | 阿里通义听悟 / 腾讯云 TTS | API | ¥100–200 | ✅ 直连 | 备选 |
| **海外 TTS** | ElevenLabs v3 | Creator $22/月 | ≈¥160 | ⚠️ 需出海 | 仅在 MiniMax 表现不够时备用 |
| **AI 音乐** | Suno V4 / V4.5 | Pro $10/月 | ≈¥75 | ⚠️ 需出海 | 国内备选：天工 SkyMusic |
| **AI 音效** | ElevenLabs Sound Effects | 含在上面套餐内 | — | ⚠️ 需出海 | 国内备选：阿里通义万相音效 |
| **环境采样** | Freesound | 免费（CC0/CC-BY） | 0 | ✅ 直连 | 注意标注作者 |
| **环境采样补充** | Epidemic Sound | $15/月 个人版 | ≈¥110 | ✅ 直连 | 有 SFX/BGM 双库 |
| **音频后期** | iZotope RX 11 + REAPER | 一次性 | ≈¥2000 | ✅ 直连 | 团队共享一份 |
| **响度计** | Youlean Loudness Meter 2 | Free 版即可 | 0 | ✅ 直连 | LUFS 监控必备 |
| **格式转换** | FFmpeg | Free | 0 | ✅ 直连 | 命令行批处理 |
| **资源管理** | Git LFS + Notion | — | 0 | ✅ 直连 | 资产 + 版权登记表 |

### 2.2 账号准备清单（开工 D-7 完成）

- [ ] MiniMax 开发者账号 + 充值 ¥500 起
- [ ] 字节豆包账号 + 充值 ¥300 起
- [ ] ElevenLabs Creator 订阅（含 Sound Effects 100k credits/月）
- [ ] Suno Pro 订阅（500 首/月，足够）
- [ ] Freesound 注册账号（用于下载追踪）
- [ ] Epidemic Sound 个人订阅
- [ ] Git LFS 启用 + S3/OSS 备份桶
- [ ] Notion 中建好「音频版权登记表」模板（见 §11.2）

### 2.3 海外工具的合规访问方式
- 团队主控通过合规企业 VPN（如阿里云国际版、腾讯云海外节点）访问。
- 不在产品线上代码中嵌入任何海外 API key——所有 Suno / ElevenLabs 资源**全部线下生产、本地存储、入库后离线打包随 App 发布**。
- App 运行时**不调用任何海外服务**。

---

## 3. 文件命名与目录规范

### 3.1 顶层目录结构

```
audio/
├── 00_raw/                    # 原始生成物，不进版本库
│   ├── tts/
│   ├── music/
│   ├── sfx/
│   └── ambience/
├── 01_processed/              # 后期处理后，进 Git LFS
│   ├── tts/
│   ├── music/
│   ├── sfx/
│   └── ambience/
├── 02_final/                  # 打包入 App 的最终版
│   └── (按关卡组织)
├── 03_qa_reports/             # 每批 QA 报告
└── 99_legal/                  # 版权登记表 + 授权证明
```

### 3.2 文件命名规范

**格式**：`{关卡号}_{时间码}_{角色}_{形态}_{序号}_{版本}.{ext}`

| 字段 | 取值 | 说明 |
|---|---|---|
| 关卡号 | `lv11` 等 | 项目代号 |
| 时间码 | `2103`、`2245` | 剧内时间，HHMM |
| 角色 | `mom` `azhe` `xiaomei` `zhounan` `hr` `anan` `system` `delivery` `unknown` `dorm-a` `dorm-b` `dorm-c` `self-3y` | 见 §4.1 角色代号表 |
| 形态 | `call` `voice` `text` `sys` | 通话/微信语音/文字 TTS/系统提示 |
| 序号 | `01`、`02`… | 同角色同时间码下的多条消息 |
| 版本 | `v1`、`v2`、`final` | 迭代版本 |

**示例**：
- `lv11_2103_mom_call_01_final.wav` — 妈妈 21:03 第一通电话最终版
- `lv11_2245_xiaomei_voice_01_v2.wav` — 小美 22:45 醉语音第二稿

**禁止**：
- 中文文件名（避免编码与 Git 兼容问题）
- 空格、`(`、`)`、`#` 等特殊字符
- 大写字母（统一小写）

### 3.3 音频技术规格统一

| 字段 | 规格 | 说明 |
|---|---|---|
| **采样率** | 48 kHz | 全程统一，避免重采样杂音 |
| **位深** | 24-bit（生产）/ 16-bit（最终） | 后期保留 24-bit 头，导出降到 16-bit |
| **声道** | 单声道（角色语音）/ 立体声（音乐与环境） | 严格区分 |
| **格式** | `.wav`（生产中）/ `.ogg` Vorbis q=5（入包） | 入包再压缩，节省体积 |
| **响度** | -16 LUFS（角色语音）/ -18 LUFS（音乐）/ -20 LUFS（环境） | 详见 §9.1 |
| **峰值上限** | -1 dBTP | 避免溢出 |

---

## 4. 角色 Voice 配置表（项目专用）

> 本章是项目工程师的"配音演员花名册"。**每个角色的 voice id、参数、prompt 前缀全部在这里固定下来**，避免不同执行人产出风格漂移。

### 4.1 角色代号表

| 角色 | 代号 | 净时长估算 | 主语种 | 形态 |
|---|---|---|---|---|
| 妈妈 | `mom` | ~7 min | 中文 | 电话×2 + 微信文字×1 + 语音×1（4'17"长戏） |
| 阿哲（前任） | `azhe` | ~2 min | 中文 | 微信语音×1 + 电话×1 |
| 小美（闺蜜） | `xiaomei` | ~3 min | 中文 | 微信语音×3（含 1'20"醉戏） |
| HR 王姐 | `hr` | ~1 min | 中文 | 微信语音×1 |
| 室友安安 | `anan` | ~30 s | 中文 | 微信语音×1 |
| 寝室群 A/B/C | `dorm-a` `dorm-b` `dorm-c` | ~2 min 共 | 中文 | 群语音×5 |
| 周南（同桌） | `zhounan` | ~5 min | 中文 | 微信语音×5（含 4 段长讲述） |
| 外卖小哥 | `delivery` | ~10 s | 中文（北方腔） | 电话×1 |
| 系统 TTS | `system` | ~2 min | 中文 | 全局提示 |
| 未知号码 | `unknown` | 无台词 | — | 仅环境呼吸声 |
| 3 年前的自己 | `self-3y` | ~50s × 3 版 | 中文 | 备忘录录音（明朗/迷茫/温柔三版预录） |
| 林夏的笑（隐藏） | `self-laugh` | ~3s | — | 仅结局 E 播放，全片唯一林夏自己的声音 |

### 4.2 角色 Voice 配置卡

每张卡固定一个角色的所有参数。**生产时严格按卡操作**。

---

#### 卡 01 · `mom`（妈妈）

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02 HD |
| Voice ID | `Chinese_Mandarin_Warm_Auntie_v3`（占位，待实际选定后回填） |
| Speed | 0.92（略慢） |
| Volume | 1.0 |
| Pitch | 0 |
| Emotion | `gentle` |
| 备用方案 | 第 16 条 4 分钟长戏改用**克隆方案**：找一位 50 岁左右真人录 30 秒原声，MiniMax Voice Clone，emotion 提到 `tender` |
| Prompt 前缀 | `<语气：温柔克制，不哭不闹，西北口音淡化，语速比常人慢半拍>` |
| SSML 控制 | 长句中段加 `<break time="500ms"/>`，结尾"晚安"前加 `<break time="1.2s"/>` |
| 后期处理 | 加 -3 dB 高频衰减（让"妈妈感"更柔），轻 reverb wet 8% 模拟客厅 |

---

#### 卡 02 · `azhe`（阿哲 / 前任）

| 项 | 值 |
|---|---|
| 主用 TTS | 字节豆包 Voice |
| Voice ID | `灿烂青年男声-v2`（北京口音淡，理性偏冷） |
| Speed | 1.05 |
| Volume | 0.95 |
| Pitch | -1 |
| Emotion | `neutral` |
| Prompt 前缀 | `<语气：礼貌但已抽离，像在跟同事说话，不带感情起伏>` |
| 后期处理 | -2 dB 中频，让声音"闷"一点，模拟"已经远了"的距离感 |

---

#### 卡 03 · `xiaomei`（小美 / 闺蜜）

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02 |
| Voice ID | `Chinese_Mandarin_Lively_Girl_v2` |
| Speed | 1.10（前两条快）/ 0.95（醉语音慢） |
| Volume | 1.0 |
| Pitch | +1 |
| Emotion | `cheerful`（前两条）/ `melancholic + drunk`（第 9 条） |
| Prompt 前缀 | `<语气：北漂女孩，活泼略大大咧咧，会爆粗，醉酒段口齿模糊但不夸张>` |
| 醉戏特殊处理 | 在 SSML 中插入 `<break time="800ms"/>` 模拟停顿 + 末句故意拉长元音；后期再叠 5% 房间混响 + 微弱酒吧 BGM 底噪 |

---

#### 卡 04 · `hr`（HR 王姐）

| 项 | 值 |
|---|---|
| 主用 TTS | 字节豆包 Voice |
| Voice ID | `知性女声-成熟款` |
| Speed | 1.00 |
| Pitch | 0 |
| Emotion | `gentle + apologetic` |
| Prompt 前缀 | `<语气：38 岁职场女性，疲惫的善意，公事公办里带一点点歉意>` |

---

#### 卡 05 · `anan`（室友安安）

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02 |
| Voice ID | `Chinese_Mandarin_Cute_Girl_v2` |
| Speed | 1.15（兴奋） |
| Pitch | +2 |
| Emotion | `excited` |
| Prompt 前缀 | `<语气：23 岁，撒娇感比小美更重，背景嘈杂酒吧>` |
| 后期处理 | 必须叠酒吧环境底噪（见 §8 ambience 库 `bar_loud_03.wav`），干声 -3 dB |

---

#### 卡 06 · `dorm-a/b/c`（大学寝室群三女生）

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02，**三个不同 Voice ID 必须区分明显** |
| 候选 IDs | A: `Lively_Girl_v2` / B: `Sweet_Girl_v3` / C: `Mature_Young_Lady_v2` |
| Speed | A: 1.10 / B: 1.00 / C: 0.95 |
| Pitch | A: +1 / B: 0 / C: -1 |
| Emotion | A: `cheerful` / B: `gentle` / C: `neutral` |
| 备注 | A 是升职那位；B 是和事佬；C 是 @ 林夏的那位 |

---

#### 卡 07 · `zhounan`（周南 / 初中同桌）

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02 |
| Voice ID | `Chinese_Mandarin_Gentleman_Young_v2` |
| Speed | 0.95 |
| Volume | 0.92（略轻，模拟拘谨） |
| Pitch | -1 |
| Emotion | `gentle + nervous` |
| Prompt 前缀 | `<语气：26 岁二三线男生，温和拘谨，明显紧张但克制，偶有自嘲>` |
| 4 段长戏 | 每段独立生成，段间留 800 ms 静音；句尾上扬避免"播音感" |

---

#### 卡 08 · `delivery`（外卖小哥）

| 项 | 值 |
|---|---|
| 主用 TTS | 字节豆包 Voice |
| Voice ID | `北方青年男声-v2` |
| Speed | 1.20（麻利） |
| Emotion | `neutral` |
| Prompt 前缀 | `<语气：30 岁，普通话+少许河南腔，工作语气，不寒暄>` |
| 后期处理 | 加 -6 dB 低频衰减 + 轻底噪，模拟手机听筒 |

---

#### 卡 09 · `system`（系统 TTS）

| 项 | 值 |
|---|---|
| 主用 TTS | 字节豆包 Voice |
| Voice ID | `通用女声-柔` |
| Speed | 1.00 |
| Pitch | 0 |
| Emotion | `flat`（无情绪） |
| Prompt 前缀 | `<语气：中性 AI 助手，类似 Siri 但更轻，不带任何情感>` |

---

#### 卡 10 · `self-3y`（3 年前的自己）

> ⚠️ **本作零麦克风权限**——本条不再使用玩家录音方案，改为**预录三版**按运行时玩家行为画像（PROFILE）动态选择。

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02 HD（建议与林夏未来版本预留同一克隆音色，便于 IP 续作） |
| Voice ID | 与 `xiaomei` 同基底音色（暗示"她们曾是同类年轻女孩"），但 speed +0.05、pitch +1，模拟 3 年前更轻盈的语调 |
| 三个预录版本 | ①「**明朗版**」：3 年前刚来北京，对一切都新鲜<br>②「**迷茫版**」：3 年前其实已经累，只是没说<br>③「**温柔版**」：3 年前对未来的自己说"撑住" |
| 选择逻辑 | 按 PROFILE 标签匹配：<br>`engagement` → 明朗版（与今夜的投入呼应）<br>`avoidance` → 迷茫版（与今夜的回避呼应）<br>`nostalgia` → 温柔版（与今夜的怀旧呼应） |
| 时长 | 每版 ~50 秒 |
| 后期处理 | 加 -2 dB 高频衰减 + 微弱"录音笔底噪"，模拟"3 年前用手机备忘录录的"质感 |
| Prompt 前缀（明朗版） | `<语气：23 岁，刚到北京半年，兴奋里带一点紧张，相信明天比今天好>` |
| Prompt 前缀（迷茫版） | `<语气：23 岁，独自在出租屋里，假装坚强，最后一句声音轻下去>` |
| Prompt 前缀（温柔版） | `<语气：23 岁，写给未来的自己，平静、有力、像在拥抱什么>` |

#### 卡 11 · `self-laugh`（隐藏结局 E 的笑声）

| 项 | 值 |
|---|---|
| 主用 TTS | MiniMax Speech 02 HD（同 `self-3y` 同一克隆音色） |
| 内容 | 一段 3 秒的轻笑——"噗"+ 一声短笑 + 一声轻轻的鼻息 |
| 制作方式 | TTS 难以直接生成自然笑声，**建议方案**：<br>① 找声线接近的 24 岁女声真人**录一次笑**（5 分钟搞定，零成本）<br>② 用 MiniMax Voice Clone 同款音色 + emotion `playful` 生成尝试，作为备选 |
| 用途 | 仅在结局 E 触发时播放——**全片唯一一次**林夏自己的声音 |
| 后期处理 | 与 `self-3y` 同款"录音笔底噪"，让玩家感到"这是从 3 年前的备忘录里偶然飘出来的一段笑" |

---

## 5. TTS 生产 SOP

### 5.1 工作流（每条语音）

```
[1] 拿到脚本最终稿（编剧签字）
        ↓
[2] 拆条 → 填入「拍摄场记表」（见 §5.5）
        ↓
[3] 套用对应角色 Voice 配置卡
        ↓
[4] 写 Prompt（含 SSML 标记）
        ↓
[5] 一键生成 3 条候选 → 听
        ↓
[6] 满意 → 进入 [7] / 不满意 → 调参/改 prompt 重生
        ↓
[7] 命名归档到 00_raw/tts/
        ↓
[8] 进入后期 (§9)
```

### 5.2 Prompt 模板（中文 TTS）

**通用结构**：

```
<voice_id>{角色 Voice ID}</voice_id>
<speed>{速度}</speed>
<emotion>{情绪标签}</emotion>
<prefix>{角色 prompt 前缀}</prefix>

[SSML 正文]
```

**SSML 关键标记速查**：

| 标记 | 作用 | 用例 |
|---|---|---|
| `<break time="800ms"/>` | 停顿 | 长句中喘气、"她说……（停）后来呢" |
| `<emphasis level="strong">字</emphasis>` | 重读 | 关键词强调 |
| `<prosody rate="0.8">慢句</prosody>` | 局部变速 | 醉酒段、临终段 |
| `<prosody pitch="-2st">低声</prosody>` | 局部降调 | 内心戏 |
| `<say-as interpret-as="characters">XYZ</say-as>` | 字母逐字读 | "AirPods" 等英文词 |

### 5.3 长戏（≥1 分钟）特殊处理

**问题**：TTS 一次生成超过 60 秒会出现：
1. 末段质感衰减
2. 情绪曲线扁平
3. 偶发吞字

**对策**：
1. **分段录制**：每段 ≤ 30 秒，按句号/段落切。
2. **段间留 200 ms 静音头尾**：方便后期对接。
3. **段间情绪渐变**：在 prompt 里手动写每段的 emotion 演进，例如妈妈 4'17" 长戏分 6 段：
   - 段 1: `gentle, hesitant`
   - 段 2: `gentle, nostalgic`
   - 段 3: `gentle, sad but holding back`
   - 段 4: `gentle, releasing`
   - 段 5: `gentle, peaceful`
   - 段 6: `gentle, tender, almost smiling`
4. **后期 crossfade 拼接**：每段间 50 ms 交叉淡化，听觉上无缝。

### 5.4 候选评审"三耳法则"

每条 TTS 出 3 条候选，必须用三种设备听过：

| 设备 | 检查重点 |
|---|---|
| AirPods Pro / 通用入耳式 | 主验收，模拟用户实际场景 |
| 头戴式监听耳机（如 ATH-M50x） | 听细节杂音、底噪、齿音 |
| 手机外放 | 兜底，确认离线场景下可懂 |

**通过标准**：3 副耳机里每副至少满意度 7/10 才入库。任意一副 ≤ 5/10 必须重做。

### 5.5 「拍摄场记表」模板（每条语音 1 行）

| ID | 关卡 | 时间码 | 角色 | 形态 | 文字稿 | 时长目标 | 情绪 | 出 prompt 人 | 评审人 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| 001 | lv11 | 2103 | mom | call | "今晚煮了你爱吃的排骨…" | 35s | gentle | A | B | ✅ |
| 002 | lv11 | 2115 | xiaomei | voice | "在吗" | 2s | cheerful | A | B | ✅ |
| ... | | | | | | | | | | |

> 该表用 Notion / 飞书表格维护，每条语音从立项到入库全周期可追。

---

## 6. 音乐生产 SOP（Suno）

### 6.1 工作流

```
[1] 编剧/导演给"音乐 brief"（场景+情绪+时长+段落结构）
        ↓
[2] 翻译成 Suno Prompt（英文，带 BPM/instrument/mood）
        ↓
[3] 一次跑 4 首候选（Suno 一次给 2 首，跑 2 轮）
        ↓
[4] 评审 → 选 1 首主稿 + 1 首备稿
        ↓
[5] 用 Suno "Extend"功能延长到目标时长
        ↓
[6] 用 Suno "Stem"功能（如开通）拆出干声/伴奏
        ↓
[7] 后期：手动剪辑、loop 点处理、淡入淡出
        ↓
[8] 导出 .wav 24-bit 入 00_raw/music/
```

### 6.2 Prompt 模板（《语音 99+》4 段曲）

#### M1 · 21:00 主题 / 全程低氛围 Loop

```
Style: lo-fi midnight bedroom, soft piano, light vinyl noise
Instruments: muted piano, subtle synth pad, occasional rain outside window
Tempo: 70 BPM
Mood: melancholy but warm, alone but not lonely
Structure: ambient loop, no drums, no clear melody peak
Duration: 90 seconds (extend to loopable)
Vocals: instrumental
```

**评审标准**：
- 必须能 loop 30 分钟不觉得"在重复"
- 不能有任何强旋律压过 TTS

#### M2 · 22:30 悬疑过门

```
Style: subtle ambient suspense, cinematic tension
Instruments: low drone, single hanging piano note (high register), sparse strings
Tempo: 60 BPM
Mood: unsettling but not horror, like a question mark
Structure: 30 seconds, builds slowly, ends on unresolved chord
Vocals: instrumental
```

#### M3 · 23:45 周南段落

```
Style: gentle indie folk, intimate acoustic
Instruments: fingerpicked nylon guitar, soft male humming (no lyrics, just "mmm"), light shaker
Tempo: 75 BPM
Mood: hopeful nostalgic, like reading an old letter
Structure: 120 seconds, gradual build, soft climax at 0:80, gentle outro
Vocals: wordless humming only, very subtle
```

#### M4 · 02:00 结尾

```
Style: warm cinematic piano, dawn moment
Instruments: solo piano, soft string pad entering at 0:30
Tempo: 50 BPM
Mood: like the moment you realize you survived a hard night
Structure: 90 seconds, single melody line, no drums, fade out
Vocals: instrumental
```

### 6.3 角色铃声生成（9 个）

每个角色一个独立铃声，玩家"听铃辨人"：

| 角色 | Suno Prompt | 时长 |
|---|---|---|
| mom | `老式诺基亚铃声风格, warm marimba, simple 4-note motif, 70bpm` | 4s loop |
| azhe | `cold minimal electronic ringtone, 2 notes only, 80bpm` | 4s loop |
| xiaomei | `cheerful pop ringtone, ukulele plucks, 4-bar phrase, 100bpm` | 4s loop |
| zhounan | `nostalgic 90s pager beep + soft chime, 70bpm` | 3s loop |
| hr | `corporate professional ringtone, neutral marimba, 90bpm` | 4s loop |
| anan | `bouncy J-pop intro, 2 seconds, 110bpm` | 3s loop |
| delivery | `standard Chinese delivery app push sound, 1 second` | 1s |
| unknown | `eerie low drone, no melody, 40bpm` | 4s loop |
| system | （不需要铃声，是震动） | — |

### 6.4 Suno 使用 Tips

1. **每次出双稿**：Suno 一次返回 2 首，第二首往往比第一首意外。
2. **用"Custom Mode"**：能精确填 Lyrics（留空）+ Style，避免随机。
3. **避免 vocal**：除非明确要 humming，否则 prompt 里加 `instrumental` `no vocals`。
4. **Extend 不超 3 次**：第 4 次开始质感会断层。
5. **Stem 拆轨非常省事**：拆出后可以单独调音量，比从 mix 抠声好太多。

---

## 7. 音效生产 SOP（ElevenLabs Sound Effects）

### 7.1 项目所需音效清单（约 60 个）

| 类别 | 数量 | 例 |
|---|---|---|
| **UI 音** | 12 | 微信咚、震动短/长、消息提示、来电铃响半秒、接通滴、挂断滴、撤回 swoosh、已读、未读、错误提示、菜单切换、确认 |
| **拟音** | 18 | 烧水壶哨响、水沸腾、键盘敲击 5 种节奏、外卖敲门 3 种、门关、钥匙、玻璃放下、椅子拉、纸张翻、笔写字、手机放在床上、手机震动桌面 |
| **角色化短音** | 8 | 阿哲消息撤回 swoosh、妈妈微信消息发出 woosh、群里@提示音、未知号码呼吸（轮询 3 段）、外卖结账提示、HR 邮件附件提示、电量 1% 警告、备忘录播放滴 |
| **过渡 / 转场** | 8 | 章节过渡轻 swell、时间流逝标记（22:00/23:00/00:00 等）、灯光熄灭暗示、心跳加速、深呼吸、玻璃碎一秒、雨势忽大、雨势忽小 |
| **结局专用** | 4 | 字幕浮现 chime、烧水壶滴一声、夜班车驶过、野猫叫一声 |
| **预留备用** | 10 | — |

### 7.2 ElevenLabs Sound Effects Prompt 模板

**通用结构**：

```
{动作或物体}, {距离/视角}, {环境}, {时长建议}
```

**示例**：

| 资产 ID | Prompt |
|---|---|
| `sfx_kettle_whistle` | `kettle whistling, close mic, small kitchen, 3 seconds, vintage` |
| `sfx_keyboard_typing` | `mechanical keyboard typing, soft, 5 seconds, intimate close mic` |
| `sfx_wechat_pop` | `short notification pop sound, soft, single high pitched 'tap', 0.5 seconds, original not WeChat` |
| `sfx_message_swoosh` | `quick whoosh of message sending, electronic, 0.3 seconds` |
| `sfx_door_knock_delivery` | `three knocks on apartment door, polite delivery, hallway echo, 2 seconds` |
| `sfx_glass_down` | `glass placed on wooden desk, soft clink, close mic, 1 second` |
| `sfx_phone_vibrate_table` | `phone vibrating on wooden bedside table, 2 seconds` |
| `sfx_cat_yowl_distant` | `single cat yowl in distance, alley, late night, 1.5 seconds` |
| `sfx_breath_unknown` | `human breathing through phone, slightly muffled, anonymous, 6 seconds` |

### 7.3 ElevenLabs SFX 使用 Tips

1. **每条 prompt 跑 3 次**：每次都不一样，多挑。
2. **时长别贪长**：>10s 容易"漂"。需要长效果就做 loop。
3. **避免品牌词**：不能写 `WeChat sound` `iPhone ringtone` `Apple notification`，直接侵权。改写为 `Chinese-style messaging app soft pop`。
4. **要用 mp3 时再转**：默认下载 mp3 192k，**生产中先转 wav 再处理**。

### 7.4 音效"哪类必须找真采样而非 AI"

| 音效 | 原因 | 采样源 |
|---|---|---|
| 30 秒以上的环境底噪 | AI 长 ambience 会"漂" | Freesound / Epidemic |
| 真实城市夜噪（远地铁、夜班车） | AI 太干净，缺真实空气感 | Freesound CC0 |
| 特定地域口音、街头叫卖 | AI 无地域性 | 自己录 |
| 情绪化的笑声、哭声、叹息 | AI SFX 还达不到 | TTS 角色化处理或真人录 |

---

## 8. 环境采样 SOP（Freesound / Epidemic Sound）

### 8.1 项目环境底噪清单

| ID | 用途 | 时长 | 描述 | 推荐源 |
|---|---|---|---|---|
| `amb_apartment_night_01` | 全程底噪 | 10 min loop | 合租屋夜晚，远处车声、冰箱嗡嗡、偶尔水管 | Freesound `apartment night ambience` |
| `amb_apartment_night_02` | 备用 | 5 min loop | 同上不同质感 | Freesound |
| `amb_bar_loud_01` | 室友安安电话背景 | 1 min loop | 拥挤酒吧，人声谈笑 + 电子音乐底 | Epidemic Sound |
| `amb_subway_distant` | 转场 | 30s | 远处地铁过站 | Freesound `subway distant` |
| `amb_kitchen_morning` | 结局 A | 1 min | 厨房环境，水龙头滴、冰箱嗡 | Freesound |
| `amb_rain_window` | M1 BGM 衬底 | 5 min loop | 窗外细雨 | Freesound `rain window soft` |
| `amb_late_night_bus` | 结局段 | 20s | 夜班公交驶过空街 | Epidemic Sound |
| `amb_dawn_birds` | 结局 D | 30s | 清晨鸟叫 | Freesound `dawn birds urban` |

### 8.2 Freesound 检索 SOP

1. 关键词搜索（英文优先）。
2. 过滤条件：
   - License: `Creative Commons 0` 优先；`Attribution` 次之；不要 `Attribution NonCommercial`（商业项目）。
   - Duration: 设最小值（避免短到没用）。
   - Sample rate: 44.1kHz / 48kHz。
3. 听 → 下载 .wav 原始版本（不要 mp3）。
4. **立刻**在 §11 版权登记表里登记：URL / 作者 ID / License / 下载日期。
5. 入 `00_raw/ambience/` 命名 `amb_xxx_freesoundXXXXX.wav`（保留 Freesound ID）。

### 8.3 Epidemic Sound 检索 SOP

1. Epidemic Sound 全部资源都是 Royalty-Free（订阅期内可商用）。
2. 直接下载 .wav 24-bit。
3. 在版权登记表登记 Track ID（Epidemic 提供）。
4. **退订后已下载的资产仍可继续使用**，但需保留下载凭证（截图存档）。

### 8.4 环境采样的"假性立体声"处理

许多 Freesound 资源是单声道。处理成立体声：

```bash
# REAPER / Audition 操作：
# 1. 复制单声道到 L、R 两轨
# 2. R 轨延迟 8–15 ms
# 3. R 轨高频 EQ 微调 ±1 dB
# → 听感即获得"环境的宽度"，但不影响 TTS 在中央的位置
```

**禁止**：用空间音效插件做 3D 定位——本作明确**不依赖空间音效定位**。

---

## 9. 后期统一处理 SOP

### 9.1 响度规范（关键）

| 资产类型 | 目标 LUFS（综合） | 峰值上限 |
|---|---|---|
| 角色语音（电话/微信语音） | -16 LUFS | -1 dBTP |
| 系统 TTS | -18 LUFS | -1 dBTP |
| 主题音乐（M1–M4） | -18 LUFS | -1 dBTP |
| 环境底噪 | -22 LUFS | -3 dBTP |
| 短音效（UI 类） | -14 LUFS（短促能听清） | -1 dBTP |

**为什么角色语音 -16 LUFS**：移动端 + 耳机场景，比影视的 -23 LUFS 响度高 7 dB，让玩家在嘈杂环境（公交、宿舍）也能听清。

**测量工具**：Youlean Loudness Meter 2 (Free)，REAPER 内置即可。

### 9.2 处理链（每条 TTS 标准链）

```
原始 TTS (.wav, 24-bit, 48kHz, 单声道)
      ↓
[1] iZotope RX · Mouth De-click（去 TTS 偶发咔嗒声）
      ↓
[2] iZotope RX · Voice De-noise（轻档 -6 dB，去合成底噪）
      ↓
[3] EQ · 高通滤波 80 Hz（去低频噪）
      ↓
[4] EQ · 角色化频段调整（按 §4 配置卡）
      ↓
[5] Compressor · 4:1, threshold -18 dB（控动态）
      ↓
[6] 加听筒效果（仅"电话/语音"形态，详见 §9.3）
      ↓
[7] Loudness Match · -16 LUFS
      ↓
[8] Limiter · ceiling -1 dBTP
      ↓
[9] 导出 .wav 16-bit 48kHz → 01_processed/tts/
```

### 9.3 「听筒效果」预设

模拟手机听筒/微信语音的窄频段感：

```
EQ:
  HPF 300 Hz, 24 dB/oct
  LPF 3.4 kHz, 24 dB/oct
  +1 dB at 1.5 kHz（保留人声清晰度）

Saturation:
  Soft tape saturation, 5–8% drive

Noise:
  叠极轻底噪（-50 dB），可用 ambience 库 phone_noise_floor.wav
```

> **例外**：`mom` 第 16 条 4 分钟长戏 **不加听筒效果** —— 这条是微信语音"完整音质版"，是设计意图。

### 9.4 音乐处理链

```
Suno 原始 (.wav, 立体声, 48kHz)
      ↓
[1] Trim 头尾静音
      ↓
[2] Loop 点设计（找节拍重音对齐）
      ↓
[3] Crossfade 50 ms（loop 接缝）
      ↓
[4] EQ · 削掉 200–500 Hz 的"AI 浊感"（-2 dB）
      ↓
[5] Stereo Width · 控制在 70%（避免吃掉中央 TTS）
      ↓
[6] Loudness Match · -18 LUFS
      ↓
[7] Limiter · -1 dBTP
      ↓
[8] 导出 .wav → 01_processed/music/
```

### 9.5 环境底噪处理链

```
Freesound 原始 (.wav)
      ↓
[1] Trim 不需要的段
      ↓
[2] iZotope RX · 去掉突兀的"事件"（突然的喊叫、关门）
      ↓
[3] HPF 60 Hz（去隆隆声）
      ↓
[4] LPF 12 kHz（去高频噪）
      ↓
[5] Loop 点设计（必须找几乎静止的 1 秒做接缝）
      ↓
[6] Crossfade 200 ms
      ↓
[7] Loudness Match · -22 LUFS
      ↓
[8] 假性立体声化（§8.4）
      ↓
[9] 导出 .wav → 01_processed/ambience/
```

### 9.6 批处理脚本（FFmpeg 示例）

格式批量转换 + 响度归一化：

```bash
# 把 01_processed 下所有 wav 转成最终 ogg + 响度归一化到 -16 LUFS
for f in 01_processed/tts/*.wav; do
  ffmpeg -i "$f" \
    -af "loudnorm=I=-16:TP=-1:LRA=11" \
    -c:a libvorbis -q:a 5 \
    "02_final/tts/$(basename "${f%.wav}.ogg")"
done
```

---

## 10. QA 验收清单（每批资产强制走一遍）

### 10.1 自检清单（执行人）

每条资产入 `01_processed/` 前自查：

- [ ] 文件命名符合 §3.2 规范
- [ ] 采样率 = 48 kHz
- [ ] 单/立体声符合 §3.3 规范
- [ ] 响度在 §9.1 目标范围内（±1 LUFS）
- [ ] 峰值不超过 -1 dBTP
- [ ] 无明显爆音、咔嗒、底噪
- [ ] 时长与场记表目标值偏差 ≤ 10%

### 10.2 评审清单（评审人，不同人）

每批 TTS 走"三耳法则"（§5.4）：

- [ ] AirPods Pro 听 → 满意度 ≥ 7/10
- [ ] 监听耳机听 → 满意度 ≥ 7/10
- [ ] 手机外放听 → 可懂 ≥ 7/10
- [ ] 角色辨识度 → 与配置卡一致
- [ ] 情绪到位度 → 与脚本意图一致

### 10.3 上下文听感测试（关键）

**单条满意 ≠ 全场景满意**。每完成一个时间段（如 21:00–22:00 这一小时）：

- [ ] 把这一小时所有资产按时间轴拼起来，戴耳机完整听一遍
- [ ] 检查：音量是否平稳？环境底噪有没有突然断层？两条 TTS 之间的"沉默"是否自然？
- [ ] 至少 3 名团队成员独立听完，给整体评分（1–10）
- [ ] 平均分 ≥ 7 才放行

### 10.4 玩家盲测（最终验收前）

- 招 5 位 22–25 岁女性玩家
- **不告知任何剧情**，让她们戴耳机黑屏完整玩一遍
- 关键观测点：
  - 哪条 TTS 让她们出戏（皱眉/摘耳机）→ 重做
  - 哪条让她们流泪/微笑/屏息 → 标记为"金条"，备份保留
  - 哪个角色被说"听不出是谁" → 配置卡需调整辨识度
- 内测报告归档到 `03_qa_reports/`

---

## 11. 版权追踪与归档

### 11.1 强制原则

> **任何一条入库资产，在它被生成/下载的当天，必须登记。**
> **当天没登记的，第二天起视为不可用，必须返工补登。**

### 11.2 版权登记表模板（Notion / 飞书表格）

| 资产 ID | 类型 | 来源工具/平台 | URL/Track ID/Voice ID | License | 创建/下载日期 | 创建人 | 商用证明位置 | 备注 |
|---|---|---|---|---|---|---|---|---|
| `lv11_2103_mom_call_01` | TTS | MiniMax Speech 02 | voice: Warm_Auntie_v3 | MiniMax 商用许可 | 2026-05-15 | 张三 | `99_legal/minimax_terms_2026.pdf` | — |
| `amb_apartment_night_01` | ambience | Freesound | freesound.org/s/123456/ | CC0 | 2026-05-13 | 李四 | (CC0 无需) | 作者: user_xxx |
| `amb_bar_loud_01` | ambience | Epidemic Sound | track id: ES_8472993 | Epidemic 订阅 | 2026-05-14 | 李四 | `99_legal/epidemic_invoice_202605.pdf` | 订阅期内 |
| `m1_main_theme` | music | Suno V4 | song id: suno_xxx | Suno Pro 商用 | 2026-05-16 | 王五 | `99_legal/suno_pro_2026.pdf` | — |
| `sfx_wechat_pop` | sfx | ElevenLabs SFX | (SFX 不返回 ID，存 prompt) | ElevenLabs Creator 商用 | 2026-05-15 | 王五 | `99_legal/elevenlabs_terms.pdf` | prompt 存留 |

### 11.3 各 AI 平台商用授权要点（截至 2026-05）

> ⚠️ **每次开新项目前必须重新核对最新条款**。AI 平台条款变化频繁。

| 平台 | 商用许可 | 特殊条件 |
|---|---|---|
| **MiniMax Speech** | ✅ 包含在 API 服务中 | 不得用于生成深度伪造、政治敏感内容 |
| **字节豆包 Voice** | ✅ 企业 API 包含商用 | 个人版可能受限，必须开企业账户 |
| **ElevenLabs** | ✅ Creator 及以上套餐 | Free 套餐**不能商用**；TTS 需注明（部分场景） |
| **Suno** | ✅ Pro 及以上 | Free 不可商用；保留生成时的订阅状态截图 |
| **Freesound** | ⚠️ 看每条 license | CC0 自由用；CC-BY 必须署名；CC-NC 不可商用 |
| **Epidemic Sound** | ✅ 订阅期内全库商用 | 退订后已下载资产可继续用，必须存订阅凭证 |

### 11.4 归档与备份

- **Git LFS**：所有 `01_processed/` 与 `02_final/` 资产入库。
- **OSS 双备份**：每周自动同步到阿里云 OSS（主）+ AWS S3（备），保留 6 个月版本。
- **冷备**：项目结项时，全套 raw + processed + final + 法务文件刻盘归档（蓝光 50 GB ≈ ¥30 一张）。

---

## 12. 附录

### 12.1 命名词典

| 字段 | 缩写 |
|---|---|
| 关卡 | `lv` |
| TTS 角色语音 | `tts` |
| 音乐 | `mus` / `m1`/`m2`/`m3`/`m4` |
| 短音效 | `sfx` |
| 环境底噪 | `amb` |
| 来电 | `call` |
| 微信语音 | `voice` |
| 微信文字 | `text` |
| 系统提示 | `sys` |

### 12.2 项目专用术语

| 术语 | 含义 |
|---|---|
| **金条** | 玩家盲测中触发明显情感反应的语音条目，优先保留 |
| **听筒效果** | §9.3 的 EQ + saturation 处理预设 |
| **三耳法则** | §5.4 的三种设备评审标准 |
| **拍摄场记表** | §5.5 的全条目追踪表 |

### 12.3 突发情况预案

| 情况 | 处理 |
|---|---|
| MiniMax 临时服务中断 | 切豆包 Voice，按角色配置卡的"备用方案"行动 |
| ElevenLabs SFX 月度 credit 用完 | 走阿里通义万相音效；或下月重做 |
| Suno 出图风格全部不满意 | 用 Udio v2 重跑同一 prompt |
| Freesound 没有合适素材 | Epidemic Sound；再不行**临时找 1 名收音师外采**（预算预留 ¥2000） |
| 玩家盲测某条全员差评 | 优先级最高，必须返工，72 小时内重做 + 复测 |

### 12.4 工时估算（参考，单人执行）

| 资产类型 | 单条耗时 | 总耗时 |
|---|---|---|
| 短 TTS（≤ 10 s） | 5 min（含 3 候选评审） | ~3 h（35 条） |
| 长 TTS（≥ 1 min） | 30 min（分段+拼接） | ~2 h（4 条） |
| 单段音乐（含 extend） | 40 min | ~3 h（4 段） |
| 单条音效 | 3 min | ~3 h（60 条） |
| 单段环境采样（含处理） | 20 min | ~3 h（8 段） |
| 后期统一处理 | 5 min/条 | ~6 h |
| QA 与盲测 | — | ~12 h |
| **合计** | | **~32 工时**（4 个工作日） |

> 实际项目预留 **2 倍**时间用于反复打磨。

---

## 13. 启动检查表（Day 0 之前）

- [ ] 所有 §2.2 账号已开通、付费、API key 已存安全位置（团队密码管理器）
- [ ] §3 文件夹结构已建好，Git LFS 已启用
- [ ] §4 角色 Voice 配置卡已在 Notion 立表，每个 voice id 跑过 1 条试音确认可用
- [ ] §5.5 拍摄场记表已建好，所有条目预填
- [ ] §11.2 版权登记表已建好
- [ ] 团队听过 1 个完整 reference 项目（推荐：《Mountain》《Florence》《Lifeline》音频部分）
- [ ] 玩家盲测候选 5 人已联系并约好测试日期

---

**文档状态**：v1.0 · 2026-05-13 · 待团队评审
**维护人**：项目主控
**下次修订**：每完成一个项目后，回看实际数据更新本 SOP
