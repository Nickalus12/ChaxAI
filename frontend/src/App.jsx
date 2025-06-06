import React, { useEffect, useState } from 'react'
import { createApi } from './api'
import Chat from './components/Chat'
import DocumentList from './components/DocumentList'
import UploadForm from './components/UploadForm'
import Header from './components/Header'

function App({ apiUrl, apiToken }) {
  const api = createApi({ baseUrl: apiUrl, token: apiToken })
  const [docs, setDocs] = useState([])
  const [theme, setTheme] = useState(
    localStorage.getItem('chaxai-theme') || 'light'
  )
  const [uploading, setUploading] = useState(false)

  const loadDocuments = async () => {
    try {
      const data = await api.listDocuments()
      setDocs(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('chaxai-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  const handleUpload = async (files) => {
    if (!files.length) return
    try {
      setUploading(true)
      await api.uploadFiles(files)
      await loadDocuments()
      alert('Upload successful')
    } catch (err) {
      console.error(err)
      alert('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const deleteDoc = async (name) => {
    if (!window.confirm(`Delete ${name}?`)) return
    try {
      await api.deleteDocument(name)
      await loadDocuments()
    } catch (err) {
      console.error(err)
      alert('Delete failed')
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4 gap-4">
      <Header theme={theme} toggleTheme={toggleTheme} />
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        ChaxAI
      </h1>
      <UploadForm uploading={uploading} onUpload={handleUpload} />
      <Chat api={api} />
      <div className="w-full max-w-xl mt-4">
        <h2 className="font-bold mb-2">Documents</h2>
        <DocumentList docs={docs} onDelete={deleteDoc} />
      </div>
    </div>
  )
}

export default App
