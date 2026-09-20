"use client";

/** @jsxRuntime automatic */
/** @jsxImportSource preact */

import type { ComponentChildren, JSX, RefObject } from "preact";
import { useCallback, useRef } from "preact/hooks";

import { AFTER_NAVIGATE_EVENT } from "@takazudo/zudo-doc/transitions";
import { useModalDialog } from "@takazudo/zudo-doc/use-modal-dialog";

export type PreviewEnlargeDialogProps = {
  readonly children: ComponentChildren;
  readonly isOpen: boolean;
  readonly labelId: string;
  readonly onClose: () => void;
  readonly returnFocusRef: RefObject<HTMLElement>;
  readonly title: string;
  readonly variant: "footprint" | "model";
};

/**
 * Centre the modal with `inset: 0; margin: auto` rather than a transform.
 *
 * A `transform` on the dialog would establish a containing block for its
 * `position: fixed` descendants, which would trap `.zld-preview-dialog__close`
 * at the dialog's corner instead of the viewport's.
 *
 * `@takazudo/zudo-doc/island-types` exports a byte-identical constant, but this
 * local copy is DELIBERATE and must not be replaced by that import:
 * `presentation.test.ts` ("keeps the dialog transform-free…") asserts these
 * exact literals in this file, so that an upstream change to the package's
 * value cannot silently un-anchor this project's close control. Importing it
 * moves the value outside the guard and turns that test red.
 */
const ENLARGE_DIALOG_STYLE = {
  position: "fixed",
  inset: "0",
  margin: "auto",
} as const;

const FOCUSABLE_SELECTOR =
  'button:not([disabled]),a[href],[tabindex]:not([tabindex="-1"]),input:not([disabled]),select:not([disabled]),textarea:not([disabled])';

/**
 * Shared native-dialog chrome for the controlled component preview adapters —
 * one dialog implementation behind both the footprint image and the 3D model
 * viewer.
 *
 * `useModalDialog` owns native open/close synchronization, focus management,
 * and SPA navigation cleanup. The coordinate-based backdrop hit-test and the
 * wrap-around Tab trap below remain local because the package hook does not
 * provide equivalent behavior.
 */
export function PreviewEnlargeDialog({
  children,
  isOpen,
  labelId,
  onClose,
  returnFocusRef,
  title,
  variant,
}: PreviewEnlargeDialogProps) {
  // The hook's navigation handler calls `dialog.close()` and `onClose()`. Its
  // native close listener can then call `onClose()` again with the open render
  // still captured, so allow only one notification per open cycle.
  const closeNotifiedRef = useRef(false);
  const previousIsOpenRef = useRef(isOpen);
  if (isOpen && !previousIsOpenRef.current) closeNotifiedRef.current = false;
  previousIsOpenRef.current = isOpen;

  const handleClose = useCallback(() => {
    if (closeNotifiedRef.current) return;
    closeNotifiedRef.current = true;
    onClose();
  }, [onClose]);

  const { dialogRef } = useModalDialog({
    isOpen,
    onClose: handleClose,
    navigateEvent: AFTER_NAVIGATE_EVENT,
    backdropClickClose: false,
    manageFocus: true,
    returnFocusRef,
  });

  const closeExplicitly = useCallback(() => {
    dialogRef.current?.close();
    // Native close events are queued; clear controlled content in the same action.
    closeNotifiedRef.current = true;
    onClose();
    returnFocusRef.current?.focus();
  }, [dialogRef, onClose, returnFocusRef]);

  const handleBackdropClick = useCallback((event: JSX.TargetedMouseEvent<HTMLDialogElement>) => {
    const dialog = event.currentTarget;
    // A click on the ::backdrop is reported with the dialog as its target, so
    // "outside" is decided by the pointer position against the dialog box.
    // A keyboard-activated click reports 0,0 with no real coordinates, which
    // `detail === 0` distinguishes from a genuine pointer press.
    if (event.detail === 0) return;
    const rect = dialog.getBoundingClientRect();
    if (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    ) {
      closeExplicitly();
    }
  }, [closeExplicitly]);

  const handleKeyDown = useCallback((event: JSX.TargetedKeyboardEvent<HTMLDialogElement>) => {
    if (event.key !== "Tab") return;
    // A native modal dialog already confines Tab to the top layer; this adds
    // the wrap-around at each end so focus never parks on the dialog box
    // itself between the last and first control.
    const dialog = event.currentTarget;
    const focusable = [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)]
      .filter((element) => element.getClientRects().length > 0);
    const first = focusable.at(0);
    const last = focusable.at(-1);
    if (first === undefined || last === undefined) {
      event.preventDefault();
      dialog.focus();
    } else if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className={`zld-preview-dialog zld-preview-dialog--${variant}`}
      style={ENLARGE_DIALOG_STYLE}
      aria-labelledby={labelId}
      data-component-preview-dialog={variant}
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
    >
      <button
        type="button"
        className="zld-preview-dialog__close"
        aria-label={`Close enlarged ${variant} preview`}
        onClick={closeExplicitly}
      >
        <svg
          className="zld-preview-dialog__close-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
          focusable="false"
        >
          <path d="M5 5l14 14M19 5L5 19" />
        </svg>
      </button>
      <h2 id={labelId} className="zld-preview-dialog__title">{title}</h2>
      <div className="zld-preview-dialog__content">
        {children}
      </div>
    </dialog>
  );
}
