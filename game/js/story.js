// story.js — 《林夏》全部16条消息数据

const A    = '../audio/00_raw';
const TDIR = `${A}/tts`;
const MUS  = `${A}/music`;
const SFX  = `${A}/sfx`;
const AMB  = `${A}/ambience`;

// 游戏时间压缩比：5小时 → 60分钟（实际秒）
// 1 游戏分钟 = 12 实际秒
// triggerAt = (游戏时间 - 21:00) 的分钟数 × 12
function gt(hh, mm) {
  const gameMin = (hh < 21 ? hh + 24 : hh) * 60 + mm - 21 * 60;
  return gameMin * 12; // 实际秒
}

const MESSAGES = [

  // ── 01 · 21:03 · 妈妈 · 电话 ──────────────────────────────────
  {
    id: 1, gameTime: '21:03', triggerAt: gt(21, 3),
    type: 'call',
    sender: 'mom', senderName: '妈妈',
    ringtone: `${MUS}/lv11_ring_mom_v1.wav`,
    ringDuration: 28,
    audio: [`${TDIR}/lv11_2103_mom_call_01_wav_v1.wav`],
    note: '今晚煮了你爱吃的排骨',
    stateOnAnswer: { MOM_LINK: true },
    profileOnMiss:  { avoidance: 2 },
    profileOnAnswer:{ engagement: 1 },
  },

  // ── 02 · 21:15 · 小美 · 微信语音×3（教学关）──────────────────
  {
    id: 2, gameTime: '21:15', triggerAt: gt(21, 15),
    type: 'wechat_voice',
    sender: 'xiaomei', senderName: '小美',
    audio: [
      `${TDIR}/lv11_2115_xiaomei_voice_01_wav_v1.wav`,
      `${TDIR}/lv11_2115_xiaomei_voice_02_wav_v1.wav`,
      `${TDIR}/lv11_2115_xiaomei_voice_03_wav_v1.wav`,
    ],
    note: '你被甩了我都听说了，明天喝酒',
    isTutorial: true,
    detailReplies: [
      { label: '好啊，明天不见不散。', dir: 'left',  profile: { engagement: 1 } },
      { label: '我不太想出门……',       dir: 'right', profile: { nostalgia: 1 } },
      { label: '你先去，我再说。',       dir: 'up',   profile: { avoidance: 1 } },
      { label: '（沉默）',               dir: 'down', isSilence: true, profile: { avoidance: 2 } },
    ],
    standardReply: '好啊。',
    profileOnRead:  { engagement: 1 },
    profileOnAvoid: { avoidance: 1 },
  },

  // ── 03 · 21:20 · 外卖小哥 · 电话 ─────────────────────────────
  {
    id: 3, gameTime: '21:20', triggerAt: gt(21, 20),
    type: 'call',
    sender: 'delivery', senderName: '外卖小哥',
    ringtone: `${MUS}/lv11_ring_delivery_v1.wav`,
    ringDuration: 20,
    audio: [`${TDIR}/lv11_2120_delivery_call_01_wav_v1.wav`],
    note: '你好，你的麻辣烫到了',
    profileOnMiss:  { avoidance: 1 },
    profileOnAnswer:{ engagement: 1 },
  },

  // ── 04 · 21:30 · 阿哲 · 微信语音（第一刀）────────────────────
  {
    id: 4, gameTime: '21:30', triggerAt: gt(21, 30),
    type: 'wechat_voice',
    sender: 'azhe', senderName: '阿哲',
    audio: [`${TDIR}/lv11_2130_azhe_voice_01_wav_v1.wav`],
    note: 'AirPods落你那了，方便寄一下吗',
    detailReplies: [
      { label: '好，明天寄。',         dir: 'left',  state: { HE_BACK: false }, profile: { engagement: 1 } },
      { label: '你怎么不自己来拿。',   dir: 'right', state: {}, profile: { engagement: 2 } },
      { label: '你那边……都好吗。',     dir: 'up',    state: {}, profile: { engagement: 2 } },
      { label: '（什么都不说）',        dir: 'down',  isSilence: true, state: { HE_BACK: null }, profile: { avoidance: 2 } },
    ],
    standardReply: '好，明天寄给你。',
    stateOnStdReply: { HE_BACK: false },
    // 10分钟后阿哲撤回消息（如果玩家未回复）
    followUp: { delayMin: 10, action: 'azhe_recall' },
    profileOnRead:  { engagement: 0 },
    profileOnAvoid: { avoidance: 1 },
  },

  // ── 05 · 21:45 · HR王姐 · 微信语音 ───────────────────────────
  {
    id: 5, gameTime: '21:45', triggerAt: gt(21, 45),
    type: 'wechat_voice',
    sender: 'hr', senderName: 'HR王姐',
    audio: [`${TDIR}/lv11_2145_hr_voice_01_wav_v1.wav`],
    note: '离职流程周三前办完哈',
    detailReplies: [
      { label: '好的，我知道了。谢谢王姐。', dir: 'left',  profile: { engagement: 1 } },
      { label: '王姐，有什么建议吗？',        dir: 'right', profile: { engagement: 2 } },
      { label: '……谢谢你。',                  dir: 'up',   profile: { nostalgia: 1 } },
      { label: '（不回复）',                   dir: 'down', isSilence: true, profile: { avoidance: 1 } },
    ],
    standardReply: '好的，谢谢王姐。',
    profileOnRead:  { engagement: 1 },
    profileOnAvoid: { avoidance: 1 },
  },

  // ── 06 · 22:00 · 安安 · 微信语音（酒吧背景）─────────────────
  {
    id: 6, gameTime: '22:00', triggerAt: gt(22, 0),
    type: 'wechat_voice',
    sender: 'anan', senderName: '安安',
    audio: [`${TDIR}/lv11_2200_anan_voice_01_wav_v1.wav`],
    note: '我在helens！要不要过来！',
    bgUnder: `${AMB}/amb_bar_loud_01_v1.wav`,  // 酒吧底噪混入
    detailReplies: [
      { label: '我今晚不方便，你们玩好啊。', dir: 'left',  profile: { avoidance: 1 } },
      { label: '在哪儿啊？我……看看吧。',     dir: 'right', profile: { engagement: 1 } },
      { label: '你喝了多少了哈哈。',          dir: 'up',   profile: { engagement: 1 } },
      { label: '（不回复）',                   dir: 'down', isSilence: true, profile: { avoidance: 2 } },
    ],
    standardReply: '不了，你们玩好～',
    profileOnRead:  { engagement: 0 },
    profileOnAvoid: { avoidance: 1 },
  },

  // ── 07 · 22:15 · 大学寝室群 · 5条语音 ────────────────────────
  {
    id: 7, gameTime: '22:15', triggerAt: gt(22, 15),
    type: 'wechat_voice',
    sender: 'dorm', senderName: '我们寝室的（4人群）',
    audio: [
      `${TDIR}/lv11_2215_dorm_a_voice_01_wav_v1.wav`,
      `${TDIR}/lv11_2215_dorm_a_voice_02_wav_v1.wav`,
      `${TDIR}/lv11_2215_dorm_b_voice_01_wav_v1.wav`,
      `${TDIR}/lv11_2215_dorm_b_voice_02_wav_v1.wav`,
      `${TDIR}/lv11_2215_dorm_c_voice_01_wav_v1.wav`,
    ],
    note: '室友A升职了，最后她@你',
    isGroup: true,
    detailReplies: [
      { label: '恭喜恭喜！',           dir: 'left',  state: { GROUP_REPLY: true }, profile: { engagement: 1 } },
      { label: '哇，快讲讲！',          dir: 'right', state: { GROUP_REPLY: true }, profile: { engagement: 2 } },
      { label: '最近有点忙，你们聊～', dir: 'up',    profile: { avoidance: 1 } },
      { label: '（沉默）',              dir: 'down',  isSilence: true, profile: { avoidance: 2 } },
    ],
    standardReply: '恭喜！',
    stateOnStdReply: { GROUP_REPLY: true },
    profileOnRepeat: { nostalgia: 2 },
    profileOnRead:   { engagement: 0 },
    profileOnAvoid:  { avoidance: 1 },
  },

  // ── 08 · 22:30 · 未知号码 · 电话（悬疑钩子）─────────────────
  {
    id: 8, gameTime: '22:30', triggerAt: gt(22, 30),
    type: 'call',
    sender: 'unknown', senderName: '未知号码',
    ringtone: `${MUS}/lv11_ring_unknown_v1.wav`,
    ringDuration: 20,
    audio: [`${SFX}/sfx_breathing_unknown_v1.wav`],
    note: '接通后只有呼吸声，6秒挂断',
    autoHangup: 6,     // 接通后自动挂断秒数
    sfxAfter: `${SFX}/sfx_heartbeat_fast_v1.wav`,
    profileOnMiss:  { avoidance: 1 },
    profileOnAnswer:{ nostalgia: 1 },
  },

  // ── 09 · 22:45 · 小美醉语音 · 4段（秘密揭晓）───────────────
  {
    id: 9, gameTime: '22:45', triggerAt: gt(22, 45),
    type: 'wechat_voice',
    sender: 'xiaomei', senderName: '小美',
    audio: [
      `${TDIR}/lv11_2245_xiaomei_voice_01_seg1_wav_v1.wav`,
      `${TDIR}/lv11_2245_xiaomei_voice_01_seg2_wav_v1.wav`,
      `${TDIR}/lv11_2245_xiaomei_voice_01_seg3_wav_v1.wav`,
      `${TDIR}/lv11_2245_xiaomei_voice_01_seg4_wav_v1.wav`,
    ],
    note: '阿哲大三追过我，我没答应他',
    isDrunk: true,
    bgm: `${MUS}/lv11_bgm_m2_suspense_v1.wav`,  // 悬疑BGM
    detailReplies: [
      { label: '我知道了。',               dir: 'left',  profile: { avoidance: 1 } },
      { label: '你……为什么现在才说。',     dir: 'right', profile: { engagement: 2 } },
      { label: '小美，你还好吗。',          dir: 'up',   profile: { engagement: 2 } },
      { label: '（什么都不说）',            dir: 'down', isSilence: true, profile: { avoidance: 2, nostalgia: 1 } },
    ],
    standardReply: '我知道了。',
    // 5秒后消息被撤回
    followUp: { delaySec: 5, action: 'xiaomei_recall' },
    profileOnRepeat: { nostalgia: 2 },
    profileOnAvoid:  { avoidance: 1, nostalgia: 1 },
  },

  // ── 10 · 23:00 · 妈妈 · 微信文字 ─────────────────────────────
  {
    id: 10, gameTime: '23:00', triggerAt: gt(23, 0),
    type: 'wechat_text',
    sender: 'mom', senderName: '妈妈',
    text: '睡了吗？',
    note: '三个字，最痛',
    detailReplies: [
      { label: '嗯，要睡了。',                 dir: 'left',  state: { MOM_LINK: true }, profile: { avoidance: 1 } },
      { label: '没有，怎么了。',                dir: 'right', state: { MOM_LINK: true }, profile: { engagement: 1 } },
      { label: '妈，你在吗，我想打电话。',     dir: 'up',    state: { MOM_LINK: true }, profile: { engagement: 2 } },
      { label: '（不回复）',                    dir: 'down', isSilence: true, profile: { avoidance: 2 } },
    ],
    standardReply: '嗯。',
    stateOnStdReply: { MOM_LINK: true },
    profileOnRead:  { nostalgia: 1 },
    profileOnAvoid: { avoidance: 1 },
  },

  // ── 11 · 23:15 · 阿哲 · 电话（关键分支）─────────────────────
  {
    id: 11, gameTime: '23:15', triggerAt: gt(23, 15),
    type: 'call',
    sender: 'azhe', senderName: '阿哲',
    ringtone: `${MUS}/lv11_ring_azhe_v1.wav`,
    ringDuration: 30,
    audio: [`${TDIR}/lv11_2315_azhe_call_01_wav_v1.wav`],
    note: '我能过去拿吗？就5分钟',
    // 通话中的选择（接通后听完再做）
    inCallChoices: [
      { label: '不方便，明天吧。',       dir: 'left',  state: { HE_BACK: false } },
      { label: '可以，但只有5分钟。',    dir: 'right', state: { HE_BACK: true  } },
      { label: '（不说话，挂断）',        dir: 'down', isSilence: true, state: { HE_BACK: false } },
    ],
    profileOnMiss:  { avoidance: 2 },
    profileOnAnswer:{ engagement: 1 },
  },

  // ── 12 · 23:30 · 周南 · 微信语音（悬疑揭晓）────────────────
  {
    id: 12, gameTime: '23:30', triggerAt: gt(23, 30),
    type: 'wechat_voice',
    sender: 'zhounan', senderName: '周南',
    audio: [`${TDIR}/lv11_2330_zhounan_voice_01_wav_v1.wav`],
    note: '林夏，是我，周南。初三坐你后桌那个',
    detailReplies: [
      { label: '嗯……你好。',                   dir: 'left',  state: { ZHOUNAN_DEPTH: 1 }, profile: { nostalgia: 1 } },
      { label: '周南！你还记得我啊！',           dir: 'right', state: { ZHOUNAN_DEPTH: 1 }, profile: { engagement: 2, nostalgia: 1 } },
      { label: '你是……初三坐我后桌那个……？',   dir: 'up',    state: { ZHOUNAN_DEPTH: 1 }, profile: { nostalgia: 2 } },
      { label: '（不回复）',                     dir: 'down', isSilence: true },
    ],
    standardReply: '嗯……好久不见。',
    stateOnStdReply: { ZHOUNAN_DEPTH: 1 },
    profileOnRead:  { nostalgia: 1 },
    profileOnAvoid: { avoidance: 1 },
  },

  // ── 13 · 23:45 · 周南 · 4条语音（十年故事）─────────────────
  {
    id: 13, gameTime: '23:45', triggerAt: gt(23, 45),
    type: 'wechat_voice',
    sender: 'zhounan', senderName: '周南',
    audio: [
      `${TDIR}/lv11_2345_zhounan_voice_01_wav_v1.wav`,
      `${TDIR}/lv11_2345_zhounan_voice_02_wav_v1.wav`,
      `${TDIR}/lv11_2345_zhounan_voice_03_wav_v1.wav`,
      `${TDIR}/lv11_2345_zhounan_voice_04_wav_v1.wav`,
    ],
    note: '高考、复读、二本、回老家……今天我生日',
    bgm: `${MUS}/lv11_bgm_m3_zhounan_v1.wav`,
    detailReplies: [
      { label: '你讲了好多。我都听了。',        dir: 'left',  state: { ZHOUNAN_DEPTH_ADD: 1 }, profile: { engagement: 2, nostalgia: 1 } },
      { label: '你一个人在北京，还好吗？',      dir: 'right', state: { ZHOUNAN_DEPTH_ADD: 1 }, profile: { engagement: 2 } },
      { label: '……生日快乐。',                  dir: 'up',    state: { ZHOUNAN_DEPTH_ADD: 1, ZHOUNAN_SHARE: true }, profile: { nostalgia: 2, engagement: 1 } },
      { label: '（沉默）',                       dir: 'down', isSilence: true, profile: { nostalgia: 1, avoidance: 1 } },
    ],
    standardReply: '……谢谢你告诉我。',
    stateOnStdReply: { ZHOUNAN_DEPTH_ADD: 1 },
    profileOnRepeat: { nostalgia: 2 },
    profileOnAvoid:  { nostalgia: 1, avoidance: 1 },
  },

  // ── 14 · 00:15 · 妈妈 · 电话（第二次）─────────────────────
  {
    id: 14, gameTime: '00:15', triggerAt: gt(0, 15),
    type: 'call',
    sender: 'mom', senderName: '妈妈',
    ringtone: `${MUS}/lv11_ring_mom_v1.wav`,
    ringDuration: 30,
    audio: [`${TDIR}/lv11_0015_mom_call_01_wav_v1.wav`],
    note: '夏夏，你不接电话我有点担心',
    stateOnAnswer: { MOM_LINK: true },
    profileOnMiss:  { avoidance: 2 },
    profileOnAnswer:{ engagement: 2 },
  },

  // ── 15 · 00:30 · 自己 · 时光胶囊（系统通知）────────────────
  {
    id: 15, gameTime: '00:30', triggerAt: gt(0, 30),
    type: 'system_notification',
    sender: 'self', senderName: '时光胶囊',
    text: '3年前的今晚，你给自己录过一段备忘录。是否播放？',
    systemAudio: `${TDIR}/lv11_sys_memo_01_wav_v1.wav`,
    audioByProfile: {
      avoidance:  `${TDIR}/lv11_0030_self3y_voice_02_wav_v1.wav`,
      engagement: `${TDIR}/lv11_0030_self3y_voice_01_wav_v1.wav`,
      nostalgia:  `${TDIR}/lv11_0030_self3y_voice_03_wav_v1.wav`,
    },
    note: 'self-3y，由PROFILE决定版本',
    stateOnPlay: { SELF_RECORD: true },
    profileOnPlay: { nostalgia: 2 },
    profileOnSkip: { avoidance: 2 },
  },

  // ── 16 · 02:00 · 妈妈 · 长语音4分17秒（结局）──────────────
  {
    id: 16, gameTime: '02:00', triggerAt: gt(2, 0),
    type: 'wechat_voice',
    sender: 'mom', senderName: '妈妈',
    audio: [
      `${TDIR}/lv11_0200_mom_voice_01_seg1_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg2_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg3_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg4_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg5_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg6_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg7_wav_v1.wav`,
      `${TDIR}/lv11_0200_mom_voice_01_seg8_wav_v1.wav`,
    ],
    note: '妈妈讲她24岁那年，结局起点',
    bgm: `${MUS}/lv11_bgm_m4_ending_v1.wav`,
    sfxAfter: [
      `${SFX}/sfx_night_bus_v1.wav`,
      `${SFX}/sfx_cat_yowl_v1.wav`,
    ],
    isEnding: true,
    requiresMomLink: true,  // 必须 MOM_LINK=true 才自动播放
  },
];

