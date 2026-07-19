/** Browser voice-note recording helpers (MediaRecorder → webm/ogg blob). */

export type VoiceRecorder = {
  start: () => Promise<void>
  stop: () => Promise<{ blob: Blob; durationMs: number }>
  cancel: () => void
  isRecording: () => boolean
}

export function createVoiceRecorder(): VoiceRecorder {
  let media: MediaStream | null = null
  let rec: MediaRecorder | null = null
  let chunks: BlobPart[] = []
  let startedAt = 0
  let recording = false

  async function start() {
    if (recording) return
    media = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : ''
    rec = mime ? new MediaRecorder(media, { mimeType: mime }) : new MediaRecorder(media)
    chunks = []
    rec.ondataavailable = (e) => {
      if (e.data && e.data.size) chunks.push(e.data)
    }
    rec.start(200)
    startedAt = Date.now()
    recording = true
  }

  function stop(): Promise<{ blob: Blob; durationMs: number }> {
    return new Promise((resolve, reject) => {
      if (!rec || !recording) {
        reject(new Error('Not recording'))
        return
      }
      const r = rec
      r.onstop = () => {
        const type = r.mimeType || 'audio/webm'
        const blob = new Blob(chunks, { type })
        const durationMs = Date.now() - startedAt
        cleanup()
        resolve({ blob, durationMs })
      }
      r.stop()
      recording = false
    })
  }

  function cancel() {
    try {
      if (rec && recording) rec.stop()
    } catch { /* */ }
    cleanup()
    recording = false
  }

  function cleanup() {
    if (media) {
      media.getTracks().forEach((t) => t.stop())
      media = null
    }
    rec = null
    chunks = []
  }

  return {
    start,
    stop,
    cancel,
    isRecording: () => recording,
  }
}

export function isVoiceUrl(url: string, isVoiceFlag?: boolean): boolean {
  if (isVoiceFlag) return true
  const u = (url || '').toLowerCase()
  return /\.(webm|ogg|mp3|m4a|wav|aac|opus)(\?|$)/i.test(u) || u.includes('audio/')
}
