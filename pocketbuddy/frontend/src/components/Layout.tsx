import { useState, useRef, useEffect } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Wallet,
  Heart,
  MessageCircle,
  Calendar,
  FileText,
  User,
  Settings,
  Bot,
  LogOut,
  Menu,
  Sun,
  Moon,
  Bell,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/financial', icon: Wallet, label: 'Financial' },
  { to: '/wellness', icon: Heart, label: 'Wellness' },
  { to: '/chat', icon: MessageCircle, label: 'AI Chat' },
  { to: '/routine', icon: Calendar, label: 'Routine' },
  { to: '/reports', icon: FileText, label: 'Reports' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const { dark, toggle } = useThemeStore()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const notifRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [dark])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setDropdownOpen(false)
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Load notifications
  useEffect(() => {
    const loadNotifs = async () => {
      try {
        const [notifRes, countRes] = await Promise.allSettled([
          import('../lib/api').then(m => m.default.get('/notifications?unread_only=true&limit=10')),
          import('../lib/api').then(m => m.default.get('/notifications/unread-count')),
        ])
        if (notifRes.status === 'fulfilled') setNotifications(notifRes.value.data)
        if (countRes.status === 'fulfilled') setUnreadCount(countRes.value.data.count)
      } catch (e) {}
    }
    loadNotifs()
    const interval = setInterval(loadNotifs, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col h-screen transition-colors duration-300" style={{ backgroundColor: 'var(--bg)' }}>
      {/* Top Navbar */}
      <nav
        className="backdrop-blur-md border-b px-6 py-3 flex items-center justify-between sticky top-0 z-50 transition-all duration-300"
        style={{ backgroundColor: 'var(--nav-bg)', borderColor: 'var(--border)' }}
      >
        {/* Left - Logo + Nav */}
        <div className="flex items-center gap-8">
          <NavLink to="/" className="flex items-center gap-2">
            <img src="/logo.png" alt="PocketBuddy" className="w-9 h-9 rounded-xl" />
            <span className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>PocketBuddy</span>
          </NavLink>

          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive ? 'nav-active' : 'nav-inactive'
                  )
                }
                style={({ isActive }) => ({
                  backgroundColor: isActive ? 'rgba(242, 101, 34, 0.1)' : 'transparent',
                  color: isActive ? 'var(--accent-orange)' : 'var(--text-secondary)',
                })}
              >
                <item.icon className="w-4 h-4" />
                <span className="hidden lg:inline">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          {/* Notification Bell */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setNotifOpen(!notifOpen)}
              className="p-2.5 rounded-xl transition-all duration-200 hover:scale-105 relative"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <Bell className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full text-white text-xs flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--accent-orange)' }}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {notifOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-2xl shadow-xl py-2 z-50 border max-h-96 overflow-y-auto" style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border)' }}>
                <div className="px-4 py-2 border-b flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
                  <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Notifications</span>
                  {unreadCount > 0 && (
                    <button onClick={async () => { try { const api = (await import('../lib/api')).default; await api.post('/notifications/mark-all-read'); setUnreadCount(0); setNotifications([]) } catch(e){} }} className="text-xs" style={{ color: 'var(--accent-orange)' }}>Mark all read</button>
                  )}
                </div>
                {notifications.length > 0 ? notifications.map((n) => (
                  <div key={n.id} className={`px-4 py-3 border-b transition-all cursor-pointer hover:opacity-80 ${!n.is_read ? 'border-l-2' : ''}`} style={{ borderColor: 'var(--border)', borderLeftColor: !n.is_read ? 'var(--accent-orange)' : 'transparent', backgroundColor: !n.is_read ? 'rgba(242,101,34,0.03)' : 'transparent' }} onClick={async () => { try { const api = (await import('../lib/api')).default; await api.post(`/notifications/${n.id}/read`) } catch(e){}; setNotifications(prev => prev.filter(x => x.id !== n.id)); setUnreadCount(c => Math.max(0, c-1)); if (n.action_url) navigate(n.action_url); setNotifOpen(false) }}>
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{n.title}</p>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0 ${n.priority === 'critical' ? 'bg-red-100 text-red-700' : n.priority === 'high' ? 'bg-orange-100 text-orange-700' : n.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'}`}>{n.priority}</span>
                    </div>
                    <p className="text-xs mt-1 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>{n.message}</p>
                  </div>
                )) : (
                  <p className="px-4 py-8 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>No notifications yet</p>
                )}
              </div>
            )}
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggle}
            className="p-2.5 rounded-xl transition-all duration-200 hover:scale-105"
            style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            title={dark ? 'Light mode' : 'Dark mode'}
          >
            {dark ? <Sun className="w-4 h-4" style={{ color: '#FF6A00' }} /> : <Moon className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />}
          </button>

          {/* User Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200"
              style={{ backgroundColor: dropdownOpen ? 'var(--surface)' : 'transparent' }}
            >
              <div className="w-8 h-8 rounded-full flex items-center justify-center overflow-hidden" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <span className="font-semibold text-sm" style={{ color: 'var(--accent-orange)' }}>
                    {user?.full_name?.charAt(0) || 'U'}
                  </span>
                )}
              </div>
              <span className="text-sm font-medium hidden sm:inline" style={{ color: 'var(--text-primary)' }}>{user?.full_name?.split(' ')[0]}</span>
              <Menu className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
            </button>

            {dropdownOpen && (
              <div
                className="absolute right-0 mt-2 w-56 rounded-2xl shadow-xl py-2 z-50 border"
                style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border)' }}
              >
                <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>{user?.full_name}</p>
                  <p className="text-xs truncate mt-0.5" style={{ color: 'var(--text-secondary)' }}>{user?.email}</p>
                </div>
                <NavLink to="/profile" onClick={() => setDropdownOpen(false)} className="flex items-center gap-3 px-4 py-2.5 text-sm transition-all hover:opacity-80" style={{ color: 'var(--text-primary)' }}>
                  <User className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} /> Profile
                </NavLink>
                <NavLink to="/settings" onClick={() => setDropdownOpen(false)} className="flex items-center gap-3 px-4 py-2.5 text-sm transition-all hover:opacity-80" style={{ color: 'var(--text-primary)' }}>
                  <Settings className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} /> Settings
                </NavLink>
                <div className="border-t mt-1 pt-1" style={{ borderColor: 'var(--border)' }}>
                  <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-2.5 text-sm w-full transition-all hover:opacity-80" style={{ color: 'var(--accent-orange)' }}>
                    <LogOut className="w-4 h-4" /> Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6 md:p-8 max-w-7xl mx-auto animate-fade-up">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
