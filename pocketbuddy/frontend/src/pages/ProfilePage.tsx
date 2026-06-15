import { useState } from 'react'
import { User, Save } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const [form, setForm] = useState({
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    college_name: '',
    living_situation: '',
    monthly_budget: '',
    food_preferences: '',
    fitness_goals: '',
    sleep_goal_hours: '7',
    has_kitchen_access: false,
    college_start_time: '09:00',
    college_end_time: '17:00',
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload: any = {}
      if (form.age) payload.age = parseInt(form.age)
      if (form.gender) payload.gender = form.gender
      if (form.height_cm) payload.height_cm = parseFloat(form.height_cm)
      if (form.weight_kg) payload.weight_kg = parseFloat(form.weight_kg)
      if (form.college_name) payload.college_name = form.college_name
      if (form.living_situation) payload.living_situation = form.living_situation
      if (form.monthly_budget) payload.monthly_budget = parseFloat(form.monthly_budget)
      if (form.food_preferences) payload.food_preferences = form.food_preferences
      if (form.fitness_goals) payload.fitness_goals = form.fitness_goals
      payload.sleep_goal_hours = parseFloat(form.sleep_goal_hours)
      payload.has_kitchen_access = form.has_kitchen_access
      payload.college_start_time = form.college_start_time
      payload.college_end_time = form.college_end_time

      const { data } = await api.put('/auth/profile', payload)
      updateUser(data)
      toast.success('Profile updated! AI will now personalize your experience.')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <User className="w-6 h-6 text-primary-500" />
          Profile Setup
        </h1>
        <p className="text-surface-500">
          The more we know about you, the better PocketBuddy can personalize your experience
        </p>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-1">👤 Personal Info</h3>
        <p className="text-xs text-surface-500 mb-4">Helps us understand your lifestyle context</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-surface-600">Age</label>
            <input type="number" value={form.age} onChange={(e) => setForm({...form, age: e.target.value})} className="input-field mt-1" placeholder="20" />
          </div>
          <div>
            <label className="text-sm text-surface-600">Gender</label>
            <select value={form.gender} onChange={(e) => setForm({...form, gender: e.target.value})} className="input-field mt-1">
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-surface-600">College Name</label>
            <input type="text" value={form.college_name} onChange={(e) => setForm({...form, college_name: e.target.value})} className="input-field mt-1" placeholder="Your college" />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-1">🏠 Living Situation</h3>
        <p className="text-xs text-surface-500 mb-4">Affects routine and food recommendations</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-surface-600">Living Situation</label>
            <select value={form.living_situation} onChange={(e) => setForm({...form, living_situation: e.target.value})} className="input-field mt-1">
              <option value="">Select</option>
              <option value="hosteller">Hosteller</option>
              <option value="day_scholar">Day Scholar</option>
              <option value="rented">Rented Apartment</option>
              <option value="home">Living at Home</option>
            </select>
          </div>
          <div className="flex items-center gap-3 pt-6">
            <input
              type="checkbox"
              checked={form.has_kitchen_access}
              onChange={(e) => setForm({...form, has_kitchen_access: e.target.checked})}
              className="w-4 h-4 rounded text-primary-500"
            />
            <label className="text-sm text-surface-600">I have kitchen access</label>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-1">💰 Financial Info</h3>
        <p className="text-xs text-surface-500 mb-4">Helps with budget-aware recommendations</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-surface-600">Monthly Budget (₹)</label>
            <input type="number" value={form.monthly_budget} onChange={(e) => setForm({...form, monthly_budget: e.target.value})} className="input-field mt-1" placeholder="8000" />
          </div>
          <div>
            <label className="text-sm text-surface-600">Food Preferences</label>
            <input type="text" value={form.food_preferences} onChange={(e) => setForm({...form, food_preferences: e.target.value})} className="input-field mt-1" placeholder="Vegetarian, no spicy food, etc." />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-1">📅 Schedule</h3>
        <p className="text-xs text-surface-500 mb-4">Used for routine generation</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-surface-600">College Start Time</label>
            <input type="time" value={form.college_start_time} onChange={(e) => setForm({...form, college_start_time: e.target.value})} className="input-field mt-1" />
          </div>
          <div>
            <label className="text-sm text-surface-600">College End Time</label>
            <input type="time" value={form.college_end_time} onChange={(e) => setForm({...form, college_end_time: e.target.value})} className="input-field mt-1" />
          </div>
          <div>
            <label className="text-sm text-surface-600">Sleep Goal (hours)</label>
            <input type="number" step="0.5" min="4" max="12" value={form.sleep_goal_hours} onChange={(e) => setForm({...form, sleep_goal_hours: e.target.value})} className="input-field mt-1" />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-1">🏋️ Health & Fitness</h3>
        <p className="text-xs text-surface-500 mb-4">For wellness and activity tracking</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-surface-600">Height (cm)</label>
            <input type="number" value={form.height_cm} onChange={(e) => setForm({...form, height_cm: e.target.value})} className="input-field mt-1" placeholder="170" />
          </div>
          <div>
            <label className="text-sm text-surface-600">Weight (kg)</label>
            <input type="number" value={form.weight_kg} onChange={(e) => setForm({...form, weight_kg: e.target.value})} className="input-field mt-1" placeholder="65" />
          </div>
          <div>
            <label className="text-sm text-surface-600">Fitness Goals</label>
            <input type="text" value={form.fitness_goals} onChange={(e) => setForm({...form, fitness_goals: e.target.value})} className="input-field mt-1" placeholder="Stay active, lose weight, etc." />
          </div>
        </div>
      </div>

      <button onClick={handleSave} disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
        <Save className="w-4 h-4" />
        {saving ? 'Saving...' : 'Save Profile'}
      </button>
    </div>
  )
}
