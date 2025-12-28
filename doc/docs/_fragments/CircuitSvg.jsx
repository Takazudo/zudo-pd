import React from 'react';

export default function CircuitSvg({ src: SvgComponent, alt, padding = '10px' }) {
  // In Docusaurus, SVGs are imported as React components via SVGR
  // So 'src' is actually a React component, not a URL string

  return (
    <div style={{ padding, border: '1px solid white', margin: '0 0 20px', borderRadius: '2px' }}>
      <SvgComponent
        aria-label={alt}
        style={{ display: 'block', maxWidth: '100%' }}
      />
    </div>
  );
}
