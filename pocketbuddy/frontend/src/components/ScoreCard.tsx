import clsx from 'clsx'

interface ScoreCardProps {
  title: string
  score: number
  maxScore?: number
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'stable'
  color?: 'orange' | 'green' | 'blue' | 'red' | 'purple'
}

const colorMap = {
  orange: 'from-primary-500 to-primary-600',
  green: 'from-emerald-500 to-emerald-600',
  blue: 'from-blue-500 to-blue-600',
  red: 'from-red-500 to-red-600',
  purple: 'from-purple-500 to-purple-600',
}

const bgColorMap = {
  orange: 'bg-primary-50 border-primary-100',
  green: 'bg-emerald-50 border-emerald-100',
  blue: 'bg-blue-50 border-blue-100',
  red: 'bg-red-50 border-red-100',
  purple: 'bg-purple-50 border-purple-100',
}

export default function ScoreCard({ title, score, maxScore = 100, icon, trend, color = 'orange' }: ScoreCardProps) {
  const percentage = (score / maxScore) * 100
  return (
    <div className={clsx('card border', bgColorMap[color])}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium text-surface-600">{title}</span>
        </div>
        {trend && (
          <span className={clsx('text-xs font-medium', { 'text-green-600': trend === 'up', 'text-red-600': trend === 'down', 'text-surface-500': trend === 'stable' })}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold text-surface-900">{Math.round(score)}</span>
        <span className="text-sm text-surface-500 mb-1">/ {maxScore}</span>
      </div>
      <div className="mt-4 h-2 bg-white/60 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full bg-gradient-to-r transition-all duration-500', colorMap[color])} style={{ width: `${Math.min(100, percentage)}%` }} />
      </div>
    </div>
  )
}
