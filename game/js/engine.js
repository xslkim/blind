// engine.js — 游戏状态机

class GameEngine {
  constructor() {
    // 游戏状态
    this.state = 'idle';  // idle→playing→ringing→in_call→msg_incoming→msg_playing→await_reply→detail_reply→inbox→ending

    // 剧情变量
    this.vars = {
      MOM_LINK: false,
      HE_BACK: null,      // null=未定, true=来了, false=拒了
      GROUP_REPLY: false,
      ZHOUNAN_DEPTH: 0,   // 0-3
      ZHOUNAN_SHARE: false,
      SELF_RECORD: false,
      UNREAD: 0,          // 未读消息计数
    };

    this.profile = new ProfileTracker();

    // 消息状态
    this.msgState = {};   // msgId → 'unread'|'read'|'replied'|'missed'
    this.replayCount = {};// msgId → 重听次数

    // 当前处理的消息
    this.currentMsg = null;
    this.currentChoices = null;   // 细回复选项列表
    this.awaitingChoice = false;

    // 定时器
    this._timers = [];
    this._ringTimer = null;
    this._startTime = null;

    // 手势引用
    this.gest = null;

    // 特殊事件追踪
    this._azheFollowUpDone = false;
    this._xiaomeiRecallDone = false;
    this._batteryWarned = false;
    this._doorbell = false;
  }

  // ══════════════════════════════════════════
  //   初始化
  // ══════════════════════════════════════════
  init(gestureDetector) {
    this.gest = gestureDetector;
    this._bindGestures();
  }

  _bindGestures() {
    const G = this.gest;
    G.on('singletap',    () => this._onSingleTap());
    G.on('doubletap',    () => this._onDoubleTap());
    G.on('longpress1s',  () => this._onLongPress1s());
    G.on('longpress5s',  () => this._onLongPress5s());
    G.on('swipe_left',   () => this._onSwipe('left'));
    G.on('swipe_right',  () => this._onSwipe('right'));
    G.on('swipe_up',     () => this._onSwipe('up'));
    G.on('swipe_down',   () => this._onSwipe('down'));
  }

  // ══════════════════════════════════════════
  //   游戏开始
  // ══════════════════════════════════════════
  async start() {
    this._startTime = Date.now();
    this.state = 'playing';

    // 启动环境底噪
    await Snd.startAmbience(AMBIENCE_DEFAULT, { vol: 0.2 });

    // 调度所有消息
    for (const msg of MESSAGES) {
      this._schedule(msg.triggerAt * 1000, () => this._triggerMessage(msg));
    }

    // 调度特殊事件
    this._scheduleSpecialEvents();

    // 02:05 兜底：确保结局被触发
    const endingDelay = (gt(2, 5)) * 1000;
    this._schedule(endingDelay, () => {
      if (!this._endingTriggered) this.triggerFinalEnding();
    });

    // 夜间启动彩蛋
    const hour = new Date().getHours();
    if (hour >= 22 || hour < 4) {
      await sleep(2000);
      await TTS.speak('你也还醒着啊。', { rate: 0.8, volume: 0.6 });
    }

    // 开始主BGM
    await sleep(3000);
    Snd.startBGM(`${MUS}/lv11_bgm_m1_main_loop_v1.wav`, { vol: 0.3 });
  }

  _scheduleSpecialEvents() {
    // 阿哲撤回（消息4未回复时，10游戏分钟后）
    this._schedule(gt(21, 40) * 1000, () => {
      if (!this._azheFollowUpDone && this.msgState[4] !== 'replied') {
        this._azheFollowUpDone = true;
        Snd.startTyping();
        sleep(8000).then(() => {
          Snd.stopTyping();
          TTS.speak('阿哲撤回了一条消息。', { rate: 0.85, volume: 0.7 });
        });
      }
    });

    // HE_BACK 为 true 时，门铃音效（23:30左右）
    this._schedule(gt(23, 28) * 1000, () => {
      if (this.vars.HE_BACK === true && !this._doorbell) {
        this._doorbell = true;
        Snd.playFX ? null : null;
        Snd.playVoice([`${SFX}/sfx_door_knock_gentle_v1.wav`]);
        Haptic.ring();
      }
    });

    // 电量1%警告（结局D触发条件之一）
    this._schedule(gt(1, 0) * 1000, () => {
      if (!this._batteryWarned) {
        this._batteryWarned = true;
        const unread = Object.values(this.msgState).filter(s => s === 'unread').length
                     + (Object.keys(this.msgState).length === 0 ? MESSAGES.length : 0);
        if (this.vars.UNREAD >= 8) {
          Snd.playVoice([`${TDIR}/lv11_sys_battery_01_wav_v1.wav`]);
          Haptic.system();
        }
      }
    });
  }