// 角色→铃声映射（用于收件箱读出）
const SENDERS = {
  mom:      { name: '妈妈',       ringtone: `${MUS}/lv11_ring_mom_v1.wav` },
  azhe:     { name: '阿哲',       ringtone: `${MUS}/lv11_ring_azhe_v1.wav` },
  xiaomei:  { name: '小美',       ringtone: `${MUS}/lv11_ring_xiaomei_v1.wav` },
  delivery: { name: '外卖小哥',   ringtone: `${MUS}/lv11_ring_delivery_v1.wav` },
  hr:       { name: 'HR王姐',     ringtone: `${MUS}/lv11_ring_hr_v1.wav` },
  anan:     { name: '安安',       ringtone: `${MUS}/lv11_ring_anan_v1.wav` },
  dorm:     { name: '寝室群',     ringtone: `${MUS}/lv11_ring_dorm_group_v1.wav` },
  unknown:  { name: '未知号码',   ringtone: `${MUS}/lv11_ring_unknown_v1.wav` },
  zhounan:  { name: '周南',       ringtone: `${MUS}/lv11_ring_zhounan_v1.wav` },
  self:     { name: '时光胶囊',   ringtone: null },
};

const SFX_UI = {
  wechat_msg:  `${SFX}/sfx_deep_breath_v1.wav`,   // 微信消息提示（用sfx模拟）
  keyboard:    `${SFX}/sfx_keyboard_slow_v1.wav`,
  chime:       `${SFX}/sfx_ending_chime_v1.wav`,
  transition:  `${SFX}/sfx_transition_chapter_v1.wav`,
};

const AMBIENCE_DEFAULT = `${AMB}/amb_apartment_night_01_v1.wav`;
const AMBIENCE_RAIN    = `${AMB}/amb_rain_window_01_v1.wav`;
