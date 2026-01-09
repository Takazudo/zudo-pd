#!/usr/bin/env node
/**
 * Generate category-nav.json for auto-generating navigation lists in category index pages
 * Separate from generate-doc-titles.js - this is a standalone feature
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const DOCS_DIR = path.join(__dirname, '../docs');
const OUTPUT_FILE = path.join(__dirname, '../src/data/category-nav.json');

// Categories to generate navigation for
const CATEGORIES = ['inbox', 'components', 'learning', 'how-to', 'misc'];

/**
 * Find all .md and .mdx files in a specific category directory
 */
function findMarkdownFiles(categoryDir) {
  if (!fs.existsSync(categoryDir)) {
    return [];
  }

  const files = fs.readdirSync(categoryDir);
  return files
    .filter((file) => file.endsWith('.md') || file.endsWith('.mdx'))
    .map((file) => path.join(categoryDir, file));
}

/**
 * Extract title from markdown file
 */
function extractTitle(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');

  // Try frontmatter first
  try {
    const { data } = matter(content);
    if (data.title) {
      return data.title;
    }
  } catch (e) {
    // Ignore frontmatter errors
  }

  // Fall back to first H1 heading
  const h1Match = content.match(/^#\s+(.+)$/m);
  if (h1Match) {
    return h1Match[1].trim();
  }

  return null;
}

/**
 * Extract sidebar_position from frontmatter (for sorting)
 */
function extractSidebarPosition(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');

  try {
    const { data } = matter(content);
    if (typeof data.sidebar_position === 'number') {
      return data.sidebar_position;
    }
  } catch (e) {
    // Ignore errors
  }

  return 999; // Default to end
}

/**
 * Get doc ID from file path (relative to docs dir, without extension)
 */
function getDocId(filePath, category) {
  const fileName = path.basename(filePath).replace(/\.(md|mdx)$/, '');
  return `${category}/${fileName}`;
}

/**
 * Check if file is an index file
 */
function isIndexFile(filePath) {
  const fileName = path.basename(filePath);
  return fileName === 'index.md' || fileName === 'index.mdx';
}

function main() {
  console.log('Generating category-nav.json...');

  const categoryNav = {};

  CATEGORIES.forEach((category) => {
    const categoryDir = path.join(DOCS_DIR, category);
    const files = findMarkdownFiles(categoryDir);

    const pages = files
      .filter((filePath) => !isIndexFile(filePath)) // Exclude index files
      .map((filePath) => {
        const docId = getDocId(filePath, category);
        const title = extractTitle(filePath);
        const position = extractSidebarPosition(filePath);

        return {
          docId,
          title: title || docId,
          position,
        };
      })
      .sort((a, b) => a.position - b.position); // Sort by sidebar_position

    categoryNav[category] = pages;
    console.log(`  ${category}: ${pages.length} pages`);
  });

  // Ensure output directory exists
  const outputDir = path.dirname(OUTPUT_FILE);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Write JSON file
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(categoryNav, null, 2) + '\n');

  console.log(`\n✅ Generated ${OUTPUT_FILE}`);
}

main();
