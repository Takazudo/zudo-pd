import type { ReactNode } from 'react';
import sidebars from '@site/sidebars';

type SidebarItem =
  | string
  | {
      type: string;
      label?: string;
      id?: string;
      items?: SidebarItem[];
      link?: { id: string };
    };

type Sidebars = Record<string, SidebarItem[]>;

const SIDEBAR_LABELS: Record<string, string> = {
  inboxSidebar: 'INBOX',
};

function renderSidebarItem(item: SidebarItem): ReactNode {
  // String item (doc ID)
  if (typeof item === 'string') {
    return (
      <li key={item}>
        <a href={`/docs/${item}`}>{item}</a>
      </li>
    );
  }

  // Doc type
  if (item.type === 'doc' && 'id' in item) {
    const label = 'label' in item ? item.label : item.id;
    return (
      <li key={item.id || label}>
        <a href={`/docs/${item.id}`}>{label}</a>
      </li>
    );
  }

  // Category with items
  if (item.type === 'category' && item.items) {
    return (
      <li key={item.label}>
        <strong>{item.label}:</strong>
        <ul>{item.items.map((subItem) => renderSidebarItem(subItem))}</ul>
      </li>
    );
  }

  return null;
}

export default function DocsSitemap(): ReactNode {
  const typedSidebars = sidebars as Sidebars;

  return (
    <section style={{ marginTop: '3rem' }}>
      <h2>All Documents</h2>
      <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
        Direct links to all documentation pages (auto-generated from sidebars.js)
      </p>

      {Object.entries(SIDEBAR_LABELS).map(([sidebarId, label]) => {
        const sidebarItems = typedSidebars[sidebarId];

        if (!sidebarItems || !label) {
          return null;
        }

        return (
          <details key={sidebarId} open style={{ marginBottom: '1rem' }}>
            <summary
              style={{
                fontSize: '1.3rem',
                fontWeight: '600',
                padding: '0.5rem 0',
                cursor: 'pointer',
                userSelect: 'none',
                listStyle: 'none',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <span style={{ marginRight: '0.5rem' }}>▶</span>
              {label}
            </summary>
            <ul style={{ marginTop: '0.5rem' }}>
              {sidebarItems.map((item) => renderSidebarItem(item))}
            </ul>
          </details>
        );
      })}

      <style>{`
        details[open] > summary > span {
          transform: rotate(90deg);
          display: inline-block;
        }
        details > summary {
          transition: all 0.2s ease;
        }
        details > summary:hover {
          color: var(--ifm-color-primary);
        }
        details > summary > span {
          transition: transform 0.2s ease;
          font-size: 0.8em;
        }
      `}</style>
    </section>
  );
}
