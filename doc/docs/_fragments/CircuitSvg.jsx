import React, { useState } from 'react';
import CircuitDialog from './CircuitDialog';

export default function CircuitSvg({ src: SvgComponent, alt, padding = '10px' }) {
  // In Docusaurus, SVGs are imported as React components via SVGR
  // So 'src' is actually a React component, not a URL string

  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const handleOpen = () => {
    setIsDialogOpen(true);
  };

  const handleClose = () => {
    setIsDialogOpen(false);
  };

  return (
    <>
      <div
        onClick={handleOpen}
        role="button"
        tabIndex={0}
        aria-label={`Click to enlarge: ${alt}`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleOpen();
          }
        }}
        style={{
          padding,
          border: '1px solid white',
          margin: '0 0 20px',
          borderRadius: '2px',
          cursor: 'pointer',
          transition: 'border-color 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = '#888';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'white';
        }}
      >
        <SvgComponent
          aria-label={alt}
          style={{ display: 'block', maxWidth: '100%', pointerEvents: 'none' }}
        />
      </div>

      <CircuitDialog isOpen={isDialogOpen} onClose={handleClose} alt={alt}>
        <div style={{
          width: '90vw',
          height: '90vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <SvgComponent
            aria-label={alt}
            width="100%"
            height="100%"
            preserveAspectRatio="xMidYMid meet"
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
            }}
          />
        </div>
      </CircuitDialog>
    </>
  );
}
