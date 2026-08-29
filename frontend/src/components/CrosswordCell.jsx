import './CrosswordCell.css'

export function CrosswordCell({
  row, col, value, answer, number,
  isBlack, isSelected, isHighlighted, isRevealed,
  checkStatus, onClick,
}) {
  if (isBlack) {
    return <div className="cell cell--black" />
  }

  let className = 'cell'
  if (isSelected) className += ' cell--selected'
  else if (isHighlighted) className += ' cell--highlighted'
  if (checkStatus === 'correct') className += ' cell--correct'
  if (checkStatus === 'incorrect') className += ' cell--incorrect'
  if (isRevealed) className += ' cell--revealed'

  return (
    <div className={className} onClick={() => onClick(row, col)}>
      {number && <span className="cell__number">{number}</span>}
      <span className="cell__letter">{value}</span>
    </div>
  )
}
