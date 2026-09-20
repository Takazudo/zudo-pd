"use client";

/** @jsxRuntime automatic */
/** @jsxImportSource preact */

import { useEffect, useRef, useState } from "preact/hooks";

import { PreviewEnlargeDialog } from "./preview-enlarge-dialog.tsx";

export type FootprintPreviewIslandProps = {
  readonly assetUrl: string;
  readonly footprintName: string;
  readonly footprintPath: string;
};

/**
 * `data-footprint-preview-state` flips "no-js" -> "ready" once the image has
 * actually decoded. The enlarge trigger is
 * scoped to the "ready" state in CSS, so a reader whose JavaScript never runs
 * is never offered a control that cannot work — the `<img>` link and the
 * caption's "Open SVG" link remain their whole affordance.
 */
export function FootprintPreviewIsland({ assetUrl, footprintName, footprintPath }: FootprintPreviewIslandProps) {
  const imageRef = useRef<HTMLImageElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [isImageReady, setImageReady] = useState(false);
  const [isDialogOpen, setDialogOpen] = useState(false);
  const alt = `Footprint preview for ${footprintName}`;

  useEffect(() => {
    const image = imageRef.current;
    if (image === null) return;
    const markReady = () => setImageReady(image.naturalWidth > 0);
    if (image.complete) markReady();
    else image.addEventListener("load", markReady, { once: true });
    return () => image.removeEventListener("load", markReady);
  }, [assetUrl]);

  return (
    <figure
      className="zld-component-references__footprint"
      data-footprint-preview-state={isImageReady ? "ready" : "no-js"}
    >
      <div className="zld-component-references__footprint-frame">
        <a href={assetUrl} aria-label={`Open footprint SVG for ${footprintName}`}>
          <img ref={imageRef} src={assetUrl} alt={alt} onLoad={() => setImageReady(true)} />
        </a>
        <button
          ref={triggerRef}
          type="button"
          className="zld-preview-enlarge-button"
          data-component-preview-enlarge="footprint"
          aria-label={`Enlarge footprint preview for ${footprintName}`}
          title={`Enlarge footprint preview for ${footprintName}`}
          onClick={() => setDialogOpen(true)}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" focusable="false">
            <path d="M9 3H3v6M15 3h6v6M9 21H3v-6M15 21h6v-6" />
          </svg>
        </button>
      </div>
      <figcaption>
        Shared footprint package: <code>{footprintName}</code>. <a href={assetUrl}>Open SVG</a>
        <br />
        Source: <code>{footprintPath}</code>
      </figcaption>
      <PreviewEnlargeDialog
        isOpen={isDialogOpen}
        onClose={() => setDialogOpen(false)}
        returnFocusRef={triggerRef}
        labelId="zld-footprint-preview-dialog-title"
        title={alt}
        variant="footprint"
      >
        {isDialogOpen && <img src={assetUrl} alt={alt} />}
      </PreviewEnlargeDialog>
    </figure>
  );
}

FootprintPreviewIsland.displayName = "FootprintPreviewIsland";
