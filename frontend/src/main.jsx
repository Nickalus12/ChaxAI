import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const apiToken = import.meta.env.VITE_API_TOKEN

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App apiUrl={apiUrl} apiToken={apiToken} />
  </React.StrictMode>
)
