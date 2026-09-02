import { useState } from 'react'
import './SupportBanner.css'

const BMC_URL = 'https://buymeacoffee.com/naiklabs'

export function SupportBanner({ show }) {
  const [dismissed, setDismissed] = useState(false)

  if (!show || dismissed) return null

  return (
    <div className="support-banner">
      <button
        className="support-banner__close"
        onClick={() => setDismissed(true)}
        title="Dismiss"
      >
        &times;
      </button>
      <p className="support-banner__text">
        Enjoyed this puzzle? Help keep the crosswords coming!
      </p>
      <a
        className="support-banner__btn"
        href={BMC_URL}
        target="_blank"
        rel="noopener noreferrer"
      >
        ☕ Buy me a coffee
      </a>
    </div>
  )
}
