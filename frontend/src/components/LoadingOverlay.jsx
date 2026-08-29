import './LoadingOverlay.css'

export function LoadingOverlay({ isLoading }) {
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
      </div>
    </div>
  )
}
