// utils.js — 轻量工具函数

const sleep = ms => new Promise(r => setTimeout(r, ms));

function dbg(msg) {
  const el = document.getElementById('dbg');
  if (el && el.style.display !== 'none') el.textContent = msg;
}

// 语音合成（选项朗读用）
const TTS = {
  _voices: [],
  _ready: false,

  init() {
    if (!window.speechSynthesis) return;
    const load = () => {
      this._voices = speechSynthesis.getVoices();
      this._ready = true;
    };
    load();
    speechSynthesis.onvoiceschanged = load;
  },

  _pick() {
    // 优先选中文语音
    const zh = this._voices.find(v =>
      v.lang.startsWith('zh') || v.name.includes('Chinese') || v.name.includes('中')
    );
    return zh || this._voices[0] || null;
  },

  speak(text, { rate = 0.85, pitch = 1, volume = 0.85 } = {}) {
    return new Promise(resolve => {
      if (!window.speechSynthesis) { resolve(); return; }
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'zh-CN';
      u.rate = rate;
      u.pitch = pitch;
      u.volume = volume;
      const v = this._pick();
      if (v) u.voice = v;
      u.onend = resolve;
      u.onerror = resolve;
      speechSynthesis.speak(u);
    });
  },

  stop() {
    if (window.speechSynthesis) speechSynthesis.cancel();
  },
};
