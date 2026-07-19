/* Shared push handlers — imported by the generated service worker when possible.
 * Also safe if registered alone. Expects JSON payload:
 * { title, body, url, tag }
 */
self.addEventListener('push', (event) => {
  let data = { title: 'CryptoInvest', body: 'You have a new notification', url: '/app/', tag: 'ci-push' }
  try {
    if (event.data) {
      const parsed = event.data.json()
      data = { ...data, ...parsed }
    }
  } catch {
    try {
      const text = event.data && event.data.text()
      if (text) data.body = text
    } catch { /* */ }
  }
  event.waitUntil(
    self.registration.showNotification(data.title || 'CryptoInvest', {
      body: data.body || '',
      tag: data.tag || 'ci-push',
      icon: '/app/favicon.svg',
      badge: '/app/favicon.svg',
      data: { url: data.url || '/app/' },
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = (event.notification.data && event.notification.data.url) || '/app/'
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          client.navigate(url)
          return client.focus()
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url)
    }),
  )
})
