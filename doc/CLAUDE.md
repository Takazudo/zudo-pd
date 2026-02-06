# CLAUDE.md - Documentation Guidelines

This file provides guidance to Claude Code when working with documentation in this directory.

## Deployment

The documentation is automatically deployed to Netlify:

- **Production URL**: https://takazudomodular.com/pj/zudo-pd/
- **Netlify URL**: https://zudopd.netlify.app/pj/zudo-pd/ (rewritten to production URL)
- **Base Path**: `/pj/zudo-pd/`
- **Deployment**: Automatic on every push to `main` branch
- **Technology**: Docusaurus static site deployed via Netlify CLI on GitHub Actions
- **Configuration**: See `.github/workflows/main-deploy.yml` for deployment workflow

## URL Reference Guidelines

When the user provides URLs starting with `http://localhost:3800/pj/zudo-pd/` or `http://zudopd.localhost:3800/pj/zudo-pd/` in the conversation:

- **DO NOT fetch the URL** - These are local documentation URLs served by Docusaurus
- **Instead, find and read the corresponding markdown file** in the `/doc/` directory
- Map URLs to file paths following Docusaurus routing (note: `/pj/zudo-pd/` is the base path):
  - `http://localhost:3800/pj/zudo-pd/` or `http://zudopd.localhost:3800/pj/zudo-pd/` → `/doc/docs/` (root pages)
  - `http://zudopd.localhost:3800/pj/zudo-pd/docs/inbox/overview` → `/doc/docs/inbox/overview.md`
  - `http://zudopd.localhost:3800/pj/zudo-pd/docs/inbox/circuit-diagrams` → `/doc/docs/inbox/circuit-diagrams.md`
- Use the Read tool to access the actual markdown source files
- This provides the raw content without HTML rendering, making it easier to edit and understand

Example:

- User mentions: `http://zudopd.localhost:3800/pj/zudo-pd/docs/inbox/current-status`
- Read file: `/doc/docs/inbox/current-status.md`

## Documentation Directory Structure

- `docs/` - **Primary documentation** (Docusaurus-based, organized)
  - `overview/` - Project overview, circuit diagrams, BOM
  - `components/` - Individual component datasheets and specifications
  - `learning/` - Circuit design learning notes
  - `how-to/` - How-to guides (KiCad workflow, parts download, SVG export, circuit diagrams)
  - `inbox/` - Quick reference and miscellaneous docs
  - `misc/` - Miscellaneous documentation
  - `_fragments/` - Reusable fragments (footprint SVGs for React imports)
- `static/` - **Documentation assets** (images, PDFs, SVGs)
  - `circuits/` - Circuit diagram SVGs
  - `footprints/` - Component package preview images (PNG)
  - `datasheets/` - Component datasheets and package specs (PDF)
  - `kicad/` - KiCad setup screenshots

## MDX Syntax Rules

**CRITICAL**: This documentation uses MDX (Markdown + JSX), which requires special handling of certain characters.

### Common MDX Syntax Errors to Avoid

#### 1. Less-than/Greater-than Characters (`<` and `>`)

**❌ WRONG** - Direct use of `<` or `>` in text:

```markdown
Float or pull low (<0.8V) = Enable
Input voltage range: 4V - 40V (>5V recommended)
```

**✅ CORRECT** - Use HTML entities:

```markdown
Float or pull low (&lt;0.8V) = Enable
Input voltage range: 4V - 40V (&gt;5V recommended)
```

**Why**: MDX interprets `<` as the start of a JSX tag. When followed by a number or invalid character, it causes compilation errors like:

```
Error: Unexpected character `0` (U+0030) before name, expected a character that can start a name
```

**Alternative solutions**:

- Use HTML entities: `&lt;` for `<`, `&gt;` for `>`
- Use code blocks: `` `<0.8V` ``
- Rephrase: "below 0.8V" instead of "<0.8V"

#### 2. Curly Braces (`{` and `}`)

**❌ WRONG** - Direct use in text:

```markdown
Use the formula {VIN - VOUT} to calculate dropout
```

**✅ CORRECT** - Escape or use code:

```markdown
Use the formula `{VIN - VOUT}` to calculate dropout
```

**Why**: MDX interprets `{...}` as JavaScript expressions.

#### 3. Common Characters That Need Escaping

