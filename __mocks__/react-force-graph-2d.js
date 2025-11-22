// Mock react-force-graph-2d for Jest tests
import React from 'react'

const ForceGraph2D = React.forwardRef((props, ref) => {
  return React.createElement('div', {
    'data-testid': 'force-graph-2d-mock',
    ref,
  })
})

ForceGraph2D.displayName = 'ForceGraph2D'

export default ForceGraph2D