  _schedule(ms, fn) {
    const t = setTimeout(fn, ms);
    this._timers.push(t);
    return t;
  }

  // ══════════════════════════════════════════
  //   消息触发
  // ══════════════════════════════════════════
  async _triggerMessage(msg) {
    if (this.state === 'ringing' || this.state === 'in_call') {
      // 已在通话中，延迟处理（放入队列）
      this._schedule(5000, () => this._triggerMessage(msg));
      return;
    }

    // 消息16（妈妈长语音）：MOM_LINK=false时跳过，直接触发结局
    if (msg.requiresMomLink && !this.vars.MOM_LINK) {
      this.triggerFinalEnding();
      return;
    }

    // 记录为未读
    this.msgState[msg.id] = 'unread';
    this.vars.UNREAD++;
    this.currentMsg = msg;

    if (msg.type === 'call') {
      await this._startRinging(msg);
    } else if (msg.type === 'wechat_voice' || msg.type === 'wechat_text') {
      await this._notifyMessage(msg);
    } else if (msg.type === 'system_notification') {
      await this._notifySystem(msg);
    }
  }

  // ── 来电流程 ──
  async _startRinging(msg) {
    this.state = 'ringing';
    this.currentMsg = msg;

    Haptic.ring();
    await Snd.startRingtone(msg.ringtone);

    // 超时自动漏接
    this._ringTimer = setTimeout(() => {
      this._missCall(msg);
    }, msg.ringDuration * 1000);

    await TTS.speak(`${msg.senderName}，来电话了。`, { rate: 0.9, volume: 0.7 });
  }

  _missCall(msg) {
    Snd.stopRingtone();
    Haptic.stop();
    this.state = 'playing';
    this.msgState[msg.id] = 'missed';
    this.profile.add(msg.profileOnMiss);
    if (msg.id === 1 || msg.id === 14) {
      // 妈妈漏接不影响 MOM_LINK（需主动接才算）
    }
  }

  _answerCall(msg) {
    clearTimeout(this._ringTimer);
    Snd.stopRingtone();
    Haptic.confirm();
    this.state = 'in_call';
    this.msgState[msg.id] = 'read';
    this.vars.UNREAD = Math.max(0, this.vars.UNREAD - 1);
    this.profile.add(msg.profileOnAnswer);

    if (msg.stateOnAnswer) this._applyState(msg.stateOnAnswer);

    // 播放通话内容
    Snd.playVoice(msg.audio, {
      onEnd: () => {
        if (msg.inCallChoices) {
          this._startInCallChoice(msg);
        } else if (msg.autoHangup) {
          setTimeout(() => this._endCall(msg), msg.autoHangup * 1000);
        } else {
          this._endCall(msg);
        }
      }
    });
  }

  async _startInCallChoice(msg) {
    this.state = 'detail_reply';
    this.currentChoices = msg.inCallChoices;
    this.awaitingChoice = true;
    await this._readChoices(msg.inCallChoices);
  }

  _endCall(msg) {
    this.state = 'playing';
    this.currentMsg = null;
    if (msg.sfxAfter) Snd.playVoice([msg.sfxAfter]);
  }

  _rejectCall(msg) {
    clearTimeout(this._ringTimer);
    Snd.stopRingtone();
    Haptic.reject();
    this.state = 'playing';
    this.msgState[msg.id] = 'missed';
    this.profile.add(msg.profileOnMiss);
  }

  // ── 微信消息流程 ──
  async _notifyMessage(msg) {
    Haptic.message();
    const type = msg.type === 'wechat_text' ? '文字消息' : '语音';
    await TTS.speak(`${msg.senderName}，发来${type}。`, { rate: 0.9, volume: 0.7 });
    this.state = 'msg_incoming';
    // 等待玩家交互（单点播放 / 不动保持未读）
  }

