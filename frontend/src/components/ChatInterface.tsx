import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface Message {
  id: string
  question: string
  answer: string
  citations: string[]
  language: string
}

interface Props {
  language: string
  section: string
}

export default function ChatInterface({ language, section }: Props) {
  const [question, setQuestion] = useState('Where is the nearest wheelchair accessible bathroom?')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const currentQuestion = question.trim()
    setQuestion('')
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: currentQuestion,
          language: language,
          location: `Section ${section}`
        })
      })

      const data = await response.json()

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        question: currentQuestion,
        answer: data.answer,
        citations: data.citations || [],
        language: data.language
      }])
    } catch (e) {
      setError('Failed to get answer. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Quick questions
  const quickQuestions = [
    "Nearest step-free restroom?",
    "Where is first aid?",
    "How do I get to Gate A?",
    "Are there halal options?"
  ]

  return (
    <div className="h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="text-center py-8">
            <p className="text-slate-600 mb-4">Ask me anything about the stadium</p>
            <div className="space-y-2">
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuestion(q)
                    // Trigger submit
                    setTimeout(() => {
                      const form = document.getElementById('chat-form') as HTMLFormElement
                      form?.requestSubmit()
                    }, 0)
                  }}
                  className="block w-full text-left px-4 py-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className="space-y-2">
            {/* Question */}
            <div className="bg-blue-100 rounded-xl rounded-br-md p-3">
              <p className="text-sm font-medium text-blue-900">{msg.question}</p>
            </div>

            {/* Answer */}
            <div className="bg-white border border-slate-200 rounded-xl rounded-bl-md p-4">
              <p className="text-slate-800">{msg.answer}</p>

              {/* Citations */}
              {msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-xs text-slate-500 mb-1">Sources:</p>
                  <div className="flex flex-wrap gap-1">
                    {msg.citations.map((citation, i) => (
                      <span key={i} className="text-xs px-2 py-1 bg-slate-100 rounded text-slate-600">
                        {citation}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Thinking...</span>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        id="chat-form"
        onSubmit={handleSubmit}
        className="p-4 bg-white border-t border-slate-200"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about the stadium..."
            className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!question.trim() || loading}
            className="px-4 py-3 bg-blue-700 text-white rounded-xl hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}