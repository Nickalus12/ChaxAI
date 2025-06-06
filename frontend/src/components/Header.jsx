import React from 'react'

function Header({ theme, toggleTheme }) {
  return (
    <div className="w-full max-w-xl flex justify-end mb-4">
      <button onClick={toggleTheme} className="px-2 py-1 border rounded">
        {theme === 'light' ? 'Dark' : 'Light'} Mode
      </button>
    </div>
  )
}

export default Header
