import './LoadingOverlay.css'

const BMC_URL = 'https://buymeacoffee.com/naiklabs'

export function LoadingOverlay({ isLoading, showSupport = false }) {
  if (!isLoading) return null

  return (
    <div className="loading-overlay">
      <div className="loading-overlay__content">
        <div className="loading-spinner">
          <div className="loading-spinner__cell" />
          <div className="loading-spinner__cell" />
          <div className="loading-spinner__cell" />
          <div className="loading-spinner__cell" />
        </div>
        <p className="loading-overlay__text">Generating your puzzle...</p>
        {showSupport && (
          <a
            className="loading-overlay__support"
            href={BMC_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            ☕ Buy me a coffee while you wait
          </a>
        )}
      </div>
    </div>
  )
}