| Character | HTML Entity           | When to Escape                                 |
| --------- | --------------------- | ---------------------------------------------- |
| `<`       | `&lt;`                | Always in regular text (except in code blocks) |
| `>`       | `&gt;`                | Always in regular text (except in code blocks) |
| `{`       | `&#123;` or backticks | When not used for JSX/MDX syntax               |
| `}`       | `&#125;` or backticks | When not used for JSX/MDX syntax               |

#### 4. Safe Zones (No Escaping Needed)

These locations don't require escaping:

- Inside code blocks (triple backticks)
- Inside inline code (single backticks)
- Inside HTML comments `<!-- ... -->`

**Example**:

```markdown
✅ This is safe: `<0.8V`
✅ This is safe in code blocks:
```

VIN < 5V will cause shutdown
< and > are safe here

```
❌ This will error: Voltage <0.8V is too low
✅ This is correct: Voltage &lt;0.8V is too low
```

### Quick Checklist Before Saving MDX Files

- [ ] Search for `<` in regular text (not in code blocks) → Replace with `&lt;`
- [ ] Search for `>` in regular text (not in code blocks) → Replace with `&gt;`
- [ ] Search for `{` `}` in regular text → Wrap in backticks or use entities
- [ ] Test compilation by checking Docusaurus dev server for errors

## Circuit Diagram Writing Rules

When creating or updating circuit diagrams in the documentation:

### 1. Use ASCII Art in Code Blocks

Always illustrate circuits using ASCII art within markdown code blocks:

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

### 2. Always Include Full Connection List

Under every circuit diagram, provide a detailed connection list showing:

- Component identifiers (U1, R1, C1, etc.)
- Pin numbers and names
- Connection destinations
- Signal names or voltage levels

Example:

```
Connections:
- J1 (USB-C) VBUS → U1 (CH224D) VIN (pin 1)
- J1 (USB-C) CC1 → U1 (CH224D) CC1 (pin 5) via R1 (5.1kΩ)
- J1 (USB-C) CC2 → U1 (CH224D) CC2 (pin 6) via R2 (5.1kΩ)
- U1 (CH224D) VOUT (pin 3) → C1 (10µF) → GND
- U1 (CH224D) VOUT (pin 3) → U2 (LM2596S) VIN (pin 1)
```

### 3. ASCII Art Best Practices

#### THE GOLDEN RULES for Clear ASCII Schematics

**Rule 1: 🚫 NEVER cross lines unless they form an electrical junction (connection point)**

If two signals cross paths:

- If they connect electrically: Use a junction symbol and clearly show the connection
- If they don't connect: **Route one of them differently to avoid the crossing**

**Rule 2: 🚫 NEVER cross lines over text labels - it looks like they're connected**

When a vertical or horizontal line passes over a text label, it creates ambiguity:

- Does the line connect to that label?
- Or does it just pass through?

**Solutions**:

1. Route lines around labels
2. Remove intermediate labels that would be crossed
3. **Route vertically in the opposite direction** - If a downward line crosses labels, route it upward instead to use empty space

**❌ WRONG** - Lines crossing without junction (ambiguous):

```
Signal A  ──┼──  (is this connected or just passing?)
            │
         Signal B
```

**❌ WRONG** - Lines crossing over labels (ambiguous):

```
Output ──┬──→ Load
         │
        GND      ← Label
         │       ← Is this line connected to the GND label above?
        C1       ← Or just passing through to C1?
```

**✅ CORRECT** - Route around to avoid crossing:

```
Signal A  ────────  (clearly not connected)

         Signal B
            │
```

**✅ CORRECT** - Remove intermediate labels to prevent crossing:

```
Output ──┬──→ Load
         │
         ├─→ C1 ─→ GND  ← No label in the path
            470µF
```

**✅ CORRECT** - Use explicit junction when signals DO connect:

```
Signal A  ──┬──  (T-junction: A and B connect here)
            │
         Signal B
```

#### Box-Drawing Characters

- Use box-drawing characters for clear visual flow: `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴`
- Use arrows to show signal direction: `→ ←`
- **NEVER use `┼` (cross) unless it's an actual 4-way junction** - it suggests connection when there may be none
- Label all voltage levels and current ratings
- Keep diagrams concise but complete
- Group related components visually

#### Junction vs Crossing Guidelines

| Symbol          | Meaning            | When to Use                                       |
| --------------- | ------------------ | ------------------------------------------------- |
| `┬`             | T-junction (3-way) | One signal splits into two paths                  |
| `├` `┤` `┴`     | Side junctions     | Signal branches from side                         |
| `─` `│`         | Straight lines     | No branching, continuous path                     |
| `┼`             | **AVOID**          | Ambiguous! Looks like connection but might not be |
| `┌` `┐` `└` `┘` | Corners            | Change direction 90°                              |

