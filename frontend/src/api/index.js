import axios from 'axios'

const DEFAULT_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const DEFAULT_TOKEN = import.meta.env.VITE_API_TOKEN

export function createApi({ baseUrl = DEFAULT_URL, token = DEFAULT_TOKEN } = {}) {
  const instance = axios.create({
    baseURL: baseUrl,
    headers: token ? { 'X-API-Token': token } : {},
  })

  const askQuestion = async (question) => {
    const res = await instance.post('/ask', { question })
    return { data: res.data, requestId: res.headers['x-request-id'] }
  }

  const listDocuments = async () => {
    const { data } = await instance.get('/documents')
    return data
  }

  const uploadFiles = async (files) => {
    const form = new FormData()
    Array.from(files).forEach((f) => form.append('files', f))
    await instance.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }

  const deleteDocument = async (name) => {
    await instance.delete(`/documents/${name}`)
  }

  return { askQuestion, listDocuments, uploadFiles, deleteDocument }
}