  async _playMessage(msg) {
    this.state = 'msg_playing';
    this.msgState[msg.id] = 'read';
    this.vars.UNREAD = Math.max(0, this.vars.UNREAD - 1);

    // 开始BGM（如果消息指定）
    if (msg.bgm) Snd.startBGM(msg.bgm, { vol: 0.25 });

    if (msg.type === 'wechat_text') {
      // 文字消息：TTS 朗读
      await TTS.speak(msg.text, { rate: 0.85 });
      this._afterMessagePlayed(msg);
    } else {
      // 语音消息：播放音频
      Snd.playVoice(msg.audio, {
        onEnd: () => {
          // 如果是小美醉语音，5秒后撤回
          if (msg.followUp?.action === 'xiaomei_recall') {
            setTimeout(() => {
              TTS.speak('小美撤回了刚才的语音。但你已经听过了。', { rate: 0.85, volume: 0.7 });
            }, msg.followUp.delaySec * 1000);
          }
          this._afterMessagePlayed(msg);
        }
      });
    }
  }

  _afterMessagePlayed(msg) {
    this.state = 'await_reply';
    this.currentMsg = msg;
    // 等待玩家选择回应方式
    // 单点=嗯 / 双点=标准回复 / 长按=细回复 / 双指上滑=已读不回 / 不动=本已读
  }

  // ── 系统通知（时光胶囊）──
  async _notifySystem(msg) {
    Haptic.system();
    Snd.playVoice([msg.systemAudio]);
    await sleep(3000);
    await TTS.speak(msg.text, { rate: 0.85, volume: 0.8 });
    this.state = 'msg_incoming';
    this.currentMsg = msg;
    // 单点=播放, 双指上滑=跳过
  }

  async _playSystemMessage(msg) {
    const profileLabel = this.profile.label;
    const audioUrl = msg.audioByProfile[profileLabel];
    this.msgState[msg.id] = 'read';
    this.vars.UNREAD = Math.max(0, this.vars.UNREAD - 1);
    this._applyState(msg.stateOnPlay || {});
    this.profile.add(msg.profileOnPlay);

    this.state = 'msg_playing';
    Snd.playVoice([audioUrl], {
      onEnd: () => {
        this.state = 'playing';
        this._checkEndingConditions();
      }
    });
  }

  // ══════════════════════════════════════════
  //   细回复流程
  // ══════════════════════════════════════════
  async _enterDetailReply(msg) {
    if (!msg.detailReplies) return;
    this.state = 'detail_reply';
    this.currentChoices = msg.detailReplies;
    this.awaitingChoice = true;
    Haptic.detailMode();
    await this._readChoices(msg.detailReplies);
  }

  async _readChoices(choices) {
    const nums = ['一', '二', '三', '四'];
    for (let i = 0; i < choices.length; i++) {
      if (!this.awaitingChoice) return;
      await TTS.speak(`${nums[i]}……`, { rate: 0.75, volume: 0.65 });
      await sleep(200);
      await TTS.speak(choices[i].label, { rate: 0.85, volume: 0.85 });
      await sleep(400);
    }
    // 读完后震动提示"可以选了"
    if (this.awaitingChoice) Haptic.confirm();
  }

  _selectDetailChoice(dir) {
    if (!this.awaitingChoice || !this.currentChoices) return;
    const choice = this.currentChoices.find(c => c.dir === dir);
    if (!choice) { Haptic.error(); return; }

    this.awaitingChoice = false;
    TTS.stop();
    Haptic.select();

    const msg = this.currentMsg;

    if (choice.isSilence) {
      // 玩家选择不说话
      TTS.speak('（沉默）', { rate: 0.8, volume: 0.5 });
    } else {
      TTS.speak(`发送：${choice.label}`, { rate: 0.85, volume: 0.7 });
      this.msgState[msg.id] = 'replied';
      this.profile.onDetailReply();
    }

    if (choice.state) this._applyState(choice.state);
    if (choice.profile) this.profile.add(choice.profile);

    // 周南相关深度追踪
    if (choice.state?.ZHOUNAN_DEPTH_ADD) {
      this.vars.ZHOUNAN_DEPTH += 1;
    }
    if (choice.state?.ZHOUNAN_SHARE) {
      this.vars.ZHOUNAN_SHARE = true;
    }

    this.state = 'playing';
    this.currentChoices = null;
    this._checkEndingConditions();
  }

