import { useState, useEffect, useCallback } from 'react'
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { MessageCircle, MapPin, Settings, Bell, Wifi, WifiOff } from 'lucide-react'
import AnnouncementFeed from '../components/AnnouncementFeed'
import ChatInterface from '../components/ChatInterface'
import StadiumMap from '../components/StadiumMap'
import SettingsPanel from '../components/SettingsPanel'
import UrgentOverlay from '../components/UrgentOverlay'
import { useWebSocket } from '../hooks/useWebSocket'

type Tab = 'feed' | 'ask' | 'map' | 'settings'

interface Settings {
  language: string
  textSize: number
  haptics: boolean
  highContrast: boolean
}

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'हिंदी (Hindi)' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'ar', name: 'العربية' },
  { code: 'pt', name: 'Português' },
  { code: 'zh', name: '中文' },
]

export default function FanApp() {
  const location = useLocation()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('feed')
  const [connected, setConnected] = useState(false)
  const [urgentMessage, setUrgentMessage] = useState<string | null>(null)
  const [settings, setSettings] = useState<Settings>({
    language: 'en',
    textSize: 1,
    haptics: true,
    highContrast: false,
  })
  const [section] = useState('114')

  // Sync tab with URL
  useEffect(() => {
    const path = location.pathname.replace('/fan/', '')
    if (path === 'ask' || path === 'map' || path === 'settings') {
      setActiveTab(path as Tab)
    } else {
      setActiveTab('feed')
    }
  }, [location])

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab)
    navigate(`/fan/${tab === 'feed' ? '' : tab}`)
  }

  // WebSocket connection
  const { announcements } = useWebSocket(section, settings.language, {
    onConnect: () => setConnected(true),
    onDisconnect: () => setConnected(false),
    onUrgent: (msg) => {
      setUrgentMessage(msg)
      if (settings.haptics && navigator.vibrate) {
        navigator.vibrate([200, 100, 200, 100, 500])
      }
    }
  })

  // Listen for urgent announcements
  useEffect(() => {
    const latest = announcements[0]
    if (latest && latest.severity === 'critical') {
      setUrgentMessage(latest.plain_language || latest.original)
      if (settings.haptics && navigator.vibrate) {
        navigator.vibrate([200, 100, 200, 100, 500])
      }
    }
  }, [announcements, settings.haptics])

  const dismissUrgent = useCallback(() => {
    setUrgentMessage(null)
  }, [])

  const updateSettings = useCallback((newSettings: Partial<Settings>) => {
    setSettings(prev => {
      const nextSettings = { ...prev, ...newSettings }
      // Apply text size
      if (newSettings.textSize !== undefined) {
        document.documentElement.style.setProperty('--font-size-multiplier', String(newSettings.textSize))
      }
      // Apply high contrast class
      if (newSettings.highContrast !== undefined) {
        if (newSettings.highContrast) {
          document.documentElement.classList.add('high-contrast')
        } else {
          document.documentElement.classList.remove('high-contrast')
        }
      }
      return nextSettings
    })
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Urgent overlay */}
      {urgentMessage && (
        <UrgentOverlay message={urgentMessage} onDismiss={dismissUrgent} />
      )}

      {/* Header */}
      <header className="bg-blue-800 text-white px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold">StadiumSense</h1>
          <div className="flex items-center gap-2 text-sm">
            {connected ? (
              <>
                <Wifi className="w-4 h-4 text-green-400" />
                <span>Section {section}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-400" />
                <span>Reconnecting...</span>
              </>
            )}
          </div>
        </div>
        <div className="text-xs text-blue-200">
          Demo data — not affiliated with FIFA
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={
            <AnnouncementFeed
              announcements={announcements}
              settings={settings}
            />
          } />
          <Route path="ask" element={
            <ChatInterface
              language={settings.language}
              section={section}
            />
          } />
          <Route path="map" element={
            <StadiumMap section={section} />
          } />
          <Route path="settings" element={
            <SettingsPanel
              settings={settings}
              onUpdate={updateSettings}
              languages={LANGUAGES}
            />
          } />
        </Routes>
      </main>

      {/* Bottom navigation */}
      <nav className="bg-white border-t border-slate-200 flex justify-around py-2">
        <NavButton
          active={activeTab === 'feed'}
          onClick={() => handleTabChange('feed')}
          icon={<Bell className="w-5 h-5" />}
          label="Feed"
        />
        <NavButton
          active={activeTab === 'ask'}
          onClick={() => handleTabChange('ask')}
          icon={<MessageCircle className="w-5 h-5" />}
          label="Ask"
        />
        <NavButton
          active={activeTab === 'map'}
          onClick={() => handleTabChange('map')}
          icon={<MapPin className="w-5 h-5" />}
          label="Map"
        />
        <NavButton
          active={activeTab === 'settings'}
          onClick={() => handleTabChange('settings')}
          icon={<Settings className="w-5 h-5" />}
          label="Settings"
        />
      </nav>
    </div>
  )
}

function NavButton({ active, onClick, icon, label }: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
        active
          ? 'text-blue-700 bg-blue-50'
          : 'text-slate-500 hover:text-slate-700'
      }`}
      aria-label={label}
    >
      {icon}
      <span className="text-xs font-medium">{label}</span>
    </button>
  )
}