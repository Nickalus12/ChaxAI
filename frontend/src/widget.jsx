import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

export function initChaxAI({ elementId = 'chaxai', apiUrl, apiToken }) {
  const el = document.getElementById(elementId)
  if (!el) {
    throw new Error(`Element with id '${elementId}' not found`)
  }
  ReactDOM.createRoot(el).render(
    <React.StrictMode>
      <App apiUrl={apiUrl} apiToken={apiToken} />
    </React.StrictMode>
  )
}

window.initChaxAI = initChaxAI
