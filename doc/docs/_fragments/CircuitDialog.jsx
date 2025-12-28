import React, { useEffect, useRef, useCallback } from 'react';

export default function CircuitDialog({ isOpen, onClose, children, alt }) {
  const dialogRef = useRef(null);

  // Open/close dialog
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // Handle backdrop click
  const handleDialogClick = useCallback(
    (event) => {
      const rect = dialogRef.current?.getBoundingClientRect();
      if (rect) {
        const clickedInDialog =
          event.clientX >= rect.left &&
          event.clientX <= rect.right &&
          event.clientY >= rect.top &&
          event.clientY <= rect.bottom;

        // If clicked outside the dialog content (on the backdrop)
        if (!clickedInDialog || event.target === dialogRef.current) {
          onClose();
        }
      }
    },
    [onClose],
  );

  // Handle ESC key
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleCancel = (event) => {
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
      onClick={handleDialogClick}
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
      <style>{`
        dialog::backdrop {
          background: rgba(0, 0, 0, 0.8);
        }
      `}</style>

      <div
        style={{
          position: 'relative',
          display: 'flex',
          height: '100%',
          width: '100%',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
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
            transition: 'background 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
          }}
        >
          ×
        </button>

        {/* Content */}
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.5)',
          }}
        >
          {children}
        </div>
      </div>
    </dialog>
  );
}
