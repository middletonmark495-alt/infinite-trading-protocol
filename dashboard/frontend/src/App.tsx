import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Transfer from './pages/Transfer'
import History from './pages/History'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/transfer" element={<Transfer />}  />
          <Route path="/history"  element={<History />}   />
          <Route path="/settings" element={<Settings />}  />
        </Routes>
      </main>
    </div>
  )
}
