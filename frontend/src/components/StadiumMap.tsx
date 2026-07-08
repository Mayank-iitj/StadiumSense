import { useState, useEffect } from 'react'
import { MapPin, Navigation, RefreshCw } from 'lucide-react'

interface GraphNode {
  name: string
  x: number
  y: number
  step_free: boolean
  type: string
}

interface Graph {
  nodes: Record<string, GraphNode>
  edges: Array<{ from: string; to: string; distance: number }>
}

interface Props {
  section: string
}

const QUICK_DESTINATIONS = [
  { id: 'restroom_105', label: 'Accessible Restroom (105)' },
  { id: 'restroom_114', label: 'Accessible Restroom (114)' },
  { id: 'first_aid_105', label: 'First Aid' },
  { id: 'quiet_room', label: 'Quiet Room' },
  { id: 'gate_a', label: 'Gate A (Main)' },
  { id: 'gate_b', label: 'Gate B (East)' },
  { id: 'gate_c', label: 'Gate C (South)' },
  { id: 'service_animal_area', label: 'Service Animal Area' },
]

export default function StadiumMap({ section }: Props) {
  const [graph, setGraph] = useState<Graph | null>(null)
  const [route, setRoute] = useState<string[]>([])
  const [routeDescription, setRouteDescription] = useState<string>('')
  const [selectedDestination, setSelectedDestination] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [currentLocation] = useState(`section_${section}`)

  useEffect(() => {
    // Load graph data
    fetch('/api/graph')
      .then(res => res.json())
      .then(data => setGraph(data))
      .catch(console.error)
  }, [])

  const handleRouteRequest = async (destinationId: string) => {
    setSelectedDestination(destinationId)
    setLoading(true)

    try {
      const response = await fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start: currentLocation,
          destination: destinationId,
          step_free: true
        })
      })

      const data = await response.json()
      setRoute(data.route || [])
      setRouteDescription(data.description || '')
    } catch (e) {
      console.error('Route error:', e)
    } finally {
      setLoading(false)
    }
  }

  if (!graph) {
    return (
      <div className="h-full flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    )
  }

  // Find user position node
  const userNodeKey = `section_${section}`
  // const userNode = graph.nodes[userNodeKey] || graph.nodes['section_105']

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Map display */}
      <div className="flex-1 relative bg-slate-100 overflow-hidden">
        <svg
          viewBox="0 0 100 100"
          className="w-full h-full"
          style={{ minHeight: '300px' }}
        >
          {/* Stadium outline */}
          <ellipse cx="50" cy="50" rx="45" ry="40" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1"/>

          {/* Field */}
          <rect x="25" y="35" width="50" height="30" fill="#4ade80" stroke="#22c55e" strokeWidth="0.5"/>

          {/* Connection lines */}
          {graph.edges.map((edge, i) => {
            const node1 = graph.nodes[edge.from]
            const node2 = graph.nodes[edge.to]
            if (!node1 || !node2) return null

            const isEdgeOnRoute = route.includes(edge.from) && route.includes(edge.to)

            return (
              <line
                key={`edge-${i}`}
                x1={node1.x}
                y1={node1.y}
                x2={node2.x}
                y2={node2.y}
                stroke={isEdgeOnRoute ? '#3b82f6' : '#cbd5e1'}
                strokeWidth={isEdgeOnRoute ? 2 : 0.5}
                strokeDasharray={node1.step_free && node2.step_free ? 'none' : '2,2'}
              />
            )
          })}

          {/* Nodes */}
          {Object.entries(graph.nodes).map(([key, node]) => {
            const isOnRoute = route.includes(key)
            const isUser = key === userNodeKey || key === `section_${section}`
            const isDest = key === selectedDestination

            return (
              <g key={key}>

                {/* Node circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isUser || isDest ? 4 : 2.5}
                  fill={
                    isUser ? '#22c55e' :
                    isDest ? '#ef4444' :
                    isOnRoute ? '#3b82f6' :
                    node.step_free ? '#64748b' : '#94a3b8'
                  }
                  stroke={isUser || isDest ? 'white' : 'none'}
                  strokeWidth={isUser || isDest ? 1.5 : 0}
                />

                {/* Labels for important nodes */}
                {(key.includes('gate') || key.includes('restroom') || key.includes('first_aid') || key.includes('quiet') || key.includes('section_')) && (
                  <text
                    x={node.x}
                    y={node.y - (isUser || isDest ? 6 : 4)}
                    fontSize="2.5"
                    fill="#475569"
                    textAnchor="middle"
                  >
                    {node.name.replace('Section ', 'Sec ').replace('Accessible ', '')}
                  </text>
                )}
              </g>
            )
          })}
        </svg>

        {/* Legend */}
        <div className="absolute bottom-2 left-2 bg-white/90 rounded-lg p-2 text-xs space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            <span>You</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Step-free</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-slate-400"></span>
            <span>Has stairs</span>
          </div>
        </div>
      </div>

      {/* Route description */}
      {route.length > 0 && (
        <div className="p-4 bg-blue-50 border-t border-blue-100">
          <div className="flex items-start gap-3">
            <Navigation className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-medium text-blue-900">{routeDescription}</p>
              <p className="text-sm text-blue-700 mt-1">
                {route.length} stops • Step-free route
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick destinations */}
      <div className="p-4 bg-white border-t border-slate-200">
        <p className="text-sm font-medium text-slate-600 mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4" />
          Quick destinations
        </p>
        <div className="grid grid-cols-2 gap-2">
          {QUICK_DESTINATIONS.map(dest => (
            <button
              key={dest.id}
              onClick={() => handleRouteRequest(dest.id)}
              disabled={loading}
              className={`px-3 py-2 text-left rounded-lg text-sm transition-colors ${
                selectedDestination === dest.id
                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                  : 'bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              {dest.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}