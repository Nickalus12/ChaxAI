import usePersistedState from './usePersistedState'

export default function useChatHistory() {
  const [messages, setMessages] = usePersistedState('chaxai-history', [])

  const addMessage = (msg) => setMessages((prev) => [...prev, msg])
  const clearHistory = () => setMessages([])

  return { messages, addMessage, clearHistory }
}
