import { Globe, Type, Smartphone, Contrast } from 'lucide-react'

interface Settings {
  language: string
  textSize: number
  haptics: boolean
  highContrast: boolean
}

interface Language {
  code: string
  name: string
}

interface Props {
  settings: Settings
  onUpdate: (newSettings: Partial<Settings>) => void
  languages: Language[]
}

export default function SettingsPanel({ settings, onUpdate, languages }: Props) {
  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      {/* Language */}
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Globe className="w-5 h-5 text-blue-600" />
          <h2 className="font-semibold text-slate-800">Language</h2>
        </div>
        <select
          value={settings.language}
          onChange={(e) => onUpdate({ language: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
      </section>

      {/* Text Size */}
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Type className="w-5 h-5 text-blue-600" />
          <h2 className="font-semibold text-slate-800">Text Size</h2>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600">A</span>
          <input
            type="range"
            min="0.8"
            max="1.5"
            step="0.1"
            value={settings.textSize}
            onChange={(e) => onUpdate({ textSize: parseFloat(e.target.value) })}
            className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
          />
          <span className="text-xl text-slate-600">A</span>
        </div>
        <p className="text-sm text-slate-500 mt-2">
          Current: {Math.round(settings.textSize * 100)}%
        </p>
      </section>

      {/* Haptics */}
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-slate-800">Vibration Alerts</h2>
          </div>
          <button
            onClick={() => onUpdate({ haptics: !settings.haptics })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              settings.haptics ? 'bg-blue-600' : 'bg-slate-300'
            }`}
            role="switch"
            aria-checked={settings.haptics}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                settings.haptics ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <p className="text-sm text-slate-500 mt-2">
          Vibrate for urgent announcements (evacuation, medical)
        </p>
      </section>

      {/* High Contrast */}
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Contrast className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-slate-800">High Contrast</h2>
          </div>
          <button
            onClick={() => onUpdate({ highContrast: !settings.highContrast })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              settings.highContrast ? 'bg-blue-600' : 'bg-slate-300'
            }`}
            role="switch"
            aria-checked={settings.highContrast}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                settings.highContrast ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <p className="text-sm text-slate-500 mt-2">
          Increase contrast for better visibility
        </p>
      </section>

      {/* About */}
      <section className="text-center text-sm text-slate-400 py-4">
        <p>StadiumSense v1.0</p>
        <p className="mt-1">Demo data — not affiliated with FIFA</p>
      </section>
    </div>
  )
}