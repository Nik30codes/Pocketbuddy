import { useState, useEffect } from 'react'
import { Wallet, Plus, TrendingUp, PieChart as PieIcon, Upload } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import api from '../lib/api'
import toast from 'react-hot-toast'

const COLORS = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4', '#f59e0b']

const categories = [
  'food', 'shopping', 'travel', 'entertainment', 'education',
  'health', 'rent', 'utilities', 'groceries', 'subscriptions', 'other'
]

export default function FinancialPage() {
  const [summary, setSummary] = useState<any>(null)
  const [expenses, setExpenses] = useState<any[]>([])
  const [showAddExpense, setShowAddExpense] = useState(false)
  const [showAddIncome, setShowAddIncome] = useState(false)
  const [expenseForm, setExpenseForm] = useState({
    amount: '',
    category: 'food',
    description: '',
    merchant: '',
    date: new Date().toISOString().split('T')[0],
  })
  const [incomeForm, setIncomeForm] = useState({
    amount: '',
    source: 'allowance',
    description: '',
    date: new Date().toISOString().split('T')[0],
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [summaryRes, expensesRes] = await Promise.allSettled([
        api.get('/financial/summary'),
        api.get('/financial/expenses?limit=20'),
      ])
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value.data)
      if (expensesRes.status === 'fulfilled') setExpenses(expensesRes.value.data)
    } catch (e) {
      console.error(e)
    }
  }

  const addExpense = async () => {
    if (!expenseForm.amount) return
    try {
      await api.post('/financial/expenses', {
        ...expenseForm,
        amount: parseFloat(expenseForm.amount),
      })
      toast.success('Expense logged!')
      setShowAddExpense(false)
      setExpenseForm({ amount: '', category: 'food', description: '', merchant: '', date: new Date().toISOString().split('T')[0] })
      loadData()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to add expense')
    }
  }

  const addIncome = async () => {
    if (!incomeForm.amount) return
    try {
      await api.post('/financial/income', {
        ...incomeForm,
        amount: parseFloat(incomeForm.amount),
      })
      toast.success('Income recorded!')
      setShowAddIncome(false)
      setIncomeForm({ amount: '', source: 'allowance', description: '', date: new Date().toISOString().split('T')[0] })
      loadData()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to add income')
    }
  }

  const categoryData = summary?.category_breakdown
    ? Object.entries(summary.category_breakdown).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
      }))
    : []

  const topSpending = summary?.top_spending_categories || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wallet className="w-6 h-6 text-blue-500" />
            Financial Dashboard
          </h1>
          <p className="text-surface-500">Track spending, income, and budget health</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowAddIncome(true)} className="btn-secondary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Income
          </button>
          <button onClick={() => setShowAddExpense(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Expense
          </button>
        </div>
      </div>

      {/* Add Expense Form */}
      {showAddExpense && (
        <div className="card border-2 border-primary-200 !bg-[#DFF1F1] dark:!bg-[#EDE9E6]">
          <h3 className="font-semibold mb-4">Add Expense</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-sm text-surface-600">Amount (₹)</label>
              <input type="number" value={expenseForm.amount} onChange={(e) => setExpenseForm({...expenseForm, amount: e.target.value})} className="input-field mt-1" placeholder="250" />
            </div>
            <div>
              <label className="text-sm text-surface-600">Category</label>
              <select value={expenseForm.category} onChange={(e) => setExpenseForm({...expenseForm, category: e.target.value})} className="input-field mt-1">
                {categories.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm text-surface-600">Date</label>
              <input type="date" value={expenseForm.date} onChange={(e) => setExpenseForm({...expenseForm, date: e.target.value})} className="input-field mt-1" />
            </div>
            <div>
              <label className="text-sm text-surface-600">Description</label>
              <input type="text" value={expenseForm.description} onChange={(e) => setExpenseForm({...expenseForm, description: e.target.value})} className="input-field mt-1" placeholder="Lunch at canteen" />
            </div>
            <div>
              <label className="text-sm text-surface-600">Merchant (optional)</label>
              <input type="text" value={expenseForm.merchant} onChange={(e) => setExpenseForm({...expenseForm, merchant: e.target.value})} className="input-field mt-1" placeholder="Store name" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={addExpense} className="btn-primary">Save Expense</button>
            <button onClick={() => setShowAddExpense(false)} className="btn-ghost">Cancel</button>
          </div>
        </div>
      )}

      {/* Add Income Form */}
      {showAddIncome && (
        <div className="card border-2 border-green-200 !bg-[#EDE9E6] dark:!bg-[#EDE9E6]">
          <h3 className="font-semibold mb-4">Add Income</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-sm text-surface-600">Amount (₹)</label>
              <input type="number" value={incomeForm.amount} onChange={(e) => setIncomeForm({...incomeForm, amount: e.target.value})} className="input-field mt-1" placeholder="5000" />
            </div>
            <div>
              <label className="text-sm text-surface-600">Source</label>
              <select value={incomeForm.source} onChange={(e) => setIncomeForm({...incomeForm, source: e.target.value})} className="input-field mt-1">
                <option value="allowance">Allowance</option>
                <option value="part-time">Part-time Job</option>
                <option value="scholarship">Scholarship</option>
                <option value="freelance">Freelance</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-surface-600">Date</label>
              <input type="date" value={incomeForm.date} onChange={(e) => setIncomeForm({...incomeForm, date: e.target.value})} className="input-field mt-1" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={addIncome} className="btn-primary !bg-green-600 hover:!bg-green-700">Save Income</button>
            <button onClick={() => setShowAddIncome(false)} className="btn-ghost">Cancel</button>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card bg-green-50 border-green-100">
            <p className="text-sm text-green-600">Total Income</p>
            <p className="text-2xl font-bold text-green-700">₹{summary.total_income?.toLocaleString()}</p>
          </div>
          <div className="card bg-red-50 border-red-100">
            <p className="text-sm text-red-600">Total Expenses</p>
            <p className="text-2xl font-bold text-red-700">₹{summary.total_expenses?.toLocaleString()}</p>
          </div>
          <div className="card bg-blue-50 border-blue-100">
            <p className="text-sm text-blue-600">Savings</p>
            <p className={`text-2xl font-bold ${summary.savings >= 0 ? 'text-blue-700' : 'text-red-700'}`}>₹{summary.savings?.toLocaleString()}</p>
          </div>
          <div className="card bg-primary-50 border-primary-100">
            <p className="text-sm text-primary-600">Financial Score</p>
            <p className="text-2xl font-bold text-primary-700">{Math.round(summary.financial_wellness_score)}/100</p>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <PieIcon className="w-5 h-5 text-primary-500" /> Spending by Category
          </h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={categoryData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}>
                  {categoryData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(value: number) => `₹${value.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-surface-400">Add expenses to see breakdown</div>
          )}
        </div>

        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-500" /> Top Spending
          </h3>
          {topSpending.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topSpending} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="category" tick={{ fontSize: 12 }} width={100} />
                <Tooltip formatter={(value: number) => `₹${value.toLocaleString()}`} />
                <Bar dataKey="amount" fill="#f97316" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-surface-400">No data yet</div>
          )}
        </div>
      </div>

      {/* Recent Expenses */}
      <div className="card">
        <h3 className="font-semibold mb-4">Recent Expenses</h3>
        {expenses.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-100">
                  <th className="text-left py-3 px-2 text-surface-500 font-medium">Date</th>
                  <th className="text-left py-3 px-2 text-surface-500 font-medium">Description</th>
                  <th className="text-left py-3 px-2 text-surface-500 font-medium">Category</th>
                  <th className="text-right py-3 px-2 text-surface-500 font-medium">Amount</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((exp) => (
                  <tr key={exp.id} className="border-b border-surface-50 hover:bg-surface-50">
                    <td className="py-3 px-2">{exp.date}</td>
                    <td className="py-3 px-2">{exp.description || '-'}</td>
                    <td className="py-3 px-2">
                      <span className="px-2 py-1 bg-surface-100 rounded-full text-xs capitalize">{exp.category}</span>
                    </td>
                    <td className="py-3 px-2 text-right font-medium">₹{exp.amount.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-surface-400 text-center py-8">No expenses recorded yet. Start tracking!</p>
        )}
      </div>
    </div>
  )
}