#### Using Labels to Avoid Crossings

**Best Practice**: When connections would require crossing wires, use arrow-to-label notation instead of drawing physical wires across the diagram.

**✅ CORRECT** - Use labels to indicate connections:

```
IC Pin ├2─→ Tap      ← Pin points to "Tap" label (no wire drawn)

Output ─┬─→ R1 ──┬─→ Tap ─→ R2 ─→ GND
        │         ↑
        │    This "Tap" matches the label above
```

**❌ WRONG** - Drawing wire creates crossings:

```
IC Pin ├2───┼────┼─→ Junction   ← Crosses other signals!
            │    │
```

**Key points**:

- Use `─→ Label` notation for pins that connect to distant points
- The label name indicates the connection without drawing a wire
- Common labels: `GND`, `Tap`, `VCC`, `Output`
- Example: `FB ├2─→ Tap` means "FB pin 2 connects to the point labeled 'Tap'"
- Example: `GND ├1─→ GND` means "GND pin 1 connects to system ground"

#### Parallel Components (Shunt Elements)

When showing components connected in parallel (between a signal and GND):

- Draw them as vertical drops from the signal line
- Make it visually obvious they're shunt elements, not series

**Example - Output filter capacitor:**

```
Output ──┬──→ Load
         │
        C1 (470µF)   ← Clearly parallel
         │
        GND
```

**Not this** (looks like series):

```
Output ── C1 ── Load   ← Confusing! Looks like C1 blocks current
```

#### Column Alignment (Preventing "Sliding Lines")

**Problem**: In monospace fonts, vertical lines can appear misaligned if labels have different character widths.

**❌ WRONG** - Lines slide because labels have different widths:

```
            │
           GND    ← 3 characters
            │
           C3     ← 2 characters
            │
          470µF   ← 5 characters
            │     ← Lines appear to "slide" left/right!
```

**✅ CORRECT** - Maintain consistent column spacing:

```
            │
           GND
            │
           C3
          470µF
            │     ← Vertical line stays in same column!
```

**Best practices**:

- Plan your column widths before drawing
- Use consistent spacing after component labels
- Align vertical bars (`│`) in the same character column throughout
- Test your diagram in a monospace font viewer before committing

### 4. Component Notation

- **ICs**: Use part numbers (CH224D, LM2596S, etc.)
- **Passives**: Show values with units (10µF, 5.1kΩ, 33µH)
- **Voltages**: Show at each stage (+15V, +13.5V, +12V, etc.)
- **Currents**: Show max ratings (1.2A, 800mA, etc.)

## Validating ASCII Diagrams with Preview Tool

**CRITICAL**: Always preview ASCII diagrams in monospace font before finalizing to catch label crossing issues and alignment problems.

**Preview method using headless-browser**:

```bash
cat > /tmp/preview.html << 'EOF'
<html>
<head>
  <style>
    body {
      background: #1e1e1e;
      color: #d4d4d4;
      font-family: 'Courier New', Courier, monospace;
      font-size: 14px;
      line-height: 1.4;
      padding: 20px;
      white-space: pre;
    }
  </style>
</head>
<body>[PASTE DIAGRAM HERE]</body>
</html>
EOF
node ~/.claude/skills/headless-browser/scripts/headless-check.js --url file:///tmp/preview.html --screenshot viewport
```

This renders the diagram exactly as users will see it in monospace font, revealing:

- Label crossings that aren't visible in plain text
- Column alignment issues ("sliding" vertical bars)
- Spacing problems
- Junction ambiguities

## Integration with Main Documentation

This documentation is part of a Docusaurus site. When referencing circuit diagrams:

- Place diagrams in the appropriate section (overview.md, circuit-diagrams.md, etc.)
- Cross-reference from other documents using relative links
- Keep technical accuracy paramount
- Use English for all text and labels
- **Preview all diagrams in monospace** before committing

## Sidebar Management

**CRITICAL**: When adding new documentation pages or reorganizing content, you MUST update the sidebar configuration in `sidebars.js`.

### When to Update the Sidebar

Update `sidebars.js` whenever you:

- **Add a new page** to any documentation category
- **Remove a page** from the documentation
- **Rename a page** (update the path reference)
- **Reorganize the documentation structure**

