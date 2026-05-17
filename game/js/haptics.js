// haptics.js — 震动反馈（Android Chrome 支持，iOS 降级为无震动）

const Haptic = {
  _ok: typeof navigator !== 'undefined' && !!navigator.vibrate,

  _v(pattern) {
    if (this._ok) navigator.vibrate(pattern);
  },

  // 来电震动（长震 + 停顿，循环由来电循环调用）
  ring()        { this._v([400, 200, 400]); },

  // 微信消息（两短震）
  message()     { this._v([80, 60, 80]); },

  // 确认操作
  confirm()     { this._v(60); },

  // 拒绝 / 挂断
  reject()      { this._v([100, 50, 100, 50, 100]); },

  // 进入细回复模式
  detailMode()  { this._v([30, 30, 60]); },

  // 选项选中
  select()      { this._v(80); },

  // 系统通知
  system()      { this._v([200, 100, 100, 100, 200]); },

  // 错误 / 无效手势
  error()       { this._v([50, 30, 50]); },

  stop()        { if (this._ok) navigator.vibrate(0); },
};
