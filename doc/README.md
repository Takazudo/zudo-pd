# USB-PD Modular Synth Power Documentation

This directory contains documentation for the USB-PD powered modular synthesizer power supply.

## Setup

```bash
# Install dependencies
pnpm install

# Start development server
pnpm start

# Production build
pnpm build
```

## Directory Structure

```
doc/
├── docs/              # Documentation Markdown files
│   ├── overview/      # Project overview, circuit diagrams, BOM
│   ├── components/    # Individual component specifications
│   ├── learning/      # Circuit design learning notes
│   ├── how-to/        # How-to guides
│   ├── inbox/         # Quick reference and misc docs
│   ├── misc/          # Miscellaneous documentation
│   └── _fragments/    # Reusable fragments (SVGs, etc.)
├── src/               # React components and styles
│   ├── components/    # Custom React components
│   ├── css/           # Custom CSS
│   ├── pages/         # Custom pages
│   └── theme/         # Theme customizations
├── static/            # Static assets (images, etc.)
│   ├── circuits/      # Circuit diagram SVGs
│   ├── datasheets/    # Component datasheets (PDF)
│   ├── footprints/    # Package preview images (PNG)
│   └── img/           # General images
└── plugins/           # Custom plugins
```

## Adding Documentation

1. Create a new `.md` or `.mdx` file in the appropriate `docs/` subdirectory
2. Set frontmatter:
   ```yaml
   ---
   sidebar_position: 1
   ---
   ```
3. Write content in Markdown/MDX

## Tech Stack

- [Docusaurus 3](https://docusaurus.io/) - Documentation site generator
- [React 19](https://react.dev/) - UI library
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Mermaid](https://mermaid.js.org/) - Diagram rendering

## Commands

- `pnpm start` - Start development server (http://localhost:3000)
- `pnpm build` - Production build
- `pnpm serve` - Preview built site locally
- `pnpm clear` - Clear cache
- `pnpm lint` - Lint code
- `pnpm format` - Format code
