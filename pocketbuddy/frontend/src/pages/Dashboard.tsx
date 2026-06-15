import { useEffect, useState } from 'react'
import {
  Wallet,
  Heart,
  Brain,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  Sun,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import ScoreCard from '../components/ScoreCard'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'

const COLORS = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4']

export default function Dashboard() {
  const { user } = useAuthStore()
  const [wellnessScore, setWellnessScore] = useState<any>(null)
  const [financialSummary, setFinancialSummary] = useState<any>(null)
  const [trends, setTrends] = useState<any>(null)
  const [predictions, setPredictions] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [wellnessRes, financialRes, trendsRes, predictionsRes] = await Promise.allSettled([
        api.get('/wellness/score'),
        api.get('/financial/summary'),
        api.get('/wellness/trends?days=14'),
        api.get('/ai/predictions'),
      ])

      if (wellnessRes.status === 'fulfilled') setWellnessScore(wellnessRes.value.data)
      if (financialRes.status === 'fulfilled') setFinancialSummary(financialRes.value.data)
      if (trendsRes.status === 'fulfilled') setTrends(trendsRes.value.data)
      if (predictionsRes.status === 'fulfilled') setPredictions(predictionsRes.value.data)
    } catch (error) {
      console.error('Dashboard load error:', error)
    } finally {
      setLoading(false)
    }
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  const trendData = trends?.dates?.map((d: string, i: number) => ({
    date: d.slice(5),
    mood: trends.mood_scores[i],
    stress: trends.stress_scores[i],
    sleep: trends.sleep_hours[i],
  })) || []

  const categoryData = financialSummary?.category_breakdown
    ? Object.entries(financialSummary.category_breakdown).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
      }))
    : []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Sun className="w-6 h-6 text-primary-500" />
            {getGreeting()}, {user?.full_name?.split(' ')[0]}!
          </h1>
          <p className="text-surface-500 mt-1">Here's your life dashboard for today</p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary-500" />
          <span className="text-sm font-medium text-surface-600">AI Insights Active</span>
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ScoreCard
          title="Wellness Score"
          score={wellnessScore?.overall_wellness || 50}
          icon={<Heart className="w-5 h-5 text-emerald-600" />}
          color="green"
        />
        <ScoreCard
          title="Financial Health"
          score={financialSummary?.financial_wellness_score || 50}
          icon={<Wallet className="w-5 h-5 text-blue-600" />}
          color="blue"
        />
        <ScoreCard
          title="Stress Level"
          score={wellnessScore?.stress_management || 50}
          icon={<Brain className="w-5 h-5 text-purple-600" />}
          color="purple"
        />
        <ScoreCard
          title="Burnout Risk"
          score={
            wellnessScore?.burnout_risk === 'low'
              ? 20
              : wellnessScore?.burnout_risk === 'medium'
              ? 50
              : wellnessScore?.burnout_risk === 'high'
              ? 80
              : 15
          }
          icon={<AlertTriangle className="w-5 h-5 text-red-600" />}
          color="red"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Wellness Trends */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-500" />
            Wellness Trends (14 days)
          </h3>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#a3a3a3" />
                <YAxis tick={{ fontSize: 12 }} stroke="#a3a3a3" />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="mood"
                  stroke="#10b981"
                  fill="#10b98120"
                  name="Mood"
                />
                <Area
                  type="monotone"
                  dataKey="sleep"
                  stroke="#3b82f6"
                  fill="#3b82f620"
                  name="Sleep"
                />
                <Area
                  type="monotone"
                  dataKey="stress"
                  stroke="#ef4444"
                  fill="#ef444420"
                  name="Stress"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-surface-400">
              <p>Start logging check-ins to see your trends</p>
            </div>
          )}
        </div>

        {/* Spending Breakdown */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center justify-center gap-2">
            <Wallet className="w-5 h-5 text-primary-500" />
            Spending Breakdown
          </h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name.slice(0,6)} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                  fontSize={11}
                >
                  {categoryData.map((_: any, index: number) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `₹${value.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-surface-400">
              <p>No expenses logged yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Predictions & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Predictions */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-500" />
            AI Predictions
          </h3>
          {predictions ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-surface-50 rounded-xl">
                <span className="text-sm text-surface-600">Month-end spending forecast</span>
                <span className="font-semibold">₹{predictions.month_end_spending_forecast?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-surface-50 rounded-xl">
                <span className="text-sm text-surface-600">Savings projection</span>
                <span className={`font-semibold ${predictions.savings_projection >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{predictions.savings_projection?.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-surface-50 rounded-xl">
                <span className="text-sm text-surface-600">Burnout risk trend</span>
                <span className="font-semibold capitalize">{predictions.burnout_risk_trend}</span>
              </div>
              {predictions.recommendations?.slice(0, 2).map((rec: string, i: number) => (
                <p key={i} className="text-sm text-surface-600 p-3 bg-primary-50 rounded-xl border border-primary-100">
                  💡 {rec}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-surface-400 text-sm">Log more data to unlock AI predictions</p>
          )}
        </div>

        {/* Financial Quick View */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Wallet className="w-5 h-5 text-primary-500" />
            Monthly Overview
          </h3>
          {financialSummary ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-green-50 rounded-xl">
                  <p className="text-xs text-green-600 font-medium">Income</p>
                  <p className="text-xl font-bold text-green-700">₹{financialSummary.total_income?.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-red-50 rounded-xl">
                  <p className="text-xs text-red-600 font-medium">Expenses</p>
                  <p className="text-xl font-bold text-red-700">₹{financialSummary.total_expenses?.toLocaleString()}</p>
                </div>
              </div>
              <div className="p-4 bg-surface-50 rounded-xl">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-surface-600">Budget Adherence</span>
                  <span className="text-sm font-semibold">{financialSummary.budget_adherence}%</span>
                </div>
                <div className="h-2 bg-surface-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${Math.min(100, financialSummary.budget_adherence)}%` }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-surface-400 text-sm">Add income and expenses to see your overview</p>
          )}
        </div>
      </div>
    </div>
  )
}
