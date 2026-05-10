const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`

export function createGateway(token, handlers) {
  const socket = new WebSocket(WS_URL)

  socket.onopen = () => {
    socket.send(JSON.stringify({ type: 'auth', token }))
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    const handler = handlers[data.type]
    if (handler) handler(data)
  }

  socket.onclose = () => {
    if (handlers.onclose) handlers.onclose()
  }

  function send(method, params = {}) {
    socket.send(JSON.stringify({ jsonrpc: '2.0', method, params, id: crypto.randomUUID() }))
  }

  return { socket, send }
}
