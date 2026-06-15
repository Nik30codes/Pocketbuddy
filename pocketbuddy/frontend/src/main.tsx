import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

// Apply dark class on load
const stored = localStorage.getItem('pocketbuddy-theme')
if (stored) {
  const { state } = JSON.parse(stored)
  if (state?.dark) document.documentElement.classList.add('dark')
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            borderRadius: '12px',
            background: '#1a1a1a',
            color: '#fff',
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
