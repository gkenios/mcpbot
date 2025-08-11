import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './App.css'
import App from './App.tsx'

createRoot(document.getElementById('chatbot-popup-container')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
