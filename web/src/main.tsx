import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/react'
import './index.css'
import App from './App.tsx'
import { MissingConfigScreen } from '@/features/auth/MissingConfigScreen'
import { readPublishableKey } from '@/lib/clerkConfig'

const key = readPublishableKey(import.meta.env)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {key ? (
      <ClerkProvider publishableKey={key} afterSignOutUrl="/">
        <App />
      </ClerkProvider>
    ) : (
      <MissingConfigScreen />
    )}
  </StrictMode>,
)