  // ══════════════════════════════════════════
  //   手势处理器
  // ══════════════════════════════════════════
  _onSingleTap() {
    const s = this.state;
    const msg = this.currentMsg;

    if (s === 'ringing') {
      this._answerCall(msg);
    }
    else if (s === 'msg_incoming') {
      if (msg.type === 'system_notification') {
        this._playSystemMessage(msg);
      } else {
        this._playMessage(msg);
      }
    }
    else if (s === 'await_reply') {
      // 单点 = 发"嗯"
      if (msg?.type !== 'call') {
        TTS.speak('发送：嗯。', { rate: 0.9, volume: 0.7 });
        this.msgState[msg.id] = 'replied';
        this.profile.onSimpleReply();
        if (msg.stateOnStdReply) this._applyState(msg.stateOnStdReply);
        this.state = 'playing';
        this._checkEndingConditions();
      }
    }
    else if (s === 'detail_reply' && this.awaitingChoice) {
      // 在细回复中单点 = 重听选项
      this._readChoices(this.currentChoices);
    }
    else if (s === 'inbox') {
      this._inboxSelect();
    }
    else if (s === 'playing') {
      const unread = this.vars.UNREAD;
      if (unread > 0) {
        TTS.speak(`${unread}条未读消息。上滑打开收件箱。`, { rate: 0.9, volume: 0.6 });
      } else {
        TTS.speak('暂无新消息。', { rate: 0.9, volume: 0.6 });
      }
    }
  }

  _onDoubleTap() {
    const s = this.state;
    const msg = this.currentMsg;

    if (s === 'await_reply' && msg) {
      // 双点 = 发标准回复
      const reply = msg.standardReply || '嗯，好的。';
      TTS.speak(`发送：${reply}`, { rate: 0.9, volume: 0.7 });
      this.msgState[msg.id] = 'replied';
      this.profile.onDetailReply();
      if (msg.stateOnStdReply) this._applyState(msg.stateOnStdReply);
      this.state = 'playing';
      this._checkEndingConditions();
    }
    else if (s === 'msg_incoming') {
      // 双点 = 直接回"嗯"不听
      if (msg?.type === 'wechat_text') {
        TTS.speak('发送：嗯。', { rate: 0.9, volume: 0.7 });
        this.msgState[msg.id] = 'replied';
        this.profile.onSimpleReply();
        this.state = 'playing';
      }
    }
    else if (s === 'ringing') {
      // 双点来电 = 同样接听
      this._answerCall(msg);
    }
  }

  _onLongPress1s() {
    const s = this.state;
    const msg = this.currentMsg;

    if (s === 'await_reply' && msg?.detailReplies) {
      this._enterDetailReply(msg);
    }
    else if (s === 'in_call' && msg?.inCallChoices) {
      this._startInCallChoice(msg);
    }
    else if (s === 'detail_reply' && this.awaitingChoice) {
      // 重听选项
      TTS.stop();
      this._readChoices(this.currentChoices);
    }
  }

  _onLongPress5s() {
    // 强制挂断
    if (this.state === 'in_call' || this.state === 'ringing') {
      clearTimeout(this._ringTimer);
      Snd.stopRingtone();
      Snd.stopVoice();
      Haptic.reject();
      TTS.speak('已挂断。', { rate: 0.9, volume: 0.7 });
      this.state = 'playing';
    }
  }

  _onSwipe(dir) {
    const s = this.state;
    const msg = this.currentMsg;

    // 细回复 / 通话选项：四个方向用于选择
    if ((s === 'detail_reply' || (s === 'in_call' && this.awaitingChoice)) && this.currentChoices) {
      this._selectDetailChoice(dir);
      return;
    }

    // 下滑 = 查询当前状态（任意场景可用）
    if (dir === 'down') {
      this._announceStatus();
      return;
    }

    // 上滑 = 打开收件箱（主屏幕时）
    if (dir === 'up') {
      if (s === 'playing') this._onInboxOpen();
      return;
    }

    // 右滑 = 接听（来电时）
    if (dir === 'right') {
      if (s === 'ringing') this._answerCall(msg);
      return;
    }

    // 左滑 = 拒接 / 挂断 / 忽略 / 已读不回 / 返回
    if (dir === 'left') {
      if (s === 'ringing') {
        this._rejectCall(msg);
      }
      else if (s === 'in_call') {
        Snd.stopVoice();
        Haptic.reject();
        TTS.speak('已挂断。', { rate: 0.9, volume: 0.7 });
        this.state = 'playing';
        this.currentMsg = null;
        this.awaitingChoice = false;
      }
      else if (s === 'msg_incoming') {
        if (msg?.type === 'system_notification') {
          TTS.speak('已跳过。', { rate: 0.9, volume: 0.6 });
          this.msgState[msg.id] = 'read';
          this.profile.add(msg.profileOnSkip);
        } else {
          TTS.speak('（消息保持未读）', { rate: 0.85, volume: 0.5 });
        }
        this.state = 'playing';
        this.currentMsg = null;
      }
      else if (s === 'await_reply' && msg) {
        TTS.speak('（已读不回）', { rate: 0.85, volume: 0.6 });
        this.msgState[msg.id] = 'read';
        this.profile.onReadNoReply();
        this.state = 'playing';
      }
      else if (s === 'inbox') {
        this.state = 'playing';
        this._inboxMessages = null;
        TTS.speak('返回主屏幕。', { rate: 0.9, volume: 0.6 });
      }
    }
  }

