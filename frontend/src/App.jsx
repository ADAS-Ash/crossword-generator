import { useState, useCallback, useRef, useEffect } from 'react'
import { generateCrossword, loadPuzzleById } from './api/crossword'
import { DEMO_PUZZLES } from './data/demoPuzzles'
import { useCrossword } from './hooks/useCrossword'
import { useKeyboardNav } from './hooks/useKeyboardNav'
import { useTimer } from './hooks/useTimer'
import { useTheme } from './hooks/useTheme'
import { TopicForm } from './components/TopicForm'
import { Toolbar } from './components/Toolbar'
import { CrosswordGrid } from './components/CrosswordGrid'
import { CluePanel } from './components/CluePanel'
import { LoadingOverlay } from './components/LoadingOverlay'
import './App.css'

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showDemos, setShowDemos] = useState(false)
  const { isDark, toggleTheme } = useTheme()
  const timer = useTimer()

  const gridRef = useRef(null)
  const crossword = useCrossword()
  const { handleKeyDown } = useKeyboardNav({
    selectedCell: crossword.selectedCell,
    direction: crossword.direction,
    puzzle: crossword.puzzle,
    userGrid: crossword.userGrid,
    setCellValue: crossword.setCellValue,
    moveToNextCell: crossword.moveToNextCell,
    moveToNextEmptyInWord: crossword.moveToNextEmptyInWord,
    moveToPrevCell: crossword.moveToPrevCell,
    moveDirection: crossword.moveDirection,
    selectNextClue: crossword.selectNextClue,
    selectPrevClue: crossword.selectPrevClue,
    setDirection: crossword.setDirection,
    selectCell: crossword.selectCell,
  })

  const handleGenerate = useCallback(async (topic, gridSize) => {
    setIsLoading(true)
    setError(null)
    timer.reset()
    try {
      const data = await generateCrossword(topic, gridSize)
      crossword.loadPuzzle(data)
      if (data.puzzle_id) {
        window.history.pushState(null, '', `/p/${data.puzzle_id}`)
      }
      timer.start()
    } catch (err) {
      setError(err.message)
      setShowDemos(true)
    } finally {
      setIsLoading(false)
    }
  }, [crossword, timer])

  const loadDemo = useCallback((index) => {
    const demo = DEMO_PUZZLES[index]
    if (!demo) return
    setError(null)
    setShowDemos(false)
    crossword.loadPuzzle(demo)
    timer.reset()
    timer.start()
    window.history.pushState(null, '', '/')
  }, [crossword, timer])

  useEffect(() => {
    const match = window.location.pathname.match(/^\/p\/([a-z0-9]+)$/)
    if (!match) return
    const puzzleId = match[1]
    setIsLoading(true)
    loadPuzzleById(puzzleId)
      .then(data => {
        if (data) {
          data.puzzle_id = puzzleId
          crossword.loadPuzzle(data)
          timer.start()
        } else {
          setError('Puzzle not found')
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Crossword Generator<span className="app__powered">by NaikLabs</span></h1>
        <p className="app__subtitle">AI-powered puzzles on any topic</p>
      </header>

      <div className="app__form-section">
        <TopicForm onGenerate={handleGenerate} isLoading={isLoading} />
      </div>

      {error && (
        <div className="app__error">
          <p>{error}</p>
          {showDemos && (
            <div className="app__demos">
              <p className="app__demos-title">Try a demo puzzle while the service recovers:</p>
              <div className="app__demos-grid">
                {DEMO_PUZZLES.map((demo, i) => (
                  <button key={i} className="app__demo-card" onClick={() => loadDemo(i)}>
                    <span className="app__demo-topic">{demo.metadata.topic}</span>
                    <span className="app__demo-meta">{demo.metadata.words_placed} words · {demo.metadata.grid_size}x{demo.metadata.grid_size}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {crossword.puzzle && (
        <>
          <Toolbar
            puzzle={crossword.puzzle}
            userGrid={crossword.userGrid}
            revealedCells={crossword.revealedCells}
            timerFormatted={timer.formatted}
            timerRunning={timer.isRunning}
            onTimerToggle={timer.toggle}
            onRevealLetter={crossword.revealLetter}
            onRevealWord={crossword.revealWord}
            onRevealAll={crossword.revealAll}
            onClearWord={crossword.clearWord}
            onCheckWord={crossword.checkWord}
            onCheckAnswers={crossword.checkAnswers}
            gridRef={gridRef}
            isDark={isDark}
            onToggleTheme={toggleTheme}
            isComplete={crossword.isComplete}
          />

          <div className="app__puzzle">
            <div className="app__grid-container">
              <LoadingOverlay isLoading={isLoading} />
              <CrosswordGrid
                ref={gridRef}
                puzzle={crossword.puzzle}
                userGrid={crossword.userGrid}
                selectedCell={crossword.selectedCell}
                highlightedCells={crossword.highlightedCells}
                revealedCells={crossword.revealedCells}
                checkedCells={crossword.checkedCells}
                selectCell={crossword.selectCell}
                onKeyDown={handleKeyDown}
              />
            </div>
            <CluePanel
              wordsAcross={crossword.wordsAcross}
              wordsDown={crossword.wordsDown}
              activeWord={crossword.activeWord}
              onSelectClue={crossword.selectClue}
            />
          </div>

          <div className="app__meta">
            <span>Theme: {crossword.puzzle.metadata.topic}</span>
            <span>Words: {crossword.puzzle.metadata.words_placed}</span>
            <span>Provider: {crossword.puzzle.metadata.provider}</span>
            {crossword.puzzle.metadata.grounded && (
              <span className="app__meta-grounded">Verified with Google Search</span>
            )}
          </div>
        </>
      )}

      {!crossword.puzzle && !isLoading && (
        <div className="app__empty">
          <p>Enter a topic above and generate your first puzzle!</p>
        </div>
      )}

      {isLoading && !crossword.puzzle && (
        <div className="app__loading-standalone">
          <LoadingOverlay isLoading={true} />
        </div>
      )}

      <footer className="app__footer">
        <p>Powered by <a href="https://naiklabs.dev" target="_blank" rel="noopener">NaikLabs</a></p>
      </footer>
    </div>
  )
}

export default App
