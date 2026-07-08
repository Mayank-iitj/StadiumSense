import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import FanApp from './pages/FanApp'
import StaffView from './pages/StaffView'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/fan" replace />} />
        <Route path="/fan/*" element={<FanApp />} />
        <Route path="/staff" element={<StaffView />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App