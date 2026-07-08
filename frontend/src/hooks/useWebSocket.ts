import { useState, useEffect, useRef, useCallback } from 'react'

interface Announcement {
  id: string
  timestamp: number
  type: string
  original: string
  category: string
  severity: string
  plain_language?: string
  translated?: Record<string, string>
  needs_avatar?: boolean
  icon?: string
  description?: string
  team_a?: string
  team_b?: string
  score_a?: number
  score_b?: number
  minute?: number
  scorer?: string
}

interface WebSocketOptions {
  onConnect?: () => void
  onDisconnect?: () => void
  onUrgent?: (message: string) => void
}

export function useWebSocket(section: string, language: string, options: WebSocketOptions = {}) {
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  // Store options in a mutable ref to prevent reconnecting when parent component callbacks are re-created
  const optionsRef = useRef(options)
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  const connect = useCallback(() => {
    // In development, use the proxied WebSocket
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${section}/${language}`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
        optionsRef.current.onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'announcement') {
            setAnnouncements(prev => [data.data, ...prev].slice(0, 50))

            // Check for urgent
            if (data.data.severity === 'critical') {
              optionsRef.current.onUrgent?.(data.data.plain_language || data.data.original)
            }
          }
        } catch (e) {
          console.error('Failed to parse message:', e)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        optionsRef.current.onDisconnect?.()

        // Reconnect after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      wsRef.current = ws
    } catch (e) {
      console.error('Failed to create WebSocket:', e)
    }
  }, [section, language]) // Decoupled from options!

  useEffect(() => {
    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [connect])



  return { announcements, connected }
}