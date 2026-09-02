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
      <div className="support-banner__icon">☕</div>
      <h3 className="support-banner__heading">Enjoyed this puzzle?</h3>
      <p className="support-banner__text">
        Each puzzle costs real money in AI inference. Help keep the crosswords free for everyone!
      </p>
      <a
        className="support-banner__btn"
        href={BMC_URL}
        target="_blank"
        rel="noopener noreferrer"
      >
        Buy me a coffee
      </a>
      <p className="support-banner__subtext">
        Or bring your own API key in <strong>Settings</strong> ⚙️ for unlimited puzzles
      </p>
    </div>
  )
}
