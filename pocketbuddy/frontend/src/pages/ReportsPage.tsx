import { useState, useEffect } from 'react'
import { FileText, Download, Sparkles, Calendar, TrendingUp, TrendingDown } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function ReportsPage() {
  const [monthlyReports, setMonthlyReports] = useState<any[]>([])
  const [weeklyReports, setWeeklyReports] = useState<any[]>([])
  const [generating, setGenerating] = useState(false)
  const [selectedReport, setSelectedReport] = useState<any>(null)
  const [tab, setTab] = useState<'monthly' | 'weekly'>('monthly')
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  useEffect(() => { loadReports() }, [])

  const loadReports = async () => {
    try {
      const [monthly, weekly] = await Promise.allSettled([
        api.get('/reports/monthly'),
        api.get('/reports/weekly'),
      ])
      if (monthly.status === 'fulfilled') {
        setMonthlyReports(monthly.value.data)
        if (monthly.value.data.length > 0 && !selectedReport) setSelectedReport(monthly.value.data[0])
      }
      if (weekly.status === 'fulfilled') setWeeklyReports(weekly.value.data)
    } catch (e) {}
  }

  const generateMonthlyReport = async () => {
    setGenerating(true)
    try {
      const { data } = await api.post(`/reports/monthly/generate?month=${selectedMonth}`)
      toast.success(`Monthly report for ${selectedMonth} generated!`)
      setSelectedReport(data)
      loadReports()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to generate report')
    } finally { setGenerating(false) }
  }

  const generateWeeklyReport = async () => {
    setGenerating(true)
    try {
      const { data } = await api.post('/reports/weekly/generate')
      toast.success('Weekly report generated!')
      loadReports()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed')
    } finally { setGenerating(false) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="w-6 h-6" style={{ color: 'var(--accent-orange)' }} />
            Reports
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Monthly & weekly life reports with insights</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button onClick={() => setTab('monthly')} className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${tab === 'monthly' ? 'text-white' : ''}`} style={{ backgroundColor: tab === 'monthly' ? 'var(--accent-orange)' : 'var(--surface)', color: tab === 'monthly' ? '#fff' : 'var(--text-primary)' }}>
          Monthly Reports
        </button>
        <button onClick={() => setTab('weekly')} className={`px-4 py-2 rounded-full text-sm font-medium transition-all`} style={{ backgroundColor: tab === 'weekly' ? 'var(--accent-orange)' : 'var(--surface)', color: tab === 'weekly' ? '#fff' : 'var(--text-primary)' }}>
          Weekly Reports
        </button>
      </div>

      {tab === 'monthly' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Month selector + generate */}
          <div className="card space-y-4">
            <h3 className="font-semibold flex items-center gap-2"><Calendar className="w-5 h-5" style={{ color: 'var(--accent-orange)' }} /> Select Month</h3>
            <input type="month" value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} className="input-field" />
            <button onClick={generateMonthlyReport} disabled={generating} className="btn-primary w-full flex items-center justify-center gap-2">
              <Sparkles className="w-4 h-4" />
              {generating ? 'Generating...' : 'Generate Report'}
            </button>

            <div className="border-t pt-4 mt-4" style={{ borderColor: 'var(--border)' }}>
              <h4 className="text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>Past Reports</h4>
              {monthlyReports.length > 0 ? (
                <div className="space-y-2">
                  {monthlyReports.map((r) => (
                    <button key={r.id} onClick={() => setSelectedReport(r)} className={`w-full text-left p-3 rounded-xl border transition-all ${selectedReport?.id === r.id ? 'border-[var(--accent-orange)]' : ''}`} style={{ borderColor: selectedReport?.id === r.id ? 'var(--accent-orange)' : 'var(--border)', backgroundColor: selectedReport?.id === r.id ? 'rgba(242,101,34,0.05)' : 'transparent' }}>
                      <p className="font-medium text-sm">{r.month}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>₹{r.total_expenses?.toLocaleString()} spent</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${r.burnout_risk === 'low' ? 'bg-green-100 text-green-700' : r.burnout_risk === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>{r.burnout_risk}</span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-center py-4" style={{ color: 'var(--text-secondary)' }}>No reports yet</p>
              )}
            </div>
          </div>

          {/* Right: Report detail */}
          <div className="lg:col-span-2">
            {selectedReport ? (
              <div className="card space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold"> {selectedReport.month} Report</h3>
                </div>

                {/* Scores */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                    <p className="text-2xl font-bold" style={{ color: 'var(--accent-orange)' }}>{Math.round(selectedReport.financial_score)}</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Financial Score</p>
                  </div>
                  <div className="p-4 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                    <p className="text-2xl font-bold" style={{ color: 'var(--accent-purple)' }}>{Math.round(selectedReport.wellness_score)}</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Wellness Score</p>
                  </div>
                  <div className="p-4 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                    <p className={`text-2xl font-bold capitalize ${selectedReport.burnout_risk === 'low' ? 'text-green-600' : selectedReport.burnout_risk === 'medium' ? 'text-yellow-600' : 'text-red-600'}`}>{selectedReport.burnout_risk}</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Burnout Risk</p>
                  </div>
                </div>

                {/* Financial */}
                <div>
                  <h4 className="font-semibold text-sm mb-2"> Financial Summary</h4>
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg)' }}>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Income</p>
                      <p className="font-bold text-green-600">₹{selectedReport.total_income?.toLocaleString()}</p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg)' }}>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Expenses</p>
                      <p className="font-bold text-red-600">₹{selectedReport.total_expenses?.toLocaleString()}</p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg)' }}>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Savings</p>
                      <p className={`font-bold ${selectedReport.savings >= 0 ? 'text-green-600' : 'text-red-600'}`}>₹{selectedReport.savings?.toLocaleString()}</p>
                    </div>
                  </div>
                  <p className="text-sm p-3 rounded-xl" style={{ backgroundColor: 'var(--bg)', color: 'var(--text-primary)' }}>{selectedReport.financial_summary}</p>
                </div>

                {/* Wellness */}
                {selectedReport.avg_mood && (
                  <div>
                    <h4 className="font-semibold text-sm mb-2"> Wellness Summary</h4>
                    <div className="grid grid-cols-4 gap-3 mb-3">
                      <div className="p-3 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                        <p className="text-lg font-bold">{selectedReport.avg_mood?.toFixed(1)}</p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Mood</p>
                      </div>
                      <div className="p-3 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                        <p className="text-lg font-bold">{selectedReport.avg_stress?.toFixed(1)}</p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Stress</p>
                      </div>
                      <div className="p-3 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                        <p className="text-lg font-bold">{selectedReport.avg_sleep?.toFixed(1)}h</p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Sleep</p>
                      </div>
                      <div className="p-3 rounded-xl text-center" style={{ backgroundColor: 'var(--bg)' }}>
                        <p className="text-lg font-bold">{selectedReport.total_checkins}</p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Check-ins</p>
                      </div>
                    </div>
                    <p className="text-sm p-3 rounded-xl" style={{ backgroundColor: 'var(--bg)' }}>{selectedReport.wellness_summary}</p>
                  </div>
                )}

                {/* Highlights & Improvements */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedReport.highlights?.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-sm mb-2 flex items-center gap-1"><TrendingUp className="w-4 h-4 text-green-600" /> Highlights</h4>
                      <div className="space-y-2">
                        {selectedReport.highlights.map((h: string, i: number) => (
                          <p key={i} className="text-sm p-2 rounded-lg bg-green-50 text-green-800">✅ {h}</p>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedReport.areas_to_improve?.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-sm mb-2 flex items-center gap-1"><TrendingDown className="w-4 h-4 text-orange-600" /> Areas to Improve</h4>
                      <div className="space-y-2">
                        {selectedReport.areas_to_improve.map((a: string, i: number) => (
                          <p key={i} className="text-sm p-2 rounded-lg bg-orange-50 text-orange-800"> {a}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="card flex items-center justify-center h-64">
                <div className="text-center" style={{ color: 'var(--text-secondary)' }}>
                  <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Select a month and generate your report</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'weekly' && (
        <div className="space-y-4">
          <button onClick={generateWeeklyReport} disabled={generating} className="btn-primary flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> {generating ? 'Generating...' : 'Generate Weekly Report'}
          </button>
          {weeklyReports.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {weeklyReports.map((r) => (
                <div key={r.id} className="card">
                  <p className="font-semibold text-sm">{r.week_start} — {r.week_end}</p>
                  <div className="flex gap-3 mt-2">
                    <span className="text-xs px-2 py-1 rounded-full" style={{ backgroundColor: 'var(--bg)' }}> {Math.round(r.financial_score)}</span>
                    <span className="text-xs px-2 py-1 rounded-full" style={{ backgroundColor: 'var(--bg)' }}> {Math.round(r.wellness_score)}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${r.burnout_risk === 'low' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{r.burnout_risk}</span>
                  </div>
                  <p className="text-sm mt-3" style={{ color: 'var(--text-secondary)' }}>{r.financial_summary}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8" style={{ color: 'var(--text-secondary)' }}>No weekly reports yet</p>
          )}
        </div>
      )}
    </div>
  )
}
