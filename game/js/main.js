// main.js — 游戏入口

// 开发模式（URL加?dev）：时间线缩短为1/10
const DEV_MODE = new URLSearchParams(location.search).has('dev');
if (DEV_MODE) {
  // 直接缩短所有消息的触发时间
  MESSAGES.forEach(m => { m.triggerAt = Math.floor(m.triggerAt / 10); });
  document.title = '林夏 [DEV x10]';
}

let engine = null;
let gestures = null;

async function main() {
  TTS.init();

  // 初始化音频（必须在用户手势后）
  await Snd.init();

  // 预加载关键短音效
  await Promise.allSettled([
    Snd.preload('sfx_keyboard', `${SFX}/sfx_keyboard_slow_v1.wav`),
    Snd.preload('sfx_chime',    `${SFX}/sfx_ending_chime_v1.wav`),
  ]);

  // 请求屏幕常亮（Android Chrome 支持）
  try {
    if ('wakeLock' in navigator) {
      window._wakeLock = await navigator.wakeLock.request('screen');
    }
  } catch(_) {}

  // 绑定手势到游戏区域
  const gameEl = document.getElementById('game');
  gestures = new GestureDetector(gameEl);

  // 创建并启动游戏引擎
  engine = new GameEngine();
  engine.init(gestures);
  await engine.start();

  if (DEV_MODE) {
    document.getElementById('dbg').style.display = 'block';
  }
}

// 触摸启动（手机）
document.getElementById('start').addEventListener('touchend', async function onStart(e) {
  e.preventDefault();
  this.removeEventListener('touchend', onStart);
  this.style.transition = 'opacity 0.8s';
  this.style.opacity = '0';
  setTimeout(() => { this.style.display = 'none'; }, 800);
  await main();
}, { once: true });

// 鼠标点击（电脑调试）
document.getElementById('start').addEventListener('click', async function onClick() {
  this.removeEventListener('click', onClick);
  this.style.transition = 'opacity 0.8s';
  this.style.opacity = '0';
  setTimeout(() => { this.style.display = 'none'; }, 800);
  await main();
}, { once: true });

// 防止页面滚动/缩放
document.addEventListener('touchmove', e => e.preventDefault(), { passive: false });
document.addEventListener('gesturestart', e => e.preventDefault());

// 页面隐藏时停止打字音效
document.addEventListener('visibilitychange', () => {
  if (document.hidden && Snd) Snd.stopTyping();
});