  // ── 下滑：播报当前状态和可用操作 ──
  _announceStatus() {
    const s = this.state;
    const msg = this.currentMsg;

    if (s === 'playing') {
      const unread = this.vars.UNREAD;
      if (unread > 0) {
        TTS.speak(`主屏幕，${unread}条未读。上滑查看收件箱。`, { rate: 0.9, volume: 0.7 });
      } else {
        TTS.speak('主屏幕，暂无新消息。', { rate: 0.9, volume: 0.7 });
      }
    }
    else if (s === 'ringing') {
      TTS.speak(`${msg?.senderName}来电中。单点接听，左滑拒接。`, { rate: 0.9, volume: 0.7 });
    }
    else if (s === 'in_call') {
      TTS.speak('通话中。左滑挂断。', { rate: 0.9, volume: 0.7 });
    }
    else if (s === 'msg_incoming') {
      TTS.speak(`${msg?.senderName}的新消息。单点播放，左滑忽略。`, { rate: 0.9, volume: 0.7 });
    }
    else if (s === 'msg_playing') {
      TTS.speak('消息播放中。', { rate: 0.9, volume: 0.7 });
    }
    else if (s === 'await_reply') {
      TTS.speak(`${msg?.senderName}的消息已播完。单点回嗯，双点标准回复，长按细回复，左滑已读不回。`, { rate: 0.9, volume: 0.7 });
    }
    else if (s === 'detail_reply') {
      TTS.speak('细回复选项中。滑动选择，单点重听。', { rate: 0.9, volume: 0.7 });
    }
    else if (s === 'inbox') {
      TTS.speak('收件箱。单点进入最新消息，左滑返回。', { rate: 0.9, volume: 0.7 });
    }
  }

  async _onInboxOpen() {
    if (this.state === 'in_call') return;

    const prevState = this.state;
    this.state = 'inbox';
    Haptic.system();

    // 统计未读/未回
    const unreadMsgs = MESSAGES.filter(m =>
      !this.msgState[m.id] || this.msgState[m.id] === 'unread'
    );

    if (unreadMsgs.length === 0) {
      await TTS.speak('收件箱已空。', { rate: 0.9, volume: 0.7 });
      this.state = prevState;
      return;
    }

    await TTS.speak(`收件箱：${unreadMsgs.length}条未读。`, { rate: 0.9, volume: 0.7 });

    for (const m of unreadMsgs.slice(0, 5)) {
      const sender = SENDERS[m.sender];
      const type = m.type === 'call' ? '未接来电' : m.type === 'wechat_text' ? '文字' : '语音';
      await TTS.speak(`${sender?.name || m.senderName}，${type}。`, { rate: 0.85, volume: 0.7 });
      await sleep(200);
    }

    await TTS.speak('单点进入最新一条，左滑返回。', { rate: 0.85, volume: 0.6 });

    this._inboxMessages = unreadMsgs;
    // 5秒后自动退出收件箱
    setTimeout(() => {
      if (this.state === 'inbox') {
        this.state = prevState;
        this._inboxMessages = null;
      }
    }, 8000);
  }

  _inboxSelect() {
    if (!this._inboxMessages || this._inboxMessages.length === 0) {
      this.state = 'playing';
      return;
    }
    const msg = this._inboxMessages[0];
    this._inboxMessages = null;
    this.currentMsg = msg;
    this.state = 'playing';
    // 触发该消息
    this._triggerMessage(msg);
  }

  // ══════════════════════════════════════════
  //   状态变量应用
  // ══════════════════════════════════════════
  _applyState(changes) {
    for (const [k, v] of Object.entries(changes)) {
      if (k === 'ZHOUNAN_DEPTH_ADD') {
        this.vars.ZHOUNAN_DEPTH += (v || 1);
      } else if (v !== null) {
        this.vars[k] = v;
      }
    }
  }

