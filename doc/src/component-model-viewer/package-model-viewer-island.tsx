"use client";

/** @jsxRuntime automatic */
/** @jsxImportSource preact */

import type { RefObject } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { decodeModelDescriptor } from "../../component-docs/core/model-descriptor.ts";
import { PreviewEnlargeDialog } from "../component-preview/preview-enlarge-dialog.tsx";
import { setViewerState } from "./viewer-state.ts";

export type PackageModelViewerIslandProps = { readonly descriptor: string };

type ViewerInstance = "inline" | "dialog";

export function PackageModelViewerIsland({ descriptor: encoded }: PackageModelViewerIslandProps) {
  const descriptor = decodeModelDescriptor(encoded);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [isDialogOpen, setDialogOpen] = useState(false);

  return (
    <>
      <ModelViewerSurface
        encoded={encoded}
        instance="inline"
        enlargeTriggerRef={triggerRef}
        onEnlarge={() => setDialogOpen(true)}
      />
      <PreviewEnlargeDialog
        isOpen={isDialogOpen}
        onClose={() => setDialogOpen(false)}
        returnFocusRef={triggerRef}
        labelId="zld-model-preview-dialog-title"
        title={`Interactive 3D view of shared footprint package ${descriptor.packageLabel}`}
        variant="model"
      >
        {isDialogOpen && <ModelViewerSurface encoded={encoded} instance="dialog" />}
      </PreviewEnlargeDialog>
    </>
  );
}

function ModelViewerSurface({
  encoded,
  enlargeTriggerRef,
  instance,
  onEnlarge,
}: {
  readonly encoded: string;
  readonly enlargeTriggerRef?: RefObject<HTMLButtonElement>;
  readonly instance: ViewerInstance;
  readonly onEnlarge?: () => void;
}) {
  const descriptor = decodeModelDescriptor(encoded);
  const rootRef = useRef<HTMLElement>(null);
  const captionId = `package-model-${descriptor.packageId}-${instance}`;

  useEffect(() => {
    const root = rootRef.current;
    if (root === null) return;

    let disposed = false;
    let cleanup: (() => void) | undefined;
    // The controller is owned here, not inside the runtime: an unmount that
    // lands while the WRL fetch is still in flight has to cancel that fetch,
    // and only the island knows when it unmounts. `mountModelViewer` takes the
    // signal as a required third argument so a caller cannot forget it.
    const abort = new AbortController();
    setViewerState(root, "loading", "Loading interactive package model…");

    void import("./viewer-runtime.ts")
      .then(({ mountModelViewer }) => {
        if (disposed) throw new DOMException("Viewer disposed", "AbortError");
        return mountModelViewer(root, descriptor, abort.signal);
      })
      .then((mounted) => {
        if (disposed) mounted.dispose();
        else cleanup = () => mounted.dispose();
      })
      .catch(() => {
        // An abort is this component's own teardown, not a failure a reader
        // should be told about, and by then `root` is detached anyway.
        if (!disposed) {
          setViewerState(
            root,
            "error",
            "The interactive package model could not be displayed. The package reference on this page is still available.",
          );
        }
      });

    return () => {
      disposed = true;
      abort.abort();
      cleanup?.();
    };
  }, [encoded]);

  return (
    <figure
      ref={rootRef}
      className="zld-model-viewer"
      data-component-model-viewer-root=""
      data-model-url={descriptor.modelUrl}
      data-model-viewer-instance={instance}
      data-viewer-state="no-js"
      aria-labelledby={captionId}
    >
      <figcaption id={captionId} className="zld-model-viewer__caption">
        <strong>Shared footprint package:</strong>{" "}
        {descriptor.packageLabel.split(/(?<=[_\/-])/u).map((segment, index) => (
          <span key={index}>{segment}<wbr /></span>
        ))}
      </figcaption>
      <div className="zld-model-viewer__viewport-frame">
        <div
          className="zld-model-viewer__viewport"
          data-model-viewer-viewport=""
          tabIndex={0}
          aria-label={`Interactive 3D view of shared footprint package ${descriptor.packageLabel}`}
        />
        {onEnlarge !== undefined && (
          <button
            ref={enlargeTriggerRef}
            type="button"
            className="zld-preview-enlarge-button"
            data-component-preview-enlarge="model"
            aria-label={`Enlarge 3D preview for ${descriptor.packageLabel}`}
            title={`Enlarge 3D preview for ${descriptor.packageLabel}`}
            onClick={onEnlarge}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" focusable="false">
              <path d="M9 3H3v6M15 3h6v6M9 21H3v-6M15 21h6v-6" />
            </svg>
          </button>
        )}
      </div>
      <p className="zld-model-viewer__status" data-model-viewer-status="" role="status" aria-live="polite">
        Interactive inspection requires JavaScript and WebGL. The package identity remains available in this page.
      </p>
      <p className="zld-model-viewer__notice">
        This geometry represents a shared footprint package and may not exactly match the manufacturer part.
      </p>
    </figure>
  );
}

PackageModelViewerIsland.displayName = "PackageModelViewerIsland";
