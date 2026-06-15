import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Plus, Trash2, Clock, X, ImagePlus, Search, MessageSquare } from 'lucide-react'
import api from '../lib/api'
import clsx from 'clsx'

interface Message { id: string; role: 'user' | 'assistant'; content: string; agent?: string; suggestions?: string[]; actions?: string[]; image?: string }
interface ConvoItem { id: number; title: string; updated_at: string }

const quickActions = ["How's my budget looking?", "I'm feeling stressed today", "Generate a daily routine", "What's my wellness score?", "I spent ₹200 on lunch", "Help me with exam prep"]

export default function ChatPage() {
  const [conversations, setConversations] = useState<ConvoItem[]>([])
  const [activeConvoId, setActiveConvoId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { loadConversations() }, [])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const loadConversations = async () => {
    try { const { data } = await api.get('/chat/conversations'); setConversations(data) } catch (e) {}
  }

  const loadConversation = async (convoId: number) => {
    setActiveConvoId(convoId)
    setSidebarOpen(false)
    try {
      const { data } = await api.get(`/chat/conversations/${convoId}/messages`)
      setMessages(data.map((m: any) => ({ id: String(m.id), role: m.role, content: m.content, agent: m.agent, suggestions: m.suggestions })))
    } catch (e) { setMessages([]) }
  }

  const startNewChat = () => { setActiveConvoId(null); setMessages([]); setSidebarOpen(false) }

  const deleteConversation = async (convoId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try { await api.delete(`/chat/conversations/${convoId}`); setConversations(c => c.filter(x => x.id !== convoId)); if (activeConvoId === convoId) startNewChat() } catch (e) {}
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) { setSelectedImage(file); const r = new FileReader(); r.onload = (ev) => setImagePreview(ev.target?.result as string); r.readAsDataURL(file) }
  }
  const clearImage = () => { setSelectedImage(null); setImagePreview(null); if (fileInputRef.current) fileInputRef.current.value = '' }

  const sendMessage = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim() && !selectedImage) return

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: messageText || 'Analyze this bill', image: imagePreview || undefined }
    setMessages(prev => [...prev, userMsg])
    setInput(''); setLoading(true)

    try {
      let data: any
      if (selectedImage) {
        const formData = new FormData()
        formData.append('image', selectedImage)
        formData.append('message', messageText || 'Analyze this bill')
        if (activeConvoId) formData.append('conversation_id', String(activeConvoId))
        const res = await api.post('/chat/message-with-image', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        data = res.data
        clearImage()
      } else {
        const res = await api.post(`/chat/message${activeConvoId ? `?conversation_id=${activeConvoId}` : ''}`, { message: messageText })
        data = res.data
      }

      if (data.conversation_id && !activeConvoId) setActiveConvoId(data.conversation_id)
      setMessages(prev => [...prev, { id: (Date.now()+1).toString(), role: 'assistant', content: data.response, agent: data.agent, suggestions: data.suggestions, actions: data.actions_taken }])
      loadConversations()
    } catch (error) {
      setMessages(prev => [...prev, { id: (Date.now()+1).toString(), role: 'assistant', content: "Connection issue. Try again.", agent: 'system' }])
    } finally { setLoading(false) }
  }

  const agentBadge = (agent?: string) => {
    const map: Record<string, string> = { financial_wellness: '💰 Financial', wellness: '🧘 Wellness', emotional_support: '💜 Support', routine_planning: '📅 Routine', burnout_detection: '⚠️ Burnout', life_coach: '🎯 Coach' }
    return <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: 'var(--bg)', color: 'var(--accent-orange)' }}>{map[agent || ''] || '🤖 AI'}</span>
  }

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  const filtered = conversations.filter(c => c.title.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="flex h-[calc(100vh-8rem)]">
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="w-72 flex-shrink-0 flex flex-col rounded-2xl mr-4 overflow-hidden" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)' }}>
          <div className="p-3 border-b" style={{ borderColor: 'var(--border)' }}>
            <button onClick={startNewChat} className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all hover:opacity-80" style={{ backgroundColor: 'var(--accent-orange)', color: '#fff' }}>
              <Plus className="w-4 h-4" /> New Chat
            </button>
          </div>
          <div className="p-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-secondary)' }} />
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search chats..." className="input-field !pl-9 !py-2 text-sm" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filtered.map((c) => (
              <div key={c.id} onClick={() => loadConversation(c.id)} className={clsx('group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all', activeConvoId === c.id ? 'ring-1' : '')} style={{ backgroundColor: activeConvoId === c.id ? 'var(--surface)' : 'transparent', outline: activeConvoId === c.id ? '2px solid var(--accent-orange)' : 'none' }}>
                <MessageSquare className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-secondary)' }} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate font-medium" style={{ color: 'var(--text-primary)' }}>{c.title}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>{timeAgo(c.updated_at)}</p>
                </div>
                <button onClick={(e) => deleteConversation(c.id, e)} className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100"><Trash2 className="w-3 h-3 text-red-500" /></button>
              </div>
            ))}
            {filtered.length === 0 && <p className="text-center py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>No conversations</p>}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 rounded-xl transition-all" style={{ backgroundColor: sidebarOpen ? 'var(--accent-orange)' : 'var(--surface)', color: sidebarOpen ? '#fff' : 'var(--text-secondary)', border: '1px solid var(--border)' }}>
              <Clock className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <Sparkles className="w-5 h-5" style={{ color: 'var(--accent-orange)' }} /> AI Chat
              </h1>
            </div>
          </div>
          <button onClick={startNewChat} className="btn-ghost flex items-center gap-1 text-sm"><Plus className="w-4 h-4" /> New</button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ backgroundColor: 'var(--surface)' }}>
                <img src="/logo.png" alt="PB" className="w-8 h-8 rounded-lg" />
              </div>
              <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>How can I help you today?</p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Ask about finances, wellness, routines, or upload a bill</p>
              <div className="flex flex-wrap gap-2 max-w-md justify-center mt-2">
                {quickActions.map((a, i) => <button key={i} onClick={() => sendMessage(a)} className="text-sm px-4 py-2 rounded-xl transition-all hover:scale-105" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>{a}</button>)}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={clsx('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
              {msg.role === 'assistant' && <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden" style={{ backgroundColor: 'var(--surface)' }}><img src="/logo.png" alt="PB" className="w-6 h-6 rounded-full" /></div>}
              <div className={clsx('max-w-[70%] rounded-2xl px-4 py-3', msg.role === 'user' ? 'rounded-br-md' : 'rounded-bl-md')} style={msg.role === 'user' ? { backgroundColor: 'var(--accent-orange)', color: '#fff' } : { backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                {msg.role === 'assistant' && msg.agent && <div className="mb-2">{agentBadge(msg.agent)}</div>}
                {msg.image && <div className="mb-2 rounded-xl overflow-hidden"><img src={msg.image} alt="" className="max-w-full max-h-48 object-contain rounded-xl" /></div>}
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.actions && msg.actions.length > 0 && <div className="mt-2 pt-2 border-t" style={{ borderColor: 'var(--border)' }}>{msg.actions.map((a,i) => <p key={i} className="text-xs text-green-600">✓ {a}</p>)}</div>}
                {msg.suggestions && msg.suggestions.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{msg.suggestions.map((s,i) => <button key={i} onClick={() => sendMessage(s)} className="text-xs px-3 py-1.5 rounded-full transition-all hover:scale-105" style={{ backgroundColor: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>{s}</button>)}</div>}
              </div>
              {msg.role === 'user' && <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--surface)' }}><User className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} /></div>}
            </div>
          ))}
          {loading && <div className="flex gap-3"><div className="w-8 h-8 rounded-full flex items-center justify-center overflow-hidden" style={{ backgroundColor: 'var(--surface)' }}><img src="/logo.png" alt="PB" className="w-6 h-6 rounded-full" /></div><div className="rounded-2xl px-4 py-3" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}><div className="flex gap-1"><div className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--text-secondary)' }} /><div className="w-2 h-2 rounded-full animate-bounce [animation-delay:0.1s]" style={{ backgroundColor: 'var(--text-secondary)' }} /><div className="w-2 h-2 rounded-full animate-bounce [animation-delay:0.2s]" style={{ backgroundColor: 'var(--text-secondary)' }} /></div></div></div>}
          <div ref={messagesEndRef} />
        </div>

        {/* Image Preview */}
        {imagePreview && (
          <div className="mb-3 flex items-center gap-3 p-3 rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <img src={imagePreview} alt="" className="w-14 h-14 object-cover rounded-lg" />
            <div className="flex-1"><p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>📸 {selectedImage?.name}</p></div>
            <button onClick={clearImage}><X className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} /></button>
          </div>
        )}

        {/* Input */}
        <div className="flex gap-3 items-center">
          <input type="file" ref={fileInputRef} onChange={handleImageSelect} accept="image/*,.pdf" className="hidden" />
          <button onClick={() => fileInputRef.current?.click()} className="p-3 rounded-xl transition-all hover:scale-105" style={{ border: '1px solid var(--border)', color: 'var(--text-secondary)' }}><ImagePlus className="w-5 h-5" /></button>
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()} placeholder="Ask me anything..." className="input-field flex-1" disabled={loading} />
          <button onClick={() => sendMessage()} disabled={loading || (!input.trim() && !selectedImage)} className="btn-primary !px-4 !py-3 !rounded-xl"><Send className="w-5 h-5" /></button>
        </div>
      </div>
    </div>
  )
}
