import { useState, useEffect } from 'react'

export default function usePersistedState(key, defaultValue) {
  const [state, setState] = useState(() => {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  })

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(state))
  }, [key, state])

  return [state, setState]
}
