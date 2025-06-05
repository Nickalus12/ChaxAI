import React, { useState } from 'react'
import axios from 'axios'

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [theme, setTheme] = useState('light')

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark')
  }

  const submitQuestion = async (e) => {
    e.preventDefault()
    if (!question) return
    try {
      const { data } = await axios.post('http://localhost:8000/ask', { question })
      setMessages([...messages, { question, answer: data.answer, sources: data.sources }])
      setQuestion('')
    } catch (err) {
      console.error(err)
      setMessages([...messages, { question, answer: 'Error fetching answer', sources: [] }])
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4 gap-4">
      <button onClick={toggleTheme} className="self-end px-2 py-1 border rounded">
        {theme === 'light' ? 'Dark' : 'Light'} Mode
      </button>
      <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-gray-100">
        ChaxAI
      </h1>
      <form onSubmit={submitQuestion} className="w-full max-w-xl flex flex-col gap-2">
        <input
          className="border rounded p-2 dark:bg-gray-700 dark:text-white"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question"
        />
        <button className="bg-blue-500 text-white p-2 rounded" type="submit">
          Ask
        </button>
      </form>
      <div className="w-full max-w-xl flex flex-col gap-4">
        {messages.map((m, idx) => (
          <div key={idx} className="bg-white dark:bg-gray-700 p-4 rounded shadow">
            <p className="font-semibold">Q: {m.question}</p>
            <p className="mt-2">A: {m.answer}</p>
            {m.sources && m.sources.length > 0 && (
              <ul className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                {m.sources.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
