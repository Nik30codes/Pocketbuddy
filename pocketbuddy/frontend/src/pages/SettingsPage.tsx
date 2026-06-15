import { useState, useRef } from 'react'
import { Settings, LogOut, Trash2, Camera, AlertTriangle, PenLine } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user, logout, updateUser } = useAuthStore()
  const navigate = useNavigate()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteText, setDeleteText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [newName, setNewName] = useState(user?.full_name || '')
  const [savingName, setSavingName] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleLogout = () => {
    logout()
    toast.success('Logged out')
    navigate('/login')
  }

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      // Convert to base64 data URL for simple storage
      const reader = new FileReader()
      reader.onload = async (ev) => {
        const avatarUrl = ev.target?.result as string
        await api.put('/auth/profile', { avatar_url: avatarUrl })
        updateUser({ avatar_url: avatarUrl })
        toast.success('Profile picture updated!')
      }
      reader.readAsDataURL(file)
    } catch (e) {
      toast.error('Failed to update picture')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteText !== 'DELETE') return
    try {
      await api.delete('/auth/account')
      logout()
      toast.success('Account deleted')
      navigate('/login')
    } catch (e) {
      toast.error('Failed to delete account')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Settings className="w-6 h-6 text-primary-500" />
          Settings
        </h1>
        <p className="text-surface-500">Manage your account</p>
      </div>

      {/* Profile Picture */}
      <div className="card">
        <h3 className="font-semibold mb-4">Profile Picture</h3>
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden border-2 border-primary-200">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <span className="text-2xl font-bold text-primary-600">
                  {user?.full_name?.charAt(0) || 'U'}
                </span>
              )}
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="absolute -bottom-1 -right-1 w-8 h-8 bg-primary-500 text-white rounded-full flex items-center justify-center shadow-md hover:bg-primary-600 transition-colors"
            >
              <Camera className="w-4 h-4" />
            </button>
          </div>
          <div>
            <p className="font-medium">{user?.full_name}</p>
            <p className="text-sm text-surface-500">{user?.email}</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="mt-2 text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              {uploading ? 'Uploading...' : 'Change photo'}
            </button>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleAvatarChange}
            accept="image/*"
            className="hidden"
          />
        </div>
      </div>

      {/* Change Username */}
      <div className="card">
        <h3 className="font-semibold mb-2 flex items-center gap-2"><PenLine className="w-5 h-5 text-primary-500" />Change Name</h3>
        <p className="text-sm text-surface-500 mb-4">Update your display name.</p>
        <div className="flex gap-3">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="input-field flex-1"
            placeholder="Your name"
          />
          <button
            onClick={async () => {
              if (!newName.trim()) return
              setSavingName(true)
              try {
                await api.put('/auth/profile', { full_name: newName.trim() })
                updateUser({ full_name: newName.trim() })
                toast.success('Name updated!')
              } catch (e) { toast.error('Failed to update name') }
              finally { setSavingName(false) }
            }}
            disabled={savingName || newName.trim() === user?.full_name}
            className="btn-primary"
          >
            {savingName ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Logout */}
      <div className="card">
        <h3 className="font-semibold mb-2">Session</h3>
        <p className="text-sm text-surface-500 mb-4">Sign out of your account on this device.</p>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-4 py-2.5 bg-surface-100 text-surface-700 rounded-xl hover:bg-surface-200 transition-colors font-medium text-sm"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>

      {/* Delete Account */}
      <div className="card border-red-200 bg-red-50/30">
        
        <p className="text-sm text-surface-600 mb-4">
          Permanently delete your account and all associated data. This action cannot be undone.
        </p>

        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-red-100 text-red-700 rounded-xl hover:bg-red-200 transition-colors font-medium text-sm"
          >
            <Trash2 className="w-4 h-4" />
            Delete Account
          </button>
        ) : (
          <div className="p-4 bg-white border border-red-200 rounded-xl space-y-3">
            <p className="text-sm font-medium text-red-700">
              Type <span className="font-mono bg-red-100 px-1.5 py-0.5 rounded">DELETE</span> to confirm:
            </p>
            <input
              type="text"
              value={deleteText}
              onChange={(e) => setDeleteText(e.target.value)}
              className="input-field border-red-200 focus:border-red-500 focus:ring-red-500/20"
              placeholder="Type DELETE"
            />
            <div className="flex gap-2">
              <button
                onClick={handleDeleteAccount}
                disabled={deleteText !== 'DELETE'}
                className="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Permanently Delete
              </button>
              <button
                onClick={() => { setShowDeleteConfirm(false); setDeleteText('') }}
                className="px-4 py-2 bg-surface-100 text-surface-600 rounded-xl text-sm font-medium hover:bg-surface-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
