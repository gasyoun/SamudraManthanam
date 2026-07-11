// Ported verbatim (logic unchanged) from buhler-sanskrit-book's
// src/remark/rstTableAst.ts — builds real mdxJsxFlowElement <table> nodes with
// true rowSpan/colSpan attributes (mdast's own tableCell type has no such
// fields, which is why this bypasses mdast tables entirely and emits raw MDX
// JSX). Adapted from TypeScript to plain JS for csl-guides.
import {fromMarkdown} from 'mdast-util-from-markdown';
import {mdxjs} from 'micromark-extension-mdxjs';
import {mdxFromMarkdown} from 'mdast-util-mdx';

function el(name, children, attributes = []) {
  return {type: 'mdxJsxFlowElement', name, attributes, children};
}

// Position data is irrelevant to rendering and only clutters the AST; drop it so
// generated cells are indistinguishable from hand-authored ones.
function stripPositions(nodes) {
  for (const n of nodes) {
    delete n.position;
    if (Array.isArray(n.attributes)) {
      for (const a of n.attributes) {
        delete a.position;
        if (a.value && typeof a.value === 'object') delete a.value.position;
      }
    }
    if (Array.isArray(n.children)) stripPositions(n.children);
  }
}

// Parse a cell's text as MDX phrasing content (markdown emphasis, inline JSX like
// <Latin/>, plain text) so it renders identically to the same text authored
// directly inside a hand-written <td>. Downstream shorthand-style remark plugins
// then run over the resulting text/strong nodes exactly as they do for authored cells.
function parseCellChildren(text) {
  if (!text) return [];
  const tree = fromMarkdown(text, {
    extensions: [mdxjs()],
    mdastExtensions: [mdxFromMarkdown()],
  });
  const children = [];
  for (const block of tree.children) {
    if (block.type === 'paragraph' && Array.isArray(block.children)) {
      children.push(...block.children);
    } else {
      children.push(block);
    }
  }
  stripPositions(children);
  return children;
}

function cellNode(cell) {
  const attributes = [];
  if (cell.rowSpan > 1) {
    attributes.push({type: 'mdxJsxAttribute', name: 'rowSpan', value: String(cell.rowSpan)});
  }
  if (cell.colSpan > 1) {
    attributes.push({type: 'mdxJsxAttribute', name: 'colSpan', value: String(cell.colSpan)});
  }
  return el(cell.header ? 'th' : 'td', parseCellChildren(cell.text), attributes);
}

function rowNode(row) {
  return el('tr', row.map(cellNode));
}

export function buildTableAst(model) {
  const sections = [];
  if (model.headerRows.length > 0) {
    sections.push(el('thead', model.headerRows.map(rowNode)));
  }
  if (model.bodyRows.length > 0) {
    sections.push(el('tbody', model.bodyRows.map(rowNode)));
  }
  return el('table', sections);
}
