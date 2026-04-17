import { useState } from 'react';
import CircuitDialog from './circuit-dialog';

interface SvgInteractiveProps {
  src: string;
  alt: string;
  padding?: string;
  minWidth?: string;
  minHeight?: string;
  enlargeIconUrl?: string;
}

export default function SvgInteractive({
  src,
  alt,
  padding = '20px',
  minWidth,
  minHeight,
  enlargeIconUrl,
}: SvgInteractiveProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const containerStyle: Record<string, string | undefined> = {
    padding,
    border: '1px solid var(--color-muted)',
    margin: '0 0 20px',
    borderRadius: '2px',
    cursor: 'pointer',
    transition: 'border-color 0.2s',
    background: '#ffffff',
    position: 'relative',
  };

  if (minWidth || minHeight) {
    containerStyle.display = 'inline-block';
    if (minWidth) containerStyle.minWidth = minWidth;
    if (minHeight) containerStyle.minHeight = minHeight;
  }

  return (
    <>
      <div
        onClick={() => setIsDialogOpen(true)}
        role="button"
        tabIndex={0}
        aria-label={`Click to enlarge: ${alt}`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsDialogOpen(true);
          }
        }}
        style={containerStyle}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-fg)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.borderColor = 'var(--color-muted)';
        }}
      >
        <img
          src={src}
          alt={alt}
          style={{
            display: 'block',
            width: '100%',
            height: 'auto',
            objectFit: 'contain',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            padding: '6px',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            borderRadius: '4px',
            zIndex: 20,
            lineHeight: 0,
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 170 170" fill="white">
            <path d="M160.7 114.85v45.85H9.3V9.3h45.85V0H0V170H170V114.85h-9.3z"/>
            <path d="M160.7 0H86.11v9.3h68.01l-81.2 81.21 6.57 6.57 81.21-81.2v68.01h9.3V0h-9.3z"/>
          </svg>
        </div>
      </div>

      <CircuitDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        alt={alt}
        src={src}
      />
    </>
  );
}
