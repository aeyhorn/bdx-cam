import type { CSSProperties, DetailedHTMLProps, HTMLAttributes } from 'react'

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
        src?: string
        poster?: string
        exposure?: string
        'camera-controls'?: boolean
        'touch-action'?: string
        'shadow-intensity'?: string
        style?: CSSProperties
      }
    }
  }
}
