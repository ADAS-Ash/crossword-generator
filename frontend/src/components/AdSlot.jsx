import { useEffect, useRef } from 'react'
import './AdSlot.css'

export function AdSlot({ slot, format = 'auto', className = '' }) {
  const adRef = useRef(null)
  const pushed = useRef(false)

  useEffect(() => {
    if (pushed.current) return
    if (!window.adsbygoogle) return
    try {
      pushed.current = true
      window.adsbygoogle.push({})
    } catch {
      // AdSense not loaded or blocked
    }
  }, [])

  if (!slot) return null

  return (
    <div className={`ad-slot ${className}`}>
      <ins
        ref={adRef}
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client="ca-pub-1163230166986964"
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  )
}
