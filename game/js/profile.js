// profile.js — 行为画像追踪器（avoidance / engagement / nostalgia）

class ProfileTracker {
  constructor() {
    this.scores = { avoidance: 0, engagement: 0, nostalgia: 0 };
  }

  add(effects) {
    if (!effects) return;
    for (const k of ['avoidance', 'engagement', 'nostalgia']) {
      if (effects[k]) this.scores[k] += effects[k];
    }
  }

  // 漏接电话
  onMissedCall()   { this.add({ avoidance: 2 }); }
  // 单点回"嗯"
  onSimpleReply()  { this.add({ avoidance: 1 }); }
  // 双指上滑已读不回
  onReadNoReply()  { this.add({ avoidance: 2 }); }
  // 进入细回复
  onDetailReply()  { this.add({ engagement: 2 }); }
  // 细回复选"主动追问"（engagement 方向）
  onEngage()       { this.add({ engagement: 2 }); }
  // 细回复选"分享自己"
  onShare()        { this.add({ engagement: 1, nostalgia: 1 }); }
  // 反复重听同一条
  onReplay()       { this.add({ nostalgia: 2 }); }
  // 听完长语音未回应
  onListenNoReact(){ this.add({ avoidance: 1, nostalgia: 1 }); }

  // 获取最终画像标签
  get label() {
    const s = this.scores;
    if (s.engagement >= s.avoidance && s.engagement >= s.nostalgia) return 'engagement';
    if (s.nostalgia >= s.avoidance) return 'nostalgia';
    return 'avoidance';
  }
}
