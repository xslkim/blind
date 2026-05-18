// gestures.js — 触控手势检测器（单指操作）
//
// 支持：单点 · 双点 · 长按1s · 长按5s
//       左滑 · 右滑 · 上滑 · 下滑

class GestureDetector {
  constructor(el) {
    this._el = el;
    this._handlers = {};

    // 状态
    this._startX = 0;
    this._startY = 0;
    this._startTime = 0;

    this._tapTimer = null;
    this._longTimer1 = null;
    this._longTimer5 = null;
    this._longFired = false;
    this._tapCount = 0;

    this._bind();
  }

  on(evt, fn) { this._handlers[evt] = fn; return this; }

  _emit(evt, data) {
    dbg(evt);
    const fn = this._handlers[evt];
    if (fn) fn(data);
  }

  _bind() {
    const el = this._el;
    el.addEventListener('touchstart',  e => this._onStart(e),  { passive: false });
    el.addEventListener('touchend',    e => this._onEnd(e),    { passive: false });
    el.addEventListener('touchcancel', e => this._onCancel(e), { passive: false });
  }

  _onStart(e) {
    e.preventDefault();
    const t = e.touches[0];
    this._startX = t.clientX;
    this._startY = t.clientY;
    this._startTime = Date.now();
    this._longFired = false;

    this._clearTimers();

    // 1s长按
    this._longTimer1 = setTimeout(() => {
      this._longFired = true;
      this._emit('longpress1s');
      Haptic.detailMode();
    }, 900);

    // 5s长按（安全机制）
    this._longTimer5 = setTimeout(() => {
      this._longFired = true;
      this._emit('longpress5s');
      Haptic.reject();
    }, 5000);
  }

  _onEnd(e) {
    e.preventDefault();
    this._clearTimers();

    const t = e.changedTouches[0];
    const dx = t.clientX - this._startX;
    const dy = t.clientY - this._startY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const dt = Date.now() - this._startTime;

    if (this._longFired) return;

    // ── 滑动判断 ──
    const SWIPE_MIN = 35;
    const SWIPE_ANG = 45;

    if (dist > SWIPE_MIN) {
      const angle = Math.abs(Math.atan2(dy, dx) * 180 / Math.PI);
      let dir = null;

      if (angle < SWIPE_ANG) dir = 'right';
      else if (angle > 180 - SWIPE_ANG) dir = 'left';
      else if (dy < 0 && Math.abs(dy) > Math.abs(dx)) dir = 'up';
      else if (dy > 0 && Math.abs(dy) > Math.abs(dx)) dir = 'down';

      if (dir) {
        this._emit(`swipe_${dir}`);
        Haptic.confirm();
        return;
      }
    }

    // ── 点击判断 ──
    if (dist < 20 && dt < 500) {
      this._tapCount++;
      if (this._tapCount === 1) {
        this._tapTimer = setTimeout(() => {
          this._tapCount = 0;
          this._emit('singletap');
          Haptic.confirm();
        }, 250);
      } else if (this._tapCount === 2) {
        clearTimeout(this._tapTimer);
        this._tapCount = 0;
        this._emit('doubletap');
        Haptic.confirm();
      }
    }
  }

  _onCancel(e) {
    this._clearTimers();
    this._longFired = false;
  }

  _clearTimers() {
    clearTimeout(this._tapTimer);
    clearTimeout(this._longTimer1);
    clearTimeout(this._longTimer5);
    this._tapTimer = null;
    this._longTimer1 = null;
    this._longTimer5 = null;
  }
}
