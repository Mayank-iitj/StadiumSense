import { useState, useEffect } from 'react'
import { Send, Play, CheckCircle, Users, Bell, RefreshCw } from 'lucide-react'

interface Announcement {
  id: string
  timestamp: number
  type: string
  original: string
  category: string
  severity: string
  plain_language?: string
}

interface HelpRequest {
  id: string
  reason: string
  location: string
  severity: string
  timestamp: number
  status: string
}

export default function StaffView() {
  const [broadcastMessage, setBroadcastMessage] = useState('Attention fans: The stadium exit on the east side is experiencing heavy delays. Please use the west exit.')
  const [broadcastCategory, setBroadcastCategory] = useState('wayfinding')
  const [broadcastSeverity, setBroadcastSeverity] = useState('warning')
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [helpRequests, setHelpRequests] = useState<HelpRequest[]>([])
  const [loading, setLoading] = useState(false)
  const [demoRunning, setDemoRunning] = useState(false)

  // Poll for updates
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [annRes, helpRes] = await Promise.all([
          fetch('/api/announcements'),
          fetch('/api/help-requests')
        ])
        const annData = await annRes.json()
        const helpData = await helpRes.json()
        setAnnouncements(annData.slice(0, 20))
        setHelpRequests(helpData)
      } catch (e) {
        console.error('Fetch error:', e)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleBroadcast = async () => {
    if (!broadcastMessage.trim() || loading) return

    setLoading(true)
    try {
      await fetch('/api/broadcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: broadcastMessage,
          category: broadcastCategory,
          severity: broadcastSeverity
        })
      })
      setBroadcastMessage('')
    } catch (e) {
      console.error('Broadcast error:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleRunDemo = async () => {
    if (demoRunning) return

    setDemoRunning(true)
    try {
      await fetch('/api/demo/run', { method: 'POST' })
    } catch (e) {
      console.error('Demo error:', e)
    } finally {
      // Reset after timeline completes (~90s)
      setTimeout(() => setDemoRunning(false), 100000)
    }
  }

  const SEVERITY_COLORS = {
    critical: 'bg-red-100 text-red-800',
    warning: 'bg-amber-100 text-amber-800',
    info: 'bg-blue-100 text-blue-800',
    crowd: 'bg-purple-100 text-purple-800'
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-slate-800 text-white px-6 py-4">
        <h1 className="text-xl font-bold">StadiumSense Staff Dashboard</h1>
        <p className="text-sm text-slate-300">Venue accessibility operations</p>
      </header>

      <div className="p-6 space-y-6">
        {/* Demo Controls */}
        <section className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Demo Controls</h2>
              <p className="text-sm text-slate-500">Run the pre-recorded timeline for demos</p>
            </div>
            <button
              onClick={handleRunDemo}
              disabled={demoRunning}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                demoRunning
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {demoRunning ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Run Demo
                </>
              )}
            </button>
          </div>
        </section>

        {/* Broadcast Composer */}
        <section className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Send className="w-5 h-5 text-blue-600" />
            Broadcast Announcement
          </h2>

          <div className="space-y-4">
            <textarea
              value={broadcastMessage}
              onChange={(e) => setBroadcastMessage(e.target.value)}
              placeholder="Type your announcement here..."
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />

            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm text-slate-600 mb-1">Category</label>
                <select
                  value={broadcastCategory}
                  onChange={(e) => setBroadcastCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="wayfinding">Wayfinding</option>
                  <option value="medical">Medical</option>
                  <option value="security">Security</option>
                  <option value="info">Info</option>
                </select>
              </div>

              <div className="flex-1">
                <label className="block text-sm text-slate-600 mb-1">Severity</label>
                <select
                  value={broadcastSeverity}
                  onChange={(e) => setBroadcastSeverity(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleBroadcast}
              disabled={!broadcastMessage.trim() || loading}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-blue-700 text-white rounded-lg font-medium hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
              Broadcast to All Fans
            </button>
          </div>
        </section>

        {/* Two column layout */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Live Announcements Log */}
          <section className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5 text-blue-600" />
              Live Feed Log
            </h2>

            <div className="space-y-2 max-h-80 overflow-y-auto">
              {announcements.length === 0 ? (
                <p className="text-slate-400 text-center py-8">No announcements yet</p>
              ) : (
                announcements.map(ann => (
                  <div key={ann.id} className="p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[ann.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.info}`}>
                        {ann.severity}
                      </span>
                      <span className="text-xs text-slate-400">
                        {new Date(ann.timestamp * 1000).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700">{ann.original}</p>
                    {ann.plain_language && (
                      <p className="text-xs text-slate-500 mt-1">
                        → {ann.plain_language}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Help Requests */}
          <section className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-600" />
              Accessibility Requests
            </h2>

            <div className="space-y-2 max-h-80 overflow-y-auto">
              {helpRequests.length === 0 ? (
                <p className="text-slate-400 text-center py-8">No pending requests</p>
              ) : (
                helpRequests.map(req => (
                  <div key={req.id} className="p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[req.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.info}`}>
                        {req.severity}
                      </span>
                      <span className="text-xs text-slate-400">
                        {req.location}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700">{req.reason}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <button className="flex items-center gap-1 text-xs text-green-600 hover:text-green-700">
                        <CheckCircle className="w-3 h-3" />
                        Mark resolved
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}