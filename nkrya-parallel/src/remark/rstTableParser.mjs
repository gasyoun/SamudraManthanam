// Ported verbatim (logic unchanged) from buhler-sanskrit-book's
// src/remark/rstTableParser.ts — the canonical no-Pandoc-dependency RST
// grid-table parser, adapted from TypeScript to plain JS for csl-guides
// (which has no TS toolchain). Keep both copies in sync by hand; there is
// no shared package yet.

// A border line is made only of '+', '-', '=', spaces and has at least one '+'.
const isBorderLine = (line) => line.includes('+') && !/[^\s+\-=]/.test(line);

export function parseRstGridTable(source) {
  // Normalize: drop surrounding blank lines, pad to a rectangular char grid.
  const lines = source.replace(/\s+$/, '').split('\n');
  while (lines.length && lines[0].trim() === '') lines.shift();
  while (lines.length && lines[lines.length - 1].trim() === '') lines.pop();
  if (lines.length === 0) return {headerRows: [], bodyRows: []};
  const width = Math.max(...lines.map((l) => l.length));
  const grid = lines.map((l) => l.padEnd(width, ' '));

  // Row boundaries: indices of border lines. Column boundaries: '+' columns on
  // the first border line (the top rule always contains every column separator).
  const rowBoundaries = [];
  grid.forEach((line, i) => {
    if (isBorderLine(line)) rowBoundaries.push(i);
  });
  if (rowBoundaries.length < 2) {
    throw new Error(
      `remarkRstTable: not a valid RST grid table (need at least two border lines):\n${source}`,
    );
  }
  const topRule = grid[rowBoundaries[0]];
  const colBoundaries = [];
  for (let col = 0; col < width; col++) {
    if (topRule[col] === '+') colBoundaries.push(col);
  }
  if (colBoundaries.length < 2) {
    throw new Error(
      `remarkRstTable: not a valid RST grid table (need at least two column boundaries):\n${source}`,
    );
  }

  const R = rowBoundaries.length - 1; // number of grid rows
  const C = colBoundaries.length - 1; // number of grid columns

  // Header separator = first border line containing '='. -1 if none.
  const headerSep = rowBoundaries.find((i) => grid[i].includes('=')) ?? -1;

  // A vertical separator exists at column X over the content lines (top, bottom)
  // iff every interior char is '|'.
  const hasVerticalBorder = (col, top, bottom) => {
    for (let li = top + 1; li < bottom; li++) {
      if (grid[li][col] !== '|') return false;
    }
    return true;
  };
  // A horizontal separator exists on line Y over columns (left, right) iff every
  // interior char is a rule char ('-', '=', '+'). A merged-down cell has spaces.
  const hasHorizontalBorder = (line, left, right) => {
    for (let col = left + 1; col < right; col++) {
      const ch = grid[line][col];
      if (ch !== '-' && ch !== '=' && ch !== '+') return false;
    }
    return true;
  };

  const consumed = Array.from({length: R}, () => new Array(C).fill(false));
  const startCell = Array.from({length: R}, () => new Array(C).fill(null));

  for (let r = 0; r < R; r++) {
    for (let c = 0; c < C; c++) {
      if (consumed[r][c]) continue;

      // Extend right while no vertical border closes the cell.
      let c2 = c;
      while (
        c2 + 1 < C &&
        !hasVerticalBorder(colBoundaries[c2 + 1], rowBoundaries[r], rowBoundaries[r + 1])
      ) {
        c2++;
      }
      // Extend down while no horizontal border closes the cell (full cell width).
      let r2 = r;
      while (
        r2 + 1 < R &&
        !hasHorizontalBorder(rowBoundaries[r2 + 1], colBoundaries[c], colBoundaries[c2 + 1])
      ) {
        r2++;
      }

      // Extract text from interior lines within the cell's column band.
      const parts = [];
      for (let li = rowBoundaries[r] + 1; li < rowBoundaries[r2 + 1]; li++) {
        const seg = grid[li].slice(colBoundaries[c] + 1, colBoundaries[c2 + 1]).trim();
        if (seg) parts.push(seg);
      }

      const header = headerSep >= 0 && rowBoundaries[r] < headerSep;
      startCell[r][c] = {
        text: parts.join(' '),
        rowSpan: r2 - r + 1,
        colSpan: c2 - c + 1,
        header,
      };
      for (let rr = r; rr <= r2; rr++) {
        for (let cc = c; cc <= c2; cc++) consumed[rr][cc] = true;
      }
    }
  }

  // Assemble output rows: each cell listed once, in its starting grid row.
  const headerRows = [];
  const bodyRows = [];
  for (let r = 0; r < R; r++) {
    const row = [];
    for (let c = 0; c < C; c++) {
      const cell = startCell[r][c];
      if (cell) row.push(cell);
    }
    if (row.length === 0) continue;
    if (headerSep >= 0 && rowBoundaries[r] < headerSep) headerRows.push(row);
    else bodyRows.push(row);
  }

  return {headerRows, bodyRows};
}
