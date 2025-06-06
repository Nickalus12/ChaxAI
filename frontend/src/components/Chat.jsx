import React, { useState } from 'react'
import useChatHistory from '../hooks/useChatHistory'

function Chat({ api }) {
  const [question, setQuestion] = useState('')
  const { messages, addMessage, clearHistory } = useChatHistory()
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!question) return
    try {
      setLoading(true)
      const result = await api.askQuestion(question)
      addMessage({
        question,
        answer: result.data.answer,
        sources: result.data.sources,
        requestId: result.requestId,
      })
      setQuestion('')
    } catch (err) {
      console.error(err)
      addMessage({ question, answer: 'Error fetching answer', sources: [], requestId: '' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-xl flex flex-col gap-4">
      <form onSubmit={submit} className="flex flex-col gap-2">
        <input
          className="border rounded p-2 dark:bg-gray-700 dark:text-white"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question"
        />
        <button className="bg-blue-500 text-white p-2 rounded" type="submit" disabled={loading}>
          {loading ? 'Asking...' : 'Ask'}
        </button>
        {messages.length > 0 && (
          <button type="button" onClick={clearHistory} className="text-sm underline mt-1 self-end">
            Clear history
          </button>
        )}
      </form>
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
          {m.requestId && (
            <p className="mt-2 text-xs text-gray-400">Request ID: {m.requestId}</p>
          )}
        </div>
      ))}
    </div>
  )
}

export default Chat
