import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ArrowLeftRight, Settings, Zap, History } from 'lucide-react'
import clsx from 'clsx'

const links = [
  { to: '/',         label: 'Dashboard', icon: LayoutDashboard },
  { to: '/transfer', label: 'Transfer',  icon: ArrowLeftRight  },
  { to: '/history',  label: 'History',   icon: History          },
  { to: '/settings', label: 'Settings',  icon: Settings         },
]

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 flex flex-col bg-navy-800 border-r border-gray-800/60 min-h-screen">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-gray-800/60">
        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
          <Zap size={14} className="text-white" />
        </div>
        <span className="font-semibold text-sm text-gray-100 tracking-wide">ITP Dashboard</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150',
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60',
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-800/60">
        <p className="text-xs text-gray-600">Keys stored locally only</p>
      </div>
    </aside>
  )
}
