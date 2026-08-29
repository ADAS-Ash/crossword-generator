import { useMemo } from 'react'
import { calculateScore } from '../utils/scoring'
import './ScoreDisplay.css'

export function ScoreDisplay({ puzzle, userGrid, revealedCells }) {
  const score = useMemo(
    () => calculateScore(puzzle, userGrid, revealedCells),
    [puzzle, userGrid, revealedCells]
  )

  if (!puzzle) return null

  return (
    <div className="score-display">
      <span className="score-display__label">Score</span>
      <span className="score-display__value">{score.correct}/{score.total}</span>
    </div>
  )
}
