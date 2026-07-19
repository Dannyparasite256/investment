/** Soft WhatsApp-like chat ping (Web Audio, no asset file). */

let ctx: AudioContext | null = null
let muted = false

export function setChatSoundMuted(v: boolean) {
  muted = v
  try {
    localStorage.setItem('ci_chat_sound_muted', v ? '1' : '0')
  } catch { /* */ }
}

export function isChatSoundMuted(): boolean {
  try {
    return localStorage.getItem('ci_chat_sound_muted') === '1'
  } catch {
    return muted
  }
}

export function playChatSound() {
  if (typeof window === 'undefined') return
  if (isChatSoundMuted() || muted) return
  try {
    const AC = window.AudioContext || (window as any).webkitAudioContext
    if (!AC) return
    if (!ctx) ctx = new AC()
    if (ctx.state === 'suspended') ctx.resume()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = 'sine'
    o.frequency.setValueAtTime(880, ctx.currentTime)
    o.frequency.exponentialRampToValueAtTime(660, ctx.currentTime + 0.08)
    g.gain.setValueAtTime(0.0001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + 0.02)
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.18)
    o.connect(g)
    g.connect(ctx.destination)
    o.start()
    o.stop(ctx.currentTime + 0.2)
  } catch { /* ignore */ }
}
