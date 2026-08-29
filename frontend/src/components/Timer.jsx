import './Timer.css'

export function Timer({ formatted, isRunning, onToggle }) {
  return (
    <div className="timer">
      <span className="timer__display">{formatted}</span>
      <button className="timer__button" onClick={onToggle} title={isRunning ? 'Pause' : 'Resume'}>
        {isRunning ? '⏸' : '▶'}
      </button>
    </div>
  )
}
