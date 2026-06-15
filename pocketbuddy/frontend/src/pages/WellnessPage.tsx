import { useState, useEffect } from 'react'
import { Heart, Moon, Brain, Apple, Activity, Smile, Plus } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function WellnessPage() {
  const [score, setScore] = useState<any>(null)
  const [trends, setTrends] = useState<any>(null)
  const [showCheckin, setShowCheckin] = useState(false)
  const [checkinForm, setCheckinForm] = useState({ mood_score: 5, stress_score: 5, sleep_hours: 7, meals_skipped: 0, water_glasses: 4, study_hours: 3, exercise_minutes: 0, journal_entry: '' })

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [s, t] = await Promise.allSettled([api.get('/wellness/score'), api.get('/wellness/trends?days=30')])
      if (s.status === 'fulfilled') setScore(s.value.data)
      if (t.status === 'fulfilled') setTrends(t.value.data)
    } catch (e) { console.error(e) }
  }

  const submitCheckin = async () => {
    try {
      await api.post('/wellness/checkin', { ...checkinForm, date: new Date().toISOString().split('T')[0] })
      toast.success('Check-in recorded!')
      setShowCheckin(false)
      loadData()
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const radarData = score ? [
    { metric: 'Sleep', value: score.sleep_quality }, { metric: 'Stress Mgmt', value: score.stress_management },
    { metric: 'Nutrition', value: score.nutrition_score }, { metric: 'Activity', value: score.activity_score }, { metric: 'Mood', value: score.mood_stability },
  ] : []

  const trendData = trends?.dates?.map((d: string, i: number) => ({ date: d.slice(5), mood: trends.mood_scores[i], stress: trends.stress_scores[i], sleep: trends.sleep_hours[i] })) || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold flex items-center gap-2"><Heart className="w-6 h-6 text-emerald-500" />Wellness Tracker</h1><p className="text-surface-500">Monitor your physical and mental wellbeing</p></div>
        <button onClick={() => setShowCheckin(!showCheckin)} className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" />Daily Check-in</button>
      </div>

      {showCheckin && (
        <div className="card border-2 border-primary-200 bg-primary-50/30">
          <h3 className="font-semibold mb-4">How are you doing today?</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div><label className="text-sm text-surface-600 flex items-center gap-1"><Smile className="w-4 h-4" />Mood (1-10)</label><input type="range" min="1" max="10" value={checkinForm.mood_score} onChange={(e) => setCheckinForm({...checkinForm, mood_score: +e.target.value})} className="w-full mt-1" /><span className="text-sm font-medium">{checkinForm.mood_score}/10</span></div>
            <div><label className="text-sm text-surface-600 flex items-center gap-1"><Brain className="w-4 h-4" />Stress (1-10)</label><input type="range" min="1" max="10" value={checkinForm.stress_score} onChange={(e) => setCheckinForm({...checkinForm, stress_score: +e.target.value})} className="w-full mt-1" /><span className="text-sm font-medium">{checkinForm.stress_score}/10</span></div>
            <div><label className="text-sm text-surface-600 flex items-center gap-1"><Moon className="w-4 h-4" />Sleep Hours</label><input type="number" min="0" max="14" step="0.5" value={checkinForm.sleep_hours} onChange={(e) => setCheckinForm({...checkinForm, sleep_hours: +e.target.value})} className="input-field mt-1" /></div>
            <div><label className="text-sm text-surface-600 flex items-center gap-1"><Apple className="w-4 h-4" />Meals Skipped</label><input type="number" min="0" max="3" value={checkinForm.meals_skipped} onChange={(e) => setCheckinForm({...checkinForm, meals_skipped: +e.target.value})} className="input-field mt-1" /></div>
            <div><label className="text-sm text-surface-600">Water (glasses)</label><input type="number" min="0" max="20" value={checkinForm.water_glasses} onChange={(e) => setCheckinForm({...checkinForm, water_glasses: +e.target.value})} className="input-field mt-1" /></div>
            <div><label className="text-sm text-surface-600">Study Hours</label><input type="number" min="0" max="16" step="0.5" value={checkinForm.study_hours} onChange={(e) => setCheckinForm({...checkinForm, study_hours: +e.target.value})} className="input-field mt-1" /></div>
            <div><label className="text-sm text-surface-600 flex items-center gap-1"><Activity className="w-4 h-4" />Exercise (min)</label><input type="number" min="0" max="180" value={checkinForm.exercise_minutes} onChange={(e) => setCheckinForm({...checkinForm, exercise_minutes: +e.target.value})} className="input-field mt-1" /></div>
            <div><label className="text-sm text-surface-600">Journal</label><input type="text" value={checkinForm.journal_entry} onChange={(e) => setCheckinForm({...checkinForm, journal_entry: e.target.value})} className="input-field mt-1" placeholder="How was your day?" /></div>
          </div>
          <button onClick={submitCheckin} className="btn-primary">Submit Check-in</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold mb-4">Wellness Breakdown</h3>
          {radarData.length > 0 ? (<ResponsiveContainer width="100%" height={300}><RadarChart data={radarData}><PolarGrid stroke="#888888" /><PolarAngleAxis dataKey="metric" tick={{fontSize:12}} /><PolarRadiusAxis angle={30} domain={[0,100]} tick={{fontSize:10}} stroke="#888888" /><Radar name="Score" dataKey="value" stroke="#f97316" fill="#f97316" fillOpacity={0.2} /></RadarChart></ResponsiveContainer>) : (<div className="h-[300px] flex items-center justify-center text-surface-400">Complete a check-in to see your breakdown</div>)}
        </div>
        <div className="card">
          <h3 className="font-semibold mb-4">Current Scores</h3>
          <div className="space-y-4">
            {[{label:'Overall',value:score?.overall_wellness,icon:Heart},{label:'Sleep',value:score?.sleep_quality,icon:Moon},{label:'Stress Mgmt',value:score?.stress_management,icon:Brain},{label:'Nutrition',value:score?.nutrition_score,icon:Apple},{label:'Activity',value:score?.activity_score,icon:Activity},{label:'Mood',value:score?.mood_stability,icon:Smile}].map((item) => (
              <div key={item.label} className="flex items-center gap-3"><item.icon className="w-5 h-5 text-surface-500" /><div className="flex-1"><div className="flex justify-between mb-1"><span className="text-sm">{item.label}</span><span className="text-sm font-semibold">{Math.round(item.value||50)}/100</span></div><div className="h-2 bg-surface-100 rounded-full overflow-hidden"><div className="h-full bg-primary-500 rounded-full transition-all" style={{width:`${item.value||50}%`}} /></div></div></div>
            ))}
          </div>
          {score?.burnout_risk && (<div className={`mt-4 p-3 rounded-xl ${score.burnout_risk==='low'?'bg-green-50 text-green-700':score.burnout_risk==='medium'?'bg-yellow-50 text-yellow-700':'bg-red-50 text-red-700'}`}><span className="text-sm font-medium">Burnout Risk: {score.burnout_risk.charAt(0).toUpperCase()+score.burnout_risk.slice(1)}</span></div>)}
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">30-Day Trends</h3>
        {trendData.length > 0 ? (<ResponsiveContainer width="100%" height={300}><LineChart data={trendData}><CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" /><XAxis dataKey="date" tick={{fontSize:12}} /><YAxis tick={{fontSize:12}} /><Tooltip /><Line type="monotone" dataKey="mood" stroke="#10b981" name="Mood" strokeWidth={2} /><Line type="monotone" dataKey="stress" stroke="#ef4444" name="Stress" strokeWidth={2} /><Line type="monotone" dataKey="sleep" stroke="#3b82f6" name="Sleep" strokeWidth={2} /></LineChart></ResponsiveContainer>) : (<div className="h-[300px] flex items-center justify-center text-surface-400">Start logging daily check-ins to see trends</div>)}
      </div>
    </div>
  )
}
