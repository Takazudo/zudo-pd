import { useState } from 'preact/hooks';
import CircuitDialog from './circuit-dialog';

interface SvgInteractiveProps {
  src: string;
  alt: string;
  padding?: string;
  minWidth?: string;
  minHeight?: string;
  enlargeIconUrl: string;
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
    border: '1px solid white',
    margin: '0 0 20px',
    borderRadius: '2px',
    cursor: 'pointer',
    transition: 'border-color 0.2s',
    background: 'oklch(86.9% 0.005 56.366)',
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
          (e.currentTarget as HTMLElement).style.borderColor = '#888';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.borderColor = 'white';
        }}
      >
        <img
          src={src}
          alt={alt}
          style={{
            display: 'block',
            maxWidth: '100%',
            ...(minWidth ? { width: '100%', minWidth, objectFit: 'contain' } : {}),
            ...(minHeight ? { height: '100%', minHeight } : {}),
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            padding: '4px',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            zIndex: 20,
          }}
        >
          <img
            src={enlargeIconUrl}
            alt="Enlarge"
            style={{
              width: '20px',
              height: '20px',
              filter: 'brightness(0) invert(1)',
              border: '0',
              margin: '0',
              borderRadius: '0',
              display: 'block',
            }}
          />
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