### Sidebar Configuration Location

**File:** `/doc/sidebars.js`

### Sidebar Structure

The project uses three main sidebars:

```javascript
const sidebars = {
  inboxSidebar: [
    'inbox/index',
    'inbox/current-status',
    'inbox/overview',
    'inbox/circuit-diagrams',
    'inbox/parts-list',
    'inbox/footprint-preview',
    'inbox/quick-reference',
  ],
  partsSidebar: [
    'parts/index',
    'parts/ch224d',
    'parts/lm2596s-adj',
    // ... more parts
  ],
  learningSidebar: [
    'learning/index',
    'learning/open-drain-pg-pin',
    'learning/buck-converter-feedback',
  ],
};
```

### Adding a New Page

**Step 1:** Create the markdown file in the appropriate directory:

```bash
# Example: Adding a new page to inbox
touch docs/inbox/my-new-page.md
```

**Step 2:** Update `sidebars.js` to include the new page:

```javascript
inboxSidebar: [
  'inbox/index',
  'inbox/current-status',
  'inbox/my-new-page',  // ← Add new page here
  'inbox/overview',
  // ...
],
```

**Step 3:** Verify the sidebar updates (Docusaurus hot-reloads automatically)

- The new page should appear in the sidebar immediately
- Click through to verify navigation works
- Check that the page title displays correctly

### Sidebar Best Practices

1. **Logical Ordering**: Group related pages together
   - Put overview/index pages first
   - Group technical details together
   - Put reference materials last

2. **Path Format**: Use relative paths without file extensions

   ```javascript
   'inbox/my-page'; // ✅ Correct
   'inbox/my-page.md'; // ❌ Wrong - no extension
   '/inbox/my-page'; // ❌ Wrong - no leading slash
   ```

3. **Consistent Naming**: Match the file path exactly

   ```
   docs/inbox/my-page.md  →  'inbox/my-page'
   docs/parts/ch224d.md   →  'parts/ch224d'
   ```

4. **Categories**: Use the appropriate sidebar for each content type
   - `inboxSidebar`: Main documentation (overview, specs, diagrams)
   - `partsSidebar`: Individual component datasheets
   - `learningSidebar`: Educational content and design notes

### Example: Adding Footprint Preview

When the `footprint-preview.md` page was added to `/doc/docs/inbox/`, the sidebar was updated:

```javascript
inboxSidebar: [
  'inbox/index',
  'inbox/current-status',
  'inbox/overview',
  'inbox/circuit-diagrams',
  'inbox/parts-list',
  'inbox/footprint-preview',  // ← Added here
  'inbox/quick-reference',
],
```

**Result:** The "Footprint Preview" page now appears in the INBOX sidebar between "Parts List" and "Quick Reference".

### Troubleshooting

**Problem:** New page doesn't appear in sidebar

- ✅ Check that the file path in `sidebars.js` matches the actual file location
- ✅ Verify no file extension in the path
- ✅ Restart the dev server if hot-reload fails: `npm start`

**Problem:** Page shows "404 Not Found"

- ✅ Verify the markdown file exists at the correct path
- ✅ Check for typos in the sidebar path
- ✅ Ensure the file has proper frontmatter (title, etc.)

**Problem:** Sidebar order is wrong

- ✅ Reorder entries in the `sidebars.js` array
- ✅ Array order determines display order in the sidebar

## Circuit Design Workflow

**For detailed instructions on creating circuit diagrams, see:**

- **[Create Circuit SVG Files Guide](/doc/docs/knowledge/create-circuit-svg.md)** - Complete workflow for generating professional circuit diagrams using schemdraw

### Quick Reference

When creating new circuit diagrams:

1. **Collect Parts Data** - Use `/jlcpcb` skill to verify component availability
2. **Create ASCII Art Draft** - Draft circuit with connection list (follows ASCII Art Best Practices above)
3. **Generate Schemdraw Diagram** - Use `/schemdraw-circuit-generator` skill
4. **Integrate into Documentation** - Use `CircuitSvg` component
5. **Verify and Commit** - Test click-to-enlarge, commit both SVG and Python source

**Configuration:**

- Black foreground with transparent background
- Background color: transparent (allows HTML container `oklch(86.9% 0.005 56.366)` to show through)
- Font: Arial, 11pt
- SVG output: `docs/_fragments/*.svg`
- Python source: `/diagram-sources/*.py` (at repository root)
