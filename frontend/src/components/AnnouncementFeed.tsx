import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'

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

interface Settings {
  language: string
  textSize: number
  haptics: boolean
  highContrast: boolean
}

interface Props {
  announcements: Announcement[]
  settings: Settings
}

const SEVERITY_COLORS = {
  critical: 'bg-red-600',
  warning: 'bg-amber-500',
  info: 'bg-blue-500',
  crowd: 'bg-purple-500',
}

const SEVERITY_BG = {
  critical: 'bg-red-50 border-red-200',
  warning: 'bg-amber-50 border-amber-200',
  info: 'bg-blue-50 border-blue-200',
  crowd: 'bg-purple-50 border-purple-200',
}

export default function AnnouncementFeed({ announcements, settings }: Props) {
  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      {announcements.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <p className="text-lg">Waiting for updates...</p>
          <p className="text-sm mt-2">The live feed will appear here</p>
        </div>
      ) : (
        announcements.map(ann => (
          <AnnouncementCard
            key={ann.id}
            announcement={ann}
            language={settings.language}
          />
        ))
      )}
    </div>
  )
}

function AnnouncementCard({ announcement, language }: {
  announcement: Announcement
  language: string
}) {
  const [expanded, setExpanded] = useState(false)

  const time = new Date(announcement.timestamp * 1000)
  const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  const color = SEVERITY_COLORS[announcement.severity as keyof typeof SEVERITY_COLORS] || 'bg-blue-500'
  const bgClass = SEVERITY_BG[announcement.severity as keyof typeof SEVERITY_BG] || 'bg-slate-50 border-slate-200'

  // Get the best available text based on selected language translation
  let displayText = announcement.plain_language || announcement.original
  if (announcement.translated && announcement.translated[language]) {
    displayText = announcement.translated[language]
  } else if (announcement.type === 'match_event' && announcement.description) {
    displayText = announcement.description
  }

  const isGoal = announcement.type === 'match_event' && announcement.score_a !== undefined

  return (
    <div
      className={clsx(
        'rounded-xl border-2 overflow-hidden transition-all',
        bgClass,
        isGoal && 'ring-2 ring-purple-400 ring-offset-2'
      )}
    >
      {/* Severity band */}
      <div className={clsx('h-1.5 w-full', color)} />

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl" role="img" aria-label={announcement.category}>
              {announcement.icon || 'ℹ️'}
            </span>
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              {announcement.category.replace('_', ' ')}
            </span>
          </div>
          <span className="text-xs text-slate-400">{timeStr}</span>
        </div>

        {/* Main content */}
        <p className="mt-3 text-lg font-medium text-slate-800 leading-snug">
          {displayText}
        </p>

        {/* Goal celebration */}
        {isGoal && (
          <div className="mt-3 flex items-center gap-4">
            <span className="text-3xl font-bold text-slate-900">
              {announcement.team_a} {announcement.score_a} - {announcement.score_b} {announcement.team_b}
            </span>
            {announcement.minute && (
              <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                {announcement.minute}'
              </span>
            )}
          </div>
        )}

        {/* Expandable details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-slate-200 space-y-2">
            <div>
              <p className="text-xs text-slate-500 uppercase">Original</p>
              <p className="text-sm text-slate-700">{announcement.original}</p>
            </div>
            {announcement.plain_language && (
              <div>
                <p className="text-xs text-slate-500 uppercase">Plain Language</p>
                <p className="text-sm text-slate-700">{announcement.plain_language}</p>
              </div>
            )}
          </div>
        )}

        {/* Expand button */}
        <button
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Collapse announcement details' : 'Expand announcement details'}
          className="mt-3 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
        >
          {expanded ? (
            <>Less <ChevronUp className="w-4 h-4" /></>
          ) : (
            <>More <ChevronDown className="w-4 h-4" /></>
          )}
        </button>
      </div>
    </div>
  )
}