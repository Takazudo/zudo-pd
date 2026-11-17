// Progressive enhancement for the source-bound unified line table. The full
// table remains visible when scripting is unavailable.
function filterCatalogLines(): void {
  const query = document.querySelector<HTMLInputElement>("#catalog-line-query");
  const status = document.querySelector<HTMLSelectElement>("#catalog-line-status");
  const count = document.querySelector<HTMLElement>("#catalog-line-count");
  const table = query?.closest("main")?.querySelector("table");
  if (!query || !status || !count || !table) return;
  const term = query.value.trim().toLocaleLowerCase();
  const rows = Array.from(table.querySelectorAll<HTMLTableRowElement>("tbody tr"));
  let visible = 0;
  for (const row of rows) {
    const key = row.cells[0]?.textContent?.trim() ?? "";
    const matchesScope = status.value === "all" || key.startsWith(`${status.value}:`);
    const matchesTerm = (row.textContent ?? "").toLocaleLowerCase().includes(term);
    row.hidden = !(matchesScope && matchesTerm);
    if (!row.hidden) visible += 1;
  }
  count.textContent = `Showing ${visible} of ${rows.length} lines`;
}

if (typeof document !== "undefined") {
  document.addEventListener("input", (event) => {
    if ((event.target as Element | null)?.id === "catalog-line-query") filterCatalogLines();
  });
  document.addEventListener("change", (event) => {
    if ((event.target as Element | null)?.id === "catalog-line-status") filterCatalogLines();
  });
}
