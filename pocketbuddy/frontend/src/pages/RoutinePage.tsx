import { useState, useEffect } from 'react'
import { Calendar, Clock, Sparkles, Sun, Moon, Book, Dumbbell } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'

const routineTypes = [
  { id: 'daily', label: 'Daily Routine', icon: Sun, description: 'Standard balanced day' },
  { id: 'weekly', label: 'Weekly Plan', icon: Calendar, description: 'Week overview with variety' },
  { id: 'exam', label: 'Exam Mode', icon: Book, description: 'Study-focused with wellness breaks' },
  { id: 'budget_friendly', label: 'Budget Friendly', icon: Clock, description: 'Cost-optimized daily plan' },
]

const categoryIcons: Record<string, string> = {
  wellness: '',
  fitness: '',
  nutrition: '',
  academic: '',
  commute: '',
  social: '',
  default: '',
}

export default function RoutinePage() {
  const [routines, setRoutines] = useState<any[]>([])
  const [selectedType, setSelectedType] = useState('daily')
  const [generating, setGenerating] = useState(false)
  const [activeRoutine, setActiveRoutine] = useState<any>(null)
  const [time, setTime] = useState(new Date())
  const [reviewActivities, setReviewActivities] = useState<string[]>([])
  const [checkedActivities, setCheckedActivities] = useState<Set<string>>(new Set())
  const [reviewRoutineId, setReviewRoutineId] = useState<number | null>(null)
  const [reviewSaved, setReviewSaved] = useState(false)
  const [newTask, setNewTask] = useState('')
  const [replacingIndex, setReplacingIndex] = useState<number | null>(null)

  useEffect(() => {
    loadRoutines()
    loadYesterdayReview()
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const loadYesterdayReview = async () => {
    try {
      const { data } = await api.get('/ai/routine/yesterday-review')
      if (data.activities && data.activities.length > 0) {
        // Always limit to 10 activities
        setReviewActivities(data.activities.slice(0, 10))
        setReviewRoutineId(data.routine_id)
      }
    } catch (e) {}
  }

  const toggleActivity = (activity: string) => {
    setCheckedActivities(prev => {
      const next = new Set(prev)
      if (next.has(activity)) next.delete(activity)
      else next.add(activity)
      return next
    })
  }

  const replaceActivity = (index: number) => {
    setReplacingIndex(index)
    setNewTask('')
  }

  const confirmReplace = (index: number) => {
    if (!newTask.trim()) return
    setReviewActivities(prev => {
      const updated = [...prev]
      updated[index] = newTask.trim()
      return updated
    })
    // Auto-check the new task since user did it
    setCheckedActivities(prev => {
      const next = new Set(prev)
      next.add(newTask.trim())
      return next
    })
    setNewTask('')
    setReplacingIndex(null)
  }

  const addNewTask = () => {
    if (!newTask.trim()) return
    if (reviewActivities.length >= 10) {
      // Replace the last unchecked activity
      const uncheckedIdx = reviewActivities.findIndex(a => !checkedActivities.has(a))
      if (uncheckedIdx >= 0) {
        setReviewActivities(prev => {
          const updated = [...prev]
          updated[uncheckedIdx] = newTask.trim()
          return updated
        })
      }
    } else {
      setReviewActivities(prev => [...prev, newTask.trim()].slice(0, 10))
    }
    setCheckedActivities(prev => { const next = new Set(prev); next.add(newTask.trim()); return next })
    setNewTask('')
  }

  const submitReview = async () => {
    const completed = Array.from(checkedActivities)
    const skipped = reviewActivities.filter(a => !checkedActivities.has(a))
    
    console.log('Submitting review:', { completed, skipped, routine_id: reviewRoutineId })
    
    try {
      const res = await api.post('/ai/routine/log-completion', { 
        completed, 
        skipped, 
        routine_id: reviewRoutineId ? reviewRoutineId : null 
      })
      console.log('Review API response:', res.data)
      
      // Also save these as a memory for the AI
      // (routine_logs table is the source of truth - no chat message needed)
      
      setReviewSaved(true)
      toast.success(`Logged! ${completed.length}/${reviewActivities.length} completed. AI will use this for your next routine.`)
    } catch (e: any) {
      console.error('Submit review FAILED:', e.response?.status, e.response?.data, e.message)
      toast.error(`Failed: ${e.response?.data?.detail || e.message}`)
    }
  }

  // When selectedType changes, show the matching routine (latest one)
  useEffect(() => {
    const matching = routines
      .filter(r => r.routine_type === selectedType)
      .sort((a, b) => b.id - a.id)  // latest first
    setActiveRoutine(matching[0] || null)
  }, [selectedType, routines])

  const loadRoutines = async () => {
    try {
      const { data } = await api.get('/ai/routines')
      setRoutines(data)
    } catch (e) {
      console.error(e)
    }
  }

  const generateRoutine = async () => {
    setGenerating(true)
    try {
      const { data } = await api.post('/ai/routine/generate', {
        routine_type: selectedType,
      })
      toast.success('Routine generated!')
      setActiveRoutine(data)
      loadRoutines()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to generate routine')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Calendar className="w-6 h-6 text-primary-500" />
          Routine Planner
        </h1>
        <p className="text-surface-500">AI-generated personalized routines based on your lifestyle</p>
      </div>

      {/* Yesterday's Review Checklist */}
      {reviewActivities.length > 0 && !reviewSaved && (
        <div className="card" style={{ borderLeft: '4px solid var(--accent-orange)' }}>
          <h3 className="font-semibold mb-1 flex items-center gap-2">📋 Yesterday's Review</h3>
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>Check what you did. Replace tasks you didn't do with what you actually did instead.</p>
          <div className="space-y-2 mb-4">
            {reviewActivities.map((activity, i) => (
              <div key={i}>
                {replacingIndex === i ? (
                  <div className="flex items-center gap-2 p-2 rounded-lg" style={{ backgroundColor: 'var(--bg)' }}>
                    <input type="text" value={newTask} onChange={(e) => setNewTask(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && confirmReplace(i)} placeholder="What did you do instead?" className="input-field !py-2 text-sm flex-1" autoFocus />
                    <button onClick={() => confirmReplace(i)} className="text-xs px-3 py-1.5 rounded-lg font-medium" style={{ backgroundColor: 'var(--accent-orange)', color: '#fff' }}>Save</button>
                    <button onClick={() => setReplacingIndex(null)} className="text-xs px-2 py-1.5" style={{ color: 'var(--text-secondary)' }}>✕</button>
                  </div>
                ) : (
                  <label className="flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all group" style={{ backgroundColor: checkedActivities.has(activity) ? 'rgba(242,101,34,0.08)' : 'var(--bg)' }}>
                    <input type="checkbox" checked={checkedActivities.has(activity)} onChange={() => toggleActivity(activity)} className="w-4 h-4 rounded accent-orange-500" />
                    <span className={`text-sm flex-1 ${checkedActivities.has(activity) ? 'line-through opacity-60' : ''}`} style={{ color: 'var(--text-primary)' }}>{activity}</span>
                    {!checkedActivities.has(activity) && (
                      <button onClick={(e) => { e.preventDefault(); replaceActivity(i) }} className="opacity-0 group-hover:opacity-100 text-[10px] px-2 py-1 rounded" style={{ backgroundColor: 'var(--surface)', color: 'var(--text-secondary)' }}>Replace</button>
                    )}
                  </label>
                )}
              </div>
            ))}
          </div>

          {/* Add new task */}
          <div className="flex items-center gap-2 mb-4">
            <input type="text" value={replacingIndex === null ? newTask : ''} onChange={(e) => { if (replacingIndex === null) setNewTask(e.target.value) }} onKeyDown={(e) => e.key === 'Enter' && addNewTask()} placeholder="+ Add a task you did today..." className="input-field !py-2 text-sm flex-1" disabled={replacingIndex !== null} />
            <button onClick={addNewTask} disabled={!newTask.trim() || replacingIndex !== null} className="text-xs px-3 py-2 rounded-lg font-medium" style={{ backgroundColor: 'var(--accent-orange)', color: '#fff', opacity: !newTask.trim() ? 0.5 : 1 }}>Add</button>
          </div>

          <div className="flex items-center gap-3">
            <button onClick={submitReview} className="btn-primary text-sm !py-2">Submit Review</button>
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{checkedActivities.size}/{reviewActivities.length} completed</span>
          </div>
        </div>
      )}

      {reviewSaved && (
        <div className="card flex items-center gap-3" style={{ borderLeft: '4px solid #10b981' }}>
          <span>✅</span>
          <p className="text-sm" style={{ color: 'var(--text-primary)' }}>Yesterday's review saved! AI will use this to improve your routines.</p>
        </div>
      )}

      {/* Routine Type Selector */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {routineTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setSelectedType(type.id)}
            className={`card-hover text-left transition-all ${
              selectedType === type.id
                ? '!border-primary-500 !bg-primary-50'
                : ''
            }`}
          >
            <type.icon className={`w-8 h-8 mb-2 ${selectedType === type.id ? 'text-primary-500' : 'text-surface-400'}`} />
            <h4 className="font-semibold text-sm">{type.label}</h4>
            <p className="text-xs text-surface-500 mt-1">{type.description}</p>
          </button>
        ))}
      </div>

      {/* Generate Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={generateRoutine}
          disabled={generating}
          className="btn-primary flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          {generating ? 'Generating with AI...' : `Generate ${selectedType.replace('_', ' ')} routine`}
        </button>
        {generating && (
          <p className="text-sm text-surface-500 animate-pulse">
            AI is crafting your personalized routine...
          </p>
        )}
      </div>

      {/* Active Routine Display */}
      {activeRoutine && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold">{activeRoutine.name}</h3>
              <p className="text-sm text-surface-500 capitalize">{activeRoutine.routine_type} routine</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="px-4 py-2 bg-surface-900 rounded-xl text-white font-mono text-lg tracking-wider">
                {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
              </div>
              <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                Active
              </span>
            </div>
          </div>

          {/* Timeline */}
          <div className="relative ml-2">
            <div className="absolute left-[52px] top-0 bottom-0 w-0.5" style={{ backgroundColor: 'var(--border)' }} />
            <div className="space-y-0">
              {activeRoutine.schedule?.map((item: any, i: number) => {
                // Check if this is the current activity
                const now = time
                const currentMinutes = now.getHours() * 60 + now.getMinutes()
                const [h, m] = (item.time || '00:00').split(':').map(Number)
                const itemMinutes = h * 60 + m
                const nextItem = activeRoutine.schedule[i + 1]
                const nextMinutes = nextItem ? (parseInt(nextItem.time?.split(':')[0] || '24') * 60 + parseInt(nextItem.time?.split(':')[1] || '0')) : 1440
                const isCurrent = currentMinutes >= itemMinutes && currentMinutes < nextMinutes
                const isPast = currentMinutes > nextMinutes

                return (
                  <div key={i} className={`flex items-center gap-3 relative py-2 px-2 rounded-xl transition-all ${isCurrent ? 'scale-[1.02]' : ''}`} style={isCurrent ? { backgroundColor: 'rgba(242,101,34,0.08)' } : {}}>
                    <div className="w-14 flex-shrink-0 text-right">
                      <span className={`text-xs font-mono font-medium ${isCurrent ? 'text-[var(--accent-orange)] font-bold' : ''}`} style={{ color: isCurrent ? 'var(--accent-orange)' : isPast ? 'var(--text-secondary)' : 'var(--text-primary)' }}>{item.time}</span>
                    </div>
                    <div className={`rounded-full z-10 flex-shrink-0 transition-all ${isCurrent ? 'w-4 h-4 ring-4 ring-orange-200' : 'w-3 h-3'}`} style={{ backgroundColor: isCurrent ? 'var(--accent-orange)' : isPast ? 'var(--text-secondary)' : 'var(--accent-orange)' }} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span>{categoryIcons[item.category] || categoryIcons.default}</span>
                        <span className={`text-sm ${isCurrent ? 'font-bold' : 'font-medium'}`} style={{ color: isPast ? 'var(--text-secondary)' : 'var(--text-primary)' }}>{item.activity}</span>
                        {isCurrent && <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-orange-100 text-orange-700 animate-pulse">NOW</span>}
                      </div>
                      {item.notes && (
                        <p className="text-xs mt-0.5 ml-6" style={{ color: 'var(--text-secondary)' }}>{item.notes}</p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Saved Routines of this type */}
      {routines.filter(r => r.routine_type === selectedType).length > 1 && (
        <div className="card">
          <h3 className="font-semibold mb-4">Saved {selectedType.replace('_', ' ')} Routines</h3>
          <div className="space-y-2">
            {routines.filter(r => r.routine_type === selectedType).map((routine) => (
              <button
                key={routine.id}
                onClick={() => setActiveRoutine(routine)}
                className={`w-full text-left p-3 rounded-xl border transition-colors ${
                  activeRoutine?.id === routine.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-surface-100 hover:border-primary-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{routine.name}</p>
                    <p className="text-xs text-surface-500 capitalize">{routine.routine_type}</p>
                  </div>
                  <span className="text-xs text-surface-400">
                    {routine.schedule?.length} activities
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
