import { useEffect, useRef } from 'react';

interface CircuitDialogProps {
  isOpen: boolean;
  onClose: () => void;
  alt: string;
  src: string;
}

export default function CircuitDialog({ isOpen, onClose, alt, src }: CircuitDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // Handle ESC key via the cancel event
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleCancel = (event: Event) => {
      event.preventDefault();
      onClose();
    };

    dialog.addEventListener('cancel', handleCancel);
    return () => {
      dialog.removeEventListener('cancel', handleCancel);
    };
  }, [onClose]);

  return (
    <dialog
      ref={dialogRef}
      aria-label={alt}
      style={{
        position: 'fixed',
        inset: 0,
        margin: 0,
        maxHeight: '100vh',
        height: '100vh',
        maxWidth: '100vw',
        width: '100vw',
        background: 'transparent',
        padding: 0,
        zIndex: 1000,
        border: 'none',
      }}
    >
      {/* Backdrop: clicking here closes the dialog */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Close button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          aria-label="Close dialog"
          style={{
            position: 'fixed',
            top: '16px',
            right: '16px',
            zIndex: 100,
            padding: '12px',
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid white',
            borderRadius: '4px',
            color: 'white',
            fontSize: '24px',
            lineHeight: '1',
            cursor: 'pointer',
          }}
        >
          &times;
        </button>

        {/* Content: stop propagation so clicking image doesn't close */}
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '90vw',
            height: '90vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--color-bg)',
            padding: '20px',
          }}
        >
          <img
            src={src}
            alt={alt}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
            }}
          />
        </div>
      </div>
    </dialog>
  );
}
