import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bot, Mail, Lock, ArrowRight } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setAuth(data.access_token, data.user)
      toast.success('Welcome back!')
      navigate('/')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-50 flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-500 to-primary-700 p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <img src="/logo.png" alt="PB" className="w-10 h-10 rounded-xl" />
          </div>
          <h1 className="text-2xl font-bold text-white">PocketBuddy</h1>
        </div>
        <div>
          <h2 className="text-4xl font-bold text-white leading-tight mb-4">Your AI-Powered<br />Student Life Coach</h2>
          <p className="text-primary-100 text-lg max-w-md">Manage finances, track wellness, prevent burnout, and build better routines — all with intelligent AI guidance.</p>
        </div>
        <div className="flex gap-8">
          <div><p className="text-3xl font-bold text-white">6</p><p className="text-primary-200 text-sm">AI Agents</p></div>
          <div><p className="text-3xl font-bold text-white">360°</p><p className="text-primary-200 text-sm">Life View</p></div>
          <div><p className="text-3xl font-bold text-white">24/7</p><p className="text-primary-200 text-sm">Support</p></div>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center"><img src="/logo.png" alt="PB" className="w-8 h-8 rounded-lg" /></div>
            <h1 className="text-xl font-bold">PocketBuddy</h1>
          </div>
          <h2 className="text-2xl font-bold mb-2">Welcome back</h2>
          <p className="text-surface-500 mb-8">Sign in to your account to continue</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-surface-700 mb-1 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field pl-11" placeholder="you@college.edu" required />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-surface-700 mb-1 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field pl-11" placeholder="••••••••" required />
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading ? 'Signing in...' : 'Sign In'}<ArrowRight className="w-4 h-4" />
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-surface-500">
            Don't have an account?{' '}<Link to="/register" className="text-primary-600 font-medium hover:text-primary-700">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
