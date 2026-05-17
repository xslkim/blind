// audio.js — 音频管理器（HTML Audio + Web Audio API 混用）

class AudioManager {
  constructor() {
    this._ctx = null;
    this._master = null;
    this._bgmNode = null;
    this._ambNode = null;
    this._voiceQueue = [];
    this._voiceEl = null;
    this._ringEl = null;
    this._ringTimer = null;
    this._preloaded = {};
  }

  // ── 初始化（必须在用户手势后调用）──
  async init() {
    this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (this._ctx.state === 'suspended') await this._ctx.resume();
    this._master = this._ctx.createGain();
    this._master.gain.value = 1.0;
    this._master.connect(this._ctx.destination);
  }

  // ── 预加载短音效（铃声、UI音）──
  async preload(key, url) {
    if (this._preloaded[key]) return;
    try {
      const res = await fetch(url);
      const buf = await res.arrayBuffer();
      this._preloaded[key] = await this._ctx.decodeAudioData(buf);
    } catch(e) {
      console.warn('[Audio] preload failed:', key, e);
    }
  }

  // ── 播放预加载的短音效 ──
  playFX(key, { vol = 1.0, loop = false } = {}) {
    const buf = this._preloaded[key];
    if (!buf) return null;
    const src = this._ctx.createBufferSource();
    src.buffer = buf;
    src.loop = loop;
    const gain = this._ctx.createGain();
    gain.gain.value = vol;
    src.connect(gain);
    gain.connect(this._master);
    src.start();
    return { src, gain, stop: () => { try { src.stop(); } catch(_){} } };
  }

  // ── 铃声（循环直到 stopRingtone）──
  async startRingtone(url) {
    this.stopRingtone();
    // 使用 HTMLAudio 以支持更大文件
    this._ringEl = new Audio(url);
    this._ringEl.loop = true;
    this._ringEl.volume = 1.0;
    try { await this._ringEl.play(); } catch(e) { console.warn('[Audio] ring play error', e); }
  }

  stopRingtone() {
    if (this._ringEl) {
      this._ringEl.pause();
      this._ringEl.src = '';
      this._ringEl = null;
    }
    if (this._ringTimer) { clearTimeout(this._ringTimer); this._ringTimer = null; }
  }

  // ── 语音消息播放（支持多段顺序播放）──
  playVoice(urls, { vol = 1.0, onEnd = null, onSegEnd = null } = {}) {
    this.stopVoice();
    this._voiceQueue = [...urls];
    this._playNextSegment(vol, onEnd, onSegEnd);
  }

  _playNextSegment(vol, onEnd, onSegEnd) {
    if (this._voiceQueue.length === 0) {
      this._voiceEl = null;
      if (onEnd) onEnd();
      return;
    }
    const url = this._voiceQueue.shift();
    const el = new Audio(url);
    el.volume = vol;
    this._voiceEl = el;
    el.onended = () => {
      if (onSegEnd) onSegEnd();
      this._playNextSegment(vol, onEnd, onSegEnd);
    };
    el.onerror = () => {
      console.warn('[Audio] voice error:', url);
      this._playNextSegment(vol, onEnd, onSegEnd);
    };
    el.play().catch(e => console.warn('[Audio] voice play error', e));
  }

  stopVoice() {
    this._voiceQueue = [];
    if (this._voiceEl) {
      this._voiceEl.pause();
      this._voiceEl.onended = null;
      this._voiceEl = null;
    }
  }

  isVoicePlaying() {
    return !!(this._voiceEl && !this._voiceEl.paused);
  }

  // ── BGM（淡入淡出切换）──
  async startBGM(url, { vol = 0.35, fade = 2000 } = {}) {
    // 先淡出现有
    if (this._bgmEl) {
      const old = this._bgmEl;
      this._fadeOut(old, fade / 2).then(() => { old.pause(); old.src = ''; });
    }
    const el = new Audio(url);
    el.loop = true;
    el.volume = 0;
    this._bgmEl = el;
    try {
      await el.play();
      this._fadeTo(el, vol, fade);
    } catch(e) { console.warn('[Audio] BGM error', e); }
  }

  stopBGM(fade = 2000) {
    if (this._bgmEl) {
      const el = this._bgmEl;
      this._bgmEl = null;
      this._fadeOut(el, fade).then(() => { el.pause(); el.src = ''; });
    }
  }

  // ── 环境音（底噪循环）──
  async startAmbience(url, { vol = 0.25 } = {}) {
    if (this._ambEl) { this._ambEl.pause(); this._ambEl.src = ''; }
    const el = new Audio(url);
    el.loop = true;
    el.volume = vol;
    this._ambEl = el;
    try { await el.play(); } catch(e) { console.warn('[Audio] ambience error', e); }
  }

  stopAmbience() {
    if (this._ambEl) {
      this._ambEl.pause(); this._ambEl.src = '';
      this._ambEl = null;
    }
  }

  // ── 音量渐变 ──
  _fadeTo(el, target, duration) {
    const start = el.volume;
    const steps = 30;
    const dt = duration / steps;
    const dv = (target - start) / steps;
    let i = 0;
    const t = setInterval(() => {
      el.volume = Math.max(0, Math.min(1, start + dv * i));
      i++;
      if (i >= steps) clearInterval(t);
    }, dt);
  }

  _fadeOut(el, duration) {
    return new Promise(resolve => {
      const start = el.volume;
      const steps = 20;
      const dt = duration / steps;
      const dv = start / steps;
      let i = 0;
      const t = setInterval(() => {
        el.volume = Math.max(0, start - dv * i);
        i++;
        if (i >= steps) { clearInterval(t); resolve(); }
      }, dt);
    });
  }

  // ── 键盘声（空间音频：左耳）──
  startTyping() {
    if (this._typingNode) return;
    const buf = this._preloaded['sfx_keyboard_slow'];
    if (!buf) return;
    const src = this._ctx.createBufferSource();
    src.buffer = buf;
    src.loop = true;
    const gain = this._ctx.createGain();
    gain.gain.value = 0.15;
    // 偏左声道
    const pan = this._ctx.createStereoPanner();
    pan.pan.value = -0.8;
    src.connect(gain);
    gain.connect(pan);
    pan.connect(this._master);
    src.start();
    this._typingNode = { src, gain, pan };
  }

  stopTyping() {
    if (this._typingNode) {
      try { this._typingNode.src.stop(); } catch(_) {}
      this._typingNode = null;
    }
  }
}

const Snd = new AudioManager();