  // ══════════════════════════════════════════
  //   结局判定
  // ══════════════════════════════════════════
  _checkEndingConditions() {
    // 只在消息16触发后真正判定结局
    // 这里只做中途检测
    const unread = Object.values(this.msgState).filter(s => s === 'unread').length;

    // 结局D：未读≥8时在01:00前触发
    if (unread >= 8 && Date.now() - this._startTime >= gt(1, 0) * 1000) {
      if (!this._endingTriggered) this._triggerEnding('D');
    }
  }

  async triggerFinalEnding() {
    if (this._endingTriggered) return;

    const v = this.vars;
    const unread = Object.values(this.msgState).filter(s => s === 'unread' || !this.msgState[s]).length;

    // 结局 E（隐藏）
    if (v.ZHOUNAN_DEPTH >= 2 && v.ZHOUNAN_SHARE &&
        (this.profile.label === 'engagement' || this.profile.label === 'nostalgia')) {
      return this._triggerEnding('E');
    }

    // 结局 A：妈妈连接+自己录音+有回复
    if (v.MOM_LINK && v.SELF_RECORD) {
      return this._triggerEnding('A');
    }

    // 结局 B：拒了阿哲+回了周南
    if (v.HE_BACK === false && v.ZHOUNAN_DEPTH >= 1) {
      return this._triggerEnding('B');
    }

    // 结局 C：全部已读但回复≤2
    const repliedCount = Object.values(this.msgState).filter(s => s === 'replied').length;
    const readCount = Object.values(this.msgState).filter(s => s !== 'unread').length;
    if (readCount >= MESSAGES.length - 2 && repliedCount <= 2) {
      return this._triggerEnding('C');
    }

    // 结局 D（兜底）
    this._triggerEnding('D');
  }

  async _triggerEnding(type) {
    if (this._endingTriggered) return;
    this._endingTriggered = true;
    this.state = 'ending';

    Snd.stopBGM(3000);
    await sleep(2000);

    const ENDINGS = {
      A: this._endingA.bind(this),
      B: this._endingB.bind(this),
      C: this._endingC.bind(this),
      D: this._endingD.bind(this),
      E: this._endingE.bind(this),
    };

    if (ENDINGS[type]) await ENDINGS[type]();
  }

  async _endingA() {
    // 妈妈语音播完→厨房→烧水
    Snd.startAmbience(`${AMB}/amb_kitchen_morning_v1.wav`, { vol: 0.3 });
    await sleep(2000);
    Snd.playVoice([`${SFX}/sfx_kettle_whistle_v1.wav`]);
    await sleep(4000);
    this._showCaption('明天再说。');
    await sleep(3000);
    Snd.playVoice([`${SFX}/sfx_ending_chime_v1.wav`]);
  }

  async _endingB() {
    await TTS.speak('寄出。', { rate: 0.8, volume: 0.8 });
    await sleep(4000);
    this._showCaption('寄出。');
  }

  async _endingC() {
    await TTS.speak(
      `今晚共${MESSAGES.length}条新消息，已读${Object.values(this.msgState).filter(s => s !== 'unread').length}，未回复${MESSAGES.length - Object.values(this.msgState).filter(s => s === 'replied').length}。`,
      { rate: 0.85, volume: 0.8 }
    );
    await sleep(6000);
    this._showCaption('今晚就这样。');
  }

  async _endingD() {
    Snd.playVoice([`${TDIR}/lv11_sys_battery_01_wav_v1.wav`]);
    await sleep(2000);
    Haptic.ring();
    await sleep(1000);
    // 屏幕"彻底黑了"→清晨鸟叫
    await sleep(3000);
    Snd.startAmbience(`${AMB}/amb_dawn_birds_v1.wav`, { vol: 0.4 });
    await sleep(4000);
    this._showCaption('早上好。');
  }

  async _endingE() {
    // 周南秒回
    await sleep(2000);
    await TTS.speak('周南发来语音。', { rate: 0.9, volume: 0.7 });
    await TTS.speak('那我下次出差来北京，请你吃饭好不好。', { rate: 0.9 });
    await sleep(2000);
    // 林夏的轻笑（用self3y音色）
    Snd.playVoice([`${TDIR}/lv11_sys_goodnight_wav_v1.wav`]);
    await sleep(3000);
    this._showCaption('好。');
    await sleep(2000);
    Snd.playVoice([`${SFX}/sfx_ending_chime_v1.wav`]);
  }

  _showCaption(text) {
    const el = document.getElementById('caption');
    el.textContent = text;
    el.style.display = 'flex';
  }
}
