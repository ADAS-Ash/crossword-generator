import { useState, useCallback } from 'react'
import './TopicForm.css'

const RANDOM_TOPICS = [
  'Space Exploration', '90s Movies', 'Ancient Egypt', 'World Capitals',
  'Ocean Life', 'Classic Rock Bands', 'Mythology', 'Inventions',
  'Dinosaurs', 'Famous Scientists', 'Video Games', 'Superheroes',
  'World Cuisine', 'Olympic Sports', 'Shakespeare', 'Jazz Music',
  'Rainforest Animals', 'Board Games', 'Architecture', 'Astronomy',
  'Pirates', 'Medieval History', 'Desserts', 'Volcanoes',
  'Famous Painters', 'Martial Arts', 'Fairy Tales', 'Camping',
  'The Human Body', 'Musical Instruments', 'Dog Breeds', 'Gemstones',
  'Photography', 'Magic Tricks', 'Roller Coasters', 'Baking',
]

export function TopicForm({ onGenerate, isLoading }) {
  const [topic, setTopic] = useState('')
  const [gridSize, setGridSize] = useState(15)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (topic.trim() && !isLoading) {
      onGenerate(topic.trim(), gridSize)
    }
  }

  const handleFeelingLucky = useCallback(() => {
    if (isLoading) return
    const randomTopic = RANDOM_TOPICS[Math.floor(Math.random() * RANDOM_TOPICS.length)]
    setTopic(randomTopic)
    onGenerate(randomTopic, gridSize)
  }, [isLoading, gridSize, onGenerate])

  return (
    <form className="topic-form" onSubmit={handleSubmit}>
      <div className="topic-form__input-group">
        <input
          type="text"
          className="topic-form__input"
          placeholder="Enter a topic... (e.g., Space Exploration, 90s Movies)"
          value={topic}
          onChange={e => setTopic(e.target.value)}
          disabled={isLoading}
          autoFocus
        />
      </div>
      <div className="topic-form__controls">
        <label className="topic-form__label">
          Grid
          <select
            className="topic-form__select"
            value={gridSize}
            onChange={e => setGridSize(Number(e.target.value))}
            disabled={isLoading}
          >
            <option value={10}>10 x 10</option>
            <option value={13}>13 x 13</option>
            <option value={15}>15 x 15</option>
            <option value={20}>20 x 20</option>
          </select>
        </label>
        <button
          type="submit"
          className="topic-form__button"
          disabled={!topic.trim() || isLoading}
        >
          {isLoading ? 'Generating...' : 'Generate Puzzle'}
        </button>
        <button
          type="button"
          className="topic-form__button topic-form__button--lucky"
          onClick={handleFeelingLucky}
          disabled={isLoading}
        >
          {isLoading ? '...' : "I'm Feeling Lucky"}
        </button>
      </div>
    </form>
  )
}
