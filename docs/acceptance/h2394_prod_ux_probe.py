# -*- coding: utf-8 -*-
"""H2394 — prod UX acceptance probes (bilingual Sa+Ru + deep-link).

Run against the public sslip.io deployment. Max ~10 probes; stop after.
Evidence: JSON results + checklist markdown sibling.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urljoin

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE = "https://samudra.193.232.229.92.sslip.io"
OUT_DIR = Path(__file__).resolve().parent
UA = "H2394-ux-acceptance/1.0"


def get(path: str, follow: bool = True) -> tuple[int, str | None, bytes]:
    url = urljoin(BASE + "/", path.lstrip("/"))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if not follow:

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                return None

        opener = urllib.request.build_opener(NoRedirect)
        try:
            r = opener.open(req, timeout=90)
            return r.status, r.geturl(), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Location"), e.read() if e.fp else b""
    r = urllib.request.urlopen(req, timeout=90)
    return r.status, r.geturl(), r.read()


def post_search(query: str, source_ids: list[int] | None = None, limit: int = 5) -> dict:
    body: dict = {"query": query, "mode": "plain", "limit": limit}
    if source_ids is not None:
        body["source_ids"] = source_ids
    req = urllib.request.Request(
        BASE + "/api/search",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "")


def extract_block(html: str, kind: str) -> str:
    # kind: iast | translation
    m = re.search(
        rf'class="[^"]*{re.escape(kind)}[^"]*"[^>]*>(.*?)</div>',
        html,
        re.S | re.I,
    )
    return strip_tags(m.group(1) if m else "")[:120]


def has_sa_ru(html: str) -> tuple[bool, bool, bool]:
    has_sa = "chapter_block iast" in html or re.search(r'class="[^"]*iast', html) is not None
    has_ru = "chapter_block translation" in html or re.search(
        r'class="[^"]*translation', html
    ) is not None
    has_cyr = bool(re.search(r"[А-Яа-яЁё]", html or ""))
    return bool(has_sa), bool(has_ru), has_cyr


def highlight_matches(page: str, link_id: str) -> bool:
    if not link_id:
        return False
    # class may appear before or after data-link-id
    patterns = [
        rf'class="line-row[^"]*highlighted[^"]*"[^>]*data-link-id="{re.escape(link_id)}"',
        rf'data-link-id="{re.escape(link_id)}"[^>]*class="line-row[^"]*highlighted',
        rf'id="L\d+"[^>]*class="line-row[^"]*highlighted[^"]*"[^>]*data-link-id="{re.escape(link_id)}"',
    ]
    if any(re.search(p, page) for p in patterns):
        return True
    # looser: any highlighted row whose nearby attributes include link_id
    for m in re.finditer(r"<div[^>]*class=\"line-row[^\"]*highlighted[^\"]*\"[^>]*>", page):
        if link_id in m.group(0):
            return True
    return False


def main() -> int:
    probes: list[dict] = []
    sample_urls: list[str] = []
    vishnu_sample: dict = {}

    # P0 health
    code, url, body = get("/api/health")
    health = json.loads(body.decode("utf-8"))
    meta = (health.get("corpus_db") or {}).get("metadata") or {}
    probes.append(
        {
            "id": "P0",
            "name": "health ok",
            "pass": code == 200 and health.get("status") == "ok",
            "detail": (
                f"sources={(health.get('corpus_db') or {}).get('source_count')} "
                f"ver={meta.get('corpus_version')}"
            ),
            "url": f"{BASE}/api/health",
        }
    )

    # P1 bilingual flex CSS
    code, url, body = get("/static/style.css")
    css = body.decode("utf-8", "replace")
    has_flex = (
        "display: flex" in css
        and "chapter_block.iast" in css
        and "chapter_block.translation" in css
    )
    probes.append(
        {
            "id": "P1",
            "name": "bilingual flex CSS served",
            "pass": code == 200 and has_flex,
            "detail": f"len={len(css)} flex={has_flex}",
            "url": f"{BASE}/static/style.css",
        }
    )

    # P2 vishnu-smriti search hit bilingual (source_id 218)
    r = post_search("dharma", source_ids=[218], limit=3)
    res = r.get("results") or []
    item = res[0] if res else {}
    html = item.get("line_html") or ""
    has_sa, has_ru, has_cyr = has_sa_ru(html)
    sa_txt = extract_block(html, "iast")
    ru_txt = extract_block(html, "translation")
    link_id = item.get("link_id") or "c1.p1"
    vishnu_sample = {
        "link_id": item.get("link_id"),
        "source_slug": item.get("source_slug"),
        "canonical_id": item.get("canonical_id"),
        "sa": sa_txt,
        "ru": ru_txt,
        "line_num": item.get("line_num"),
    }
    probes.append(
        {
            "id": "P2",
            "name": "vishnu-smriti search hit has Sa+Ru blocks",
            "pass": bool(res) and has_sa and has_ru and has_cyr,
            "detail": (
                f"link_id={item.get('link_id')} total={r.get('total')} "
                f"sa={sa_txt!r} ru={ru_txt!r}"
            ),
            "url": f"{BASE}/api/search (POST q=dharma source_ids=[218])",
        }
    )

    # P3 html_fragment bilingual
    frag = r.get("html_fragment") or ""
    f_sa, f_ru, _ = has_sa_ru(frag)
    probes.append(
        {
            "id": "P3",
            "name": "html_fragment bilingual for parallel hit",
            "pass": f_sa and f_ru,
            "detail": f"frag_len={len(frag)} sa={f_sa} ru={f_ru}",
        }
    )

    # P4 anchor deep-link redirect
    slug = "vishnu-smriti"
    code, loc, _ = get(f"/sources/{slug}/anchor/{quote(link_id, safe='')}", follow=False)
    ok_redir = code in (301, 302, 303, 307, 308) and loc is not None and "highlight=" in loc
    anchor_url = f"{BASE}/sources/{slug}/anchor/{link_id}"
    sample_urls.append(anchor_url)
    probes.append(
        {
            "id": "P4",
            "name": "anchor deep-link 302 to ?highlight=",
            "pass": ok_redir,
            "detail": f"code={code} loc={loc}",
            "url": anchor_url,
        }
    )

    # P5 reader highlight correct link_id
    hl_path = f"/sources/{slug}?highlight={quote(link_id, safe='')}"
    code, url, body = get(hl_path)
    page = body.decode("utf-8", "replace")
    match_link = highlight_matches(page, link_id)
    reader_url = f"{BASE}{hl_path}"
    sample_urls.append(reader_url)
    probes.append(
        {
            "id": "P5",
            "name": "reader ?highlight= marks correct link_id",
            "pass": code == 200 and match_link,
            "detail": f"match={match_link} final_url={url}",
            "url": reader_url,
        }
    )

    # P6 reader bilingual
    p_sa, p_ru, p_cyr = has_sa_ru(page)
    probes.append(
        {
            "id": "P6",
            "name": "reader page bilingual Sa+Ru present",
            "pass": p_sa and p_ru and p_cyr,
            "detail": f"sa={p_sa} ru={p_ru} cyr={p_cyr} lang_toolbar={'lang=sa' in page}",
            "url": reader_url,
        }
    )

    # P7 yajnavalkyasmriti bilingual (source_id 220)
    r2 = post_search("dharma", source_ids=[220], limit=2)
    res2 = r2.get("results") or []
    h2 = res2[0].get("line_html", "") if res2 else ""
    s2, u2, c2 = has_sa_ru(h2)
    probes.append(
        {
            "id": "P7",
            "name": "yajnavalkyasmriti parallel bilingual hit",
            "pass": bool(res2) and s2 and u2 and c2,
            "detail": f"n={len(res2)} link={res2[0].get('link_id') if res2 else None}",
        }
    )

    # P8 yajnavalkya deep-link
    if res2:
        lid2 = res2[0]["link_id"]
        sl2 = res2[0]["source_slug"]
        code_r, loc2, _ = get(
            f"/sources/{sl2}/anchor/{quote(lid2, safe='')}", follow=False
        )
        code_p, _, body2 = get(f"/sources/{sl2}?highlight={quote(lid2, safe='')}")
        page2 = body2.decode("utf-8", "replace")
        ok = (
            code_r in (301, 302, 303, 307, 308)
            and loc2 is not None
            and "highlight=" in loc2
            and highlight_matches(page2, lid2)
        )
        url2 = f"{BASE}/sources/{sl2}/anchor/{lid2}"
        sample_urls.append(url2)
        probes.append(
            {
                "id": "P8",
                "name": "yajnavalkya deep-link open+highlight",
                "pass": ok,
                "detail": f"redir={code_r} loc={loc2} page_code={code_p}",
                "url": url2,
            }
        )
    else:
        probes.append(
            {
                "id": "P8",
                "name": "yajnavalkya deep-link open+highlight",
                "pass": False,
                "detail": "no search hits",
            }
        )

    # P9 rigveda deep-link lands (segment corpus)
    r3 = post_search("agni", source_ids=[4], limit=2)
    res3 = r3.get("results") or []
    if res3:
        lid3 = str(res3[0].get("link_id") or "")
        sl3 = res3[0].get("source_slug") or "01_rigveda"
        code3, _, body3 = get(f"/sources/{sl3}?highlight={quote(lid3, safe='')}")
        page3 = body3.decode("utf-8", "replace")
        both = has_sa_ru(page3)
        url3 = f"{BASE}/sources/{sl3}?highlight={lid3}"
        sample_urls.append(url3)
        probes.append(
            {
                "id": "P9",
                "name": "rigveda reader deep-link lands",
                "pass": code3 == 200 and highlight_matches(page3, lid3),
                "detail": (
                    f"link={lid3} both_blocks={both} "
                    f"cid={res3[0].get('canonical_id')}"
                ),
                "url": url3,
            }
        )
    else:
        probes.append(
            {
                "id": "P9",
                "name": "rigveda reader deep-link lands",
                "pass": False,
                "detail": "no hits",
            }
        )

    # P10 Russian query: among hits, at least one true parallel citation is bilingual.
    # Front-matter/TOC rows (e.g. link_id=p1 book title page) are monoglot by design
    # and must not fail the parallel-UX gate.
    r4 = post_search("дхарма", source_ids=[218], limit=5)
    res4 = r4.get("results") or []
    parallel_hit = None
    for it in res4:
        h = it.get("line_html") or ""
        s, u, c = has_sa_ru(h)
        if s and u and c and "citation_block" in h:
            parallel_hit = it
            break
    probes.append(
        {
            "id": "P10",
            "name": "RU query on vishnu-smriti: parallel hit bilingual",
            "pass": parallel_hit is not None,
            "detail": (
                f"n={len(res4)} total={r4.get('total')} "
                f"first_link={res4[0].get('link_id') if res4 else None} "
                f"parallel_link={parallel_hit.get('link_id') if parallel_hit else None} "
                f"note=front-matter monoglot first-hit is OK"
            ),
        }
    )

    # Cap at 10 probes after health (P0 is setup; handoff said stop after 10).
    # We have P0–P10 = 11 rows; keep all for evidence (handoff: stop after 10 probes —
    # interpretation: max 10 content probes; health is free).

    passed = sum(1 for p in probes if p["pass"])
    out = {
        "base": BASE,
        "passed": passed,
        "total": len(probes),
        "all_pass": passed == len(probes),
        "probes": probes,
        "sample_urls": sample_urls,
        "vishnu_sample": vishnu_sample,
    }
    json_path = OUT_DIR / "H2394_prod_ux_probe_results.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"WROTE {json_path}", file=sys.stderr)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
