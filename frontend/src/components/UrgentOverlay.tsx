import { useEffect } from 'react'
import { AlertTriangle, X } from 'lucide-react'

interface Props {
  message: string
  onDismiss: () => void
}

export default function UrgentOverlay({ message, onDismiss }: Props) {
  // Auto-dismiss after 10 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss()
    }, 10000)

    return () => clearTimeout(timer)
  }, [onDismiss])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-red-600 animate-flash">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="max-w-lg w-full mx-4 p-8 bg-white rounded-2xl shadow-2xl text-center">
          {/* Alert icon */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-10 h-10 text-red-600" />
            </div>
          </div>

          {/* Urgent message */}
          <h1 className="text-3xl font-bold text-slate-900 mb-4">
            {message}
          </h1>

          {/* Sign language note */}
          <p className="text-lg text-slate-600 mb-6">
            Please follow staff instructions immediately.
            Use the nearest accessible exit.
          </p>

          {/* Dismiss button */}
          <button aria-label="interactive button"
            onClick={onDismiss}
            className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-colors"
          >
            <X className="w-5 h-5" />
            I understand
          </button>

          {/* Timer bar */}
          <div className="mt-6 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-red-500 animate-pulse-urgent" style={{ animationDuration: '10s' }} />
          </div>
        </div>
      </div>
    </div>
  )
}