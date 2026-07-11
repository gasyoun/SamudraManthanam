// Ported verbatim (logic unchanged) from buhler-sanskrit-book's
// src/remark/rstTable.ts. Renders a plain ```rst-table fenced code block —
// NO ':::' directive wrapper — into a real MDX <table> with true rowSpan/
// colSpan, by parsing Pandoc/RST grid-table syntax directly in JS (no Pandoc
// dependency at Docusaurus build time). Supersedes the earlier Pandoc-shell-out
// ':::table' directive design (see git history) once this superior prior-art
// implementation was found in buhler-sanskrit-book.
import {visit} from 'unist-util-visit';
import {parseRstGridTable} from './rstTableParser.mjs';
import {buildTableAst} from './rstTableAst.mjs';

export default function remarkRstTable() {
  return (tree) => {
    visit(tree, 'code', (node, index, parent) => {
      if (node.lang !== 'rst-table') return;
      if (!parent || typeof index !== 'number') return;
      const model = parseRstGridTable(node.value ?? '');
      parent.children[index] = buildTableAst(model);
    });
  };
}
