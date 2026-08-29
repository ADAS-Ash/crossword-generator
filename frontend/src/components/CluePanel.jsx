import './CluePanel.css'

export function CluePanel({ wordsAcross, wordsDown, activeWord, onSelectClue }) {
  return (
    <div className="clue-panel">
      <div className="clue-section">
        <h3 className="clue-section__title">Across</h3>
        <ul className="clue-list">
          {wordsAcross.map(w => (
            <li
              key={`a-${w.number}`}
              className={`clue-item ${activeWord?.number === w.number && activeWord?.direction === 'across' ? 'clue-item--active' : ''}`}
              onClick={() => onSelectClue(w)}
            >
              <span className="clue-item__number">{w.number}</span>
              <span className="clue-item__text">{w.clue}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="clue-section">
        <h3 className="clue-section__title">Down</h3>
        <ul className="clue-list">
          {wordsDown.map(w => (
            <li
              key={`d-${w.number}`}
              className={`clue-item ${activeWord?.number === w.number && activeWord?.direction === 'down' ? 'clue-item--active' : ''}`}
              onClick={() => onSelectClue(w)}
            >
              <span className="clue-item__number">{w.number}</span>
              <span className="clue-item__text">{w.clue}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
