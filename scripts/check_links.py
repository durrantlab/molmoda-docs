#!/usr/bin/env python
"""Spider a running MolModa docs site and report broken links.

Crawls every page reachable from the start URL (same-host only) and
checks every outbound reference it finds:

  - `<a href>` — followed for further crawling when same-host, otherwise
    status-checked. Fragments are validated against target page IDs.
  - `<img src>`, `<img srcset>`, `<source src>`, `<source srcset>` —
    status-checked as assets.
  - `<link href>` (stylesheets, favicons, etc.) and `<script src>` —
    status-checked as assets.

Links whose host contains "molmoda.org" are skipped entirely.

Usage:
    python scripts/check_links.py [START_URL]

START_URL defaults to http://127.0.0.1:3000/. Each URL is printed with
its status as it's checked; a grouped summary of broken links is printed
at the end. Exits non-zero if any broken links are found.
"""
from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests

DEFAULT_START_URL = "http://127.0.0.1:3000/"

# Timeout for any single HTTP request. Local server should be instant;
# external sites get a bit more slack but not enough to stall the run.
INTERNAL_TIMEOUT = 10
EXTERNAL_TIMEOUT = 15

# Identify ourselves so sites that block default `requests` UA (some
# CDNs, Cloudflare-fronted docs) are more likely to respond.
USER_AGENT = (
    "Mozilla/5.0 (compatible; MolModaDocsLinkChecker/1.0; "
    "+https://durrantlab.pitt.edu/molmoda/)"
)

# Hosts skipped entirely. Substring match against the netloc.
SKIP_HOST_SUBSTRINGS = ("molmoda.org",)

# Extensions we treat as non-HTML and therefore don't parse for further
# links or fragment IDs. We still status-check them.
NON_HTML_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".zip", ".gz", ".tgz", ".tar",
    ".mp4", ".mp3", ".wav", ".webm",
    ".css", ".js", ".json", ".xml",
    ".smiles", ".sdf", ".mol2", ".pdb", ".molmoda",
)

# `rel` values on `<link>` elements that describe *connection hints*
# rather than fetchable resources. `preconnect` and `dns-prefetch`
# point at an origin (no path) and intentionally 404 if requested;
# checking them produces noise. Other hint-like rels (`prefetch`,
# `preload`, `modulepreload`) DO point at real assets and are left in.
LINK_REL_SKIP = {"preconnect", "dns-prefetch"}

# HTTP statuses that mean "the server saw the request and refused to
# serve us," rather than "this resource does not exist." Common cause
# is publisher / CDN anti-bot rules (ACS at pubs.acs.org behind DOI
# redirects is the canonical example). A human in a browser reaches
# these URLs fine, so we surface them as inconclusive instead of
# broken — they don't fail the run and don't pollute the broken-link
# report.
INCONCLUSIVE_STATUSES = frozenset({401, 403, 429})

@dataclass
class LinkRef:
    """One occurrence of a link, used for reporting context."""

    source_page: str
    raw_href: str


@dataclass
class PageInfo:
    """Parsed result for one HTML page we fetched.

    `links` is everything we want to crawl/follow further (i.e., `<a>`
    targets). `assets` is everything we only status-check (images,
    stylesheets, scripts, favicons). Splitting them keeps the crawl
    loop from accidentally trying to parse a CSS or JS file as HTML and
    keeps fragment validation honest, since fragments only make sense
    on anchor targets.
    """

    links: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    ids: set[str] = field(default_factory=set)


def log_ok(url: str, detail: str = "") -> None:
    """Print a one-line OK record for a checked URL.

    Kept as a helper so the live log format stays consistent across
    internal fetches, external checks, and fragment validations.
    """
    suffix = f" ({detail})" if detail else ""
    print(f"  OK     {url}{suffix}")

def log_inconclusive(url: str, detail: str) -> None:
    """Print a one-line inconclusive record (auth/anti-bot block).

    Distinct from `log_bad` so the live stream visually separates
    "server refused us" from "resource is missing."
    """
    print(f"  MAYBE  {url} -- {detail}")

def log_bad(url: str, detail: str) -> None:
    """Print a one-line failure record for a checked URL."""
    print(f"  BROKEN {url} -- {detail}")


def log_skip(url: str, detail: str) -> None:
    """Print a one-line skip record (e.g. molmoda.org host)."""
    print(f"  SKIP   {url} ({detail})")


def _parse_srcset(value: str) -> list[str]:
    """Extract URLs from a `srcset` attribute.

    `srcset` is a comma-separated list of `url descriptor` pairs
    (e.g. `foo.png 1x, bar.png 2x`). We only need the URL portion to
    status-check it. Commas inside URLs are not standard here, so a
    simple split is sufficient for HTML produced by mkdocs-material.
    """
    urls: list[str] = []
    for candidate in value.split(","):
        token = candidate.strip().split()
        if token:
            urls.append(token[0])
    return urls


class _PageParser(HTMLParser):
    """Collect anchor links, asset references, and in-page IDs.

    Anchor links go into `info.links` so the crawler can follow them.
    Every other reference (images, stylesheets, scripts, favicons,
    `<source>` elements inside `<picture>`/`<video>`) goes into
    `info.assets` for status-only checking. IDs come from both `id=`
    attributes on any element and legacy `<a name>` targets.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.info = PageInfo()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs if v is not None}
        # Any element can be a fragment target via its id.
        elem_id = attr_map.get("id")
        if elem_id:
            self.info.ids.add(elem_id)

        if tag == "a":
            # `<a name="...">` is the legacy fragment-target form and
            # MathJax/older Markdown renderers still emit it.
            name = attr_map.get("name")
            if name:
                self.info.ids.add(name)
            href = attr_map.get("href")
            if href:
                self.info.links.append(href)
            return

        if tag == "img":
            src = attr_map.get("src")
            if src:
                self.info.assets.append(src)
            srcset = attr_map.get("srcset")
            if srcset:
                self.info.assets.extend(_parse_srcset(srcset))
            return

        if tag == "source":
            # Used inside `<picture>` and `<video>`/`<audio>`. Both
            # `src` and `srcset` show up in the wild.
            src = attr_map.get("src")
            if src:
                self.info.assets.append(src)
            srcset = attr_map.get("srcset")
            if srcset:
                self.info.assets.extend(_parse_srcset(srcset))
            return

        if tag == "link":
            # Connection hints (`preconnect`, `dns-prefetch`) point at
            # origins, not assets, so they 404 when fetched. Skip
            # them; other rel values are real resources.
            rel = (attr_map.get("rel") or "").lower().split()
            if any(r in LINK_REL_SKIP for r in rel):
                return
            href = attr_map.get("href")
            if href:
                self.info.assets.append(href)
            return

        if tag == "script":
            src = attr_map.get("src")
            if src:
                self.info.assets.append(src)
            return


def should_skip(url: str) -> bool:
    """True for hosts we've been told to ignore (molmoda.org)."""
    host = urlparse(url).netloc.lower()
    return any(s in host for s in SKIP_HOST_SUBSTRINGS)


def is_http_url(url: str) -> bool:
    """Filter out mailto:, javascript:, tel:, data:, etc."""
    return urlparse(url).scheme in ("http", "https")


def looks_like_html(url: str) -> bool:
    """Heuristic: treat anything without a non-HTML suffix as HTML.

    Trailing slashes and bare paths (mkdocs pretty URLs) count as HTML.
    """
    path = urlparse(url).path.lower()
    return not path.endswith(NON_HTML_SUFFIXES)


def normalize(url: str) -> str:
    """Strip fragment for use as a fetch/cache key.

    Fragments don't change what the server returns, so two links that
    differ only by `#section` share one fetch.
    """
    defragged, _ = urldefrag(url)
    return defragged


def parse_html(body: str) -> PageInfo:
    """Run the HTML parser and return collected links + ids."""
    parser = _PageParser()
    try:
        parser.feed(body)
    except Exception:
        # Malformed HTML shouldn't kill the whole run; return what we got.
        pass
    return parser.info


def fetch_internal(session: requests.Session, url: str) -> tuple[int | None, str | None, str | None]:
    """GET an internal URL.

    Returns (status_code, body_or_None, error_or_None). Body is None for
    non-HTML responses or non-2xx replies.
    """
    try:
        resp = session.get(url, timeout=INTERNAL_TIMEOUT, allow_redirects=True)
    except requests.RequestException as err:
        return None, None, str(err)
    body: str | None = None
    ctype = resp.headers.get("Content-Type", "").lower()
    if resp.ok and "html" in ctype:
        # `resp.text` uses the declared encoding; mkdocs serves utf-8.
        body = resp.text
    return resp.status_code, body, None


def fetch_external(session: requests.Session, url: str) -> tuple[int | None, str | None, str | None]:
    """HEAD an external URL, falling back to GET on 4xx/405.

    Some servers (notably GitHub raw, a few CDNs) reject HEAD with 403
    or 405 even when GET works fine, so we retry once with GET. Body is
    returned only when we did a GET *and* the response is HTML, so
    fragment checks can run against external pages too.
    """
    try:
        resp = session.head(
            url, timeout=EXTERNAL_TIMEOUT, allow_redirects=True
        )
    except requests.RequestException as err:
        # Network-level failure; try GET before giving up — some hosts
        # drop HEAD at the firewall.
        try:
            resp = session.get(
                url, timeout=EXTERNAL_TIMEOUT, allow_redirects=True, stream=True
            )
        except requests.RequestException as err2:
            return None, None, f"{err} / {err2}"

    # If HEAD looks unhappy, retry with GET.
    if resp.status_code in (403, 405, 501) or resp.status_code >= 400:
        try:
            resp = session.get(
                url, timeout=EXTERNAL_TIMEOUT, allow_redirects=True
            )
        except requests.RequestException as err:
            return None, None, str(err)

    body: str | None = None
    ctype = resp.headers.get("Content-Type", "").lower()
    if resp.ok and "html" in ctype and resp.request.method == "GET":
        body = resp.text
    return resp.status_code, body, None


def _check_asset_url(
    session: requests.Session,
    absolute: str,
    absolute_norm: str,
    ref: LinkRef,
    start_host: str,
    nonhtml_status: dict[str, tuple[int | None, str | None]],
    external_links: dict[str, list[LinkRef]],
    fetch_errors: list[tuple[LinkRef, str]],
) -> None:
    """Status-check an asset reference (img/link/script/source).

    Same-host assets are fetched directly; cross-host assets are
    deferred to the external-link pass so HEAD/GET fallback logic and
    de-duplication are reused. Same-host caching lives in
    `nonhtml_status` so an image referenced from 50 pages only hits
    the server once.
    """
    target_host = urlparse(absolute_norm).netloc
    if target_host == start_host:
        if absolute_norm in nonhtml_status:
            status, err = nonhtml_status[absolute_norm]
        else:
            status, _, err = fetch_internal(session, absolute_norm)
            nonhtml_status[absolute_norm] = (status, err)
            if err is not None or (status is not None and status >= 400):
                log_bad(absolute_norm, err or f"HTTP {status}")
            else:
                log_ok(absolute_norm, f"HTTP {status}, asset")
        if err is not None or (status is not None and status >= 400):
            fetch_errors.append((ref, err or f"HTTP {status}"))
    else:
        external_links.setdefault(absolute_norm, []).append(ref)


def gather_internal_pages(
    session: requests.Session, start_url: str
) -> tuple[dict[str, PageInfo], dict[str, list[LinkRef]], list[tuple[LinkRef, str]], str]:
    """Crawl the site and return per-page info + all outbound links.

    Returns:
        pages: map of normalized internal URL -> PageInfo.
        external_links: map of normalized external URL -> list of
            LinkRef occurrences (covers both anchor links and assets
            hosted off-site).
        fetch_errors: list of (LinkRef, message) for internal URLs
            (pages or assets) that failed to load.
        effective_start_host: the host derived from the *final* URL
            after redirects of the initial fetch.
    """
    # Resolve any redirect on the start URL up front. Without this, a
    # `127.0.0.1` -> `localhost` (or http -> https) redirect would cause
    # every subsequent link to be classified as external and only
    # HEAD-checked, which both misses fragment validation and looks
    # suspiciously fast.
    try:
        bootstrap = session.get(start_url, timeout=INTERNAL_TIMEOUT, allow_redirects=True)
        effective_start_url = bootstrap.url
    except requests.RequestException:
        effective_start_url = start_url
    start_host = urlparse(effective_start_url).netloc

    pages: dict[str, PageInfo] = {}
    external_links: dict[str, list[LinkRef]] = {}
    fetch_errors: list[tuple[LinkRef, str]] = []

    # Track internal URLs we've already fetched (or queued) so we don't
    # re-fetch. Key is normalized (fragment-stripped) URL.
    seen: set[str] = set()
    # Also track *non-HTML* internal URLs we've status-checked, so
    # images/PDFs/etc. linked from many pages only hit the server once.
    nonhtml_status: dict[str, tuple[int | None, str | None]] = {}

    queue: deque[tuple[str, LinkRef]] = deque()
    start_norm = normalize(effective_start_url)
    queue.append((start_norm, LinkRef(source_page="<start>", raw_href=effective_start_url)))
    seen.add(start_norm)

    print("\n=== Crawling internal pages ===")
    while queue:
        url, ref = queue.popleft()

        # Non-HTML internal asset: just status-check it.
        if not looks_like_html(url):
            if url not in nonhtml_status:
                status, _, err = fetch_internal(session, url)
                nonhtml_status[url] = (status, err)
                if err is not None or (status is not None and status >= 400):
                    log_bad(url, err or f"HTTP {status}")
                else:
                    log_ok(url, f"HTTP {status}, asset")
            status, err = nonhtml_status[url]
            if err is not None or (status is not None and status >= 400):
                fetch_errors.append((ref, err or f"HTTP {status}"))
            continue

        status, body, err = fetch_internal(session, url)
        if err is not None:
            log_bad(url, err)
            fetch_errors.append((ref, err))
            continue
        if status is None or status >= 400:
            log_bad(url, f"HTTP {status}")
            fetch_errors.append((ref, f"HTTP {status}"))
            continue
        if body is None:
            # 2xx but not HTML — accept and move on without parsing.
            log_ok(url, f"HTTP {status}, non-HTML")
            continue

        info = parse_html(body)
        pages[url] = info
        log_ok(
            url,
            f"HTTP {status}, {len(info.links)} link(s), {len(info.assets)} asset(s)",
        )

        # Anchor links: follow if internal, otherwise defer to external pass.
        for raw in info.links:
            absolute = urljoin(url, raw)
            if not is_http_url(absolute):
                continue
            if should_skip(absolute):
                continue
            absolute_norm = normalize(absolute)
            target_host = urlparse(absolute_norm).netloc
            occurrence = LinkRef(source_page=url, raw_href=absolute)

            if target_host == start_host:
                if absolute_norm not in seen:
                    seen.add(absolute_norm)
                    queue.append((absolute_norm, occurrence))
            else:
                external_links.setdefault(absolute_norm, []).append(occurrence)

        # Assets: status-checked only, never crawled. Same-host assets
        # are fetched inline (cached in nonhtml_status); cross-host
        # ones go through the external pass for HEAD/GET fallback.
        for raw in info.assets:
            absolute = urljoin(url, raw)
            if not is_http_url(absolute):
                continue
            if should_skip(absolute):
                continue
            absolute_norm = normalize(absolute)
            occurrence = LinkRef(source_page=url, raw_href=absolute)
            _check_asset_url(
                session,
                absolute,
                absolute_norm,
                occurrence,
                start_host,
                nonhtml_status,
                external_links,
                fetch_errors,
            )

    return pages, external_links, fetch_errors, start_host


def check_fragments(
    pages: dict[str, PageInfo], external_bodies: dict[str, PageInfo]
) -> list[tuple[LinkRef, str]]:
    """Verify that every `#fragment` resolves to an id on its target.

    Logs each fragment check live; returns the list of failures.
    """
    problems: list[tuple[LinkRef, str]] = []
    checked: set[tuple[str, str]] = set()

    print("\n=== Validating URL fragments ===")

    def check_against(target_norm: str, fragment: str, ref: LinkRef, info: PageInfo) -> None:
        key = (target_norm, fragment)
        full = f"{target_norm}#{fragment}"
        if key in checked:
            return
        checked.add(key)
        if fragment in info.ids:
            log_ok(full, "fragment present")
            return
        log_bad(full, f"fragment #{fragment} not found")
        problems.append((ref, f"fragment #{fragment} not found on {target_norm}"))

    any_checked = False
    for source, info in pages.items():
        for raw in info.links:
            absolute = urljoin(source, raw)
            if not is_http_url(absolute):
                continue
            if should_skip(absolute):
                continue
            _, fragment = urldefrag(absolute)
            if not fragment:
                continue
            target_norm = normalize(absolute)
            ref = LinkRef(source_page=source, raw_href=absolute)
            if target_norm in pages:
                any_checked = True
                check_against(target_norm, fragment, ref, pages[target_norm])
            elif target_norm in external_bodies:
                any_checked = True
                check_against(target_norm, fragment, ref, external_bodies[target_norm])
            # else: target's HTML wasn't fetched; can't validate the
            # fragment. Silently skip rather than logging noise.

    if not any_checked:
        print("  (no fragments to validate)")
    return problems


def check_external(
    session: requests.Session, external_links: dict[str, list[LinkRef]]
) -> tuple[
    list[tuple[LinkRef, str]],
    list[tuple[LinkRef, str]],
    dict[str, PageInfo],
]:
    """Status-check each external URL once; collect HTML bodies for fragments.

    Returns three things:
      - hard failures (4xx other than auth/anti-bot, 5xx, network errors)
      - inconclusive results (401/403/429 — server refused us, not
        necessarily a dead link)
      - parsed bodies for any external page that returned HTML, so the
        fragment checker can validate `#anchor` targets on them
    """
    problems: list[tuple[LinkRef, str]] = []
    inconclusive: list[tuple[LinkRef, str]] = []
    bodies: dict[str, PageInfo] = {}

    print("\n=== Checking external links ===")
    if not external_links:
        print("  (no external links to check)")

    for url in sorted(external_links):
        refs = external_links[url]
        status, body, err = fetch_external(session, url)
        if err is not None:
            log_bad(url, err)
            for ref in refs:
                problems.append((ref, err))
            continue
        if status is None:
            log_bad(url, "no status")
            for ref in refs:
                problems.append((ref, "no status"))
            continue
        if status in INCONCLUSIVE_STATUSES:
            msg = f"HTTP {status} (server refused; likely anti-bot)"
            log_inconclusive(url, msg)
            for ref in refs:
                inconclusive.append((ref, msg))
            continue
        if status >= 400:
            msg = f"HTTP {status}"
            log_bad(url, msg)
            for ref in refs:
                problems.append((ref, msg))
            continue
        log_ok(url, f"HTTP {status}")
        if body is not None:
            bodies[url] = parse_html(body)

    return problems, inconclusive, bodies


def report(
    broken: Iterable[tuple[LinkRef, str]],
    inconclusive: Iterable[tuple[LinkRef, str]],
) -> int:
    """Print the broken-link report plus an inconclusive section.

    Inconclusive entries are listed so the user can spot-check, but
    they do not affect the exit code. Returns 1 only if there are real
    broken links.
    """
    items = list(broken)
    incon = list(inconclusive)

    print("\n=== Broken-link report ===")
    if not items:
        print("No broken links found.")
    else:
        by_source: dict[str, list[tuple[str, str]]] = {}
        for ref, msg in items:
            by_source.setdefault(ref.source_page, []).append((ref.raw_href, msg))
        total = 0
        for source in sorted(by_source):
            print(f"\n{source}")
            for href, msg in sorted(by_source[source]):
                print(f"  - {href}")
                print(f"      {msg}")
                total += 1
        print(f"\n{total} broken link(s) found.")

    if incon:
        # Surfaced but not fatal: a 403 from ACS on a DOI redirect is
        # the server refusing automated traffic, not a dead link.
        print("\n=== Inconclusive (server refused; verify manually) ===")
        by_source_i: dict[str, list[tuple[str, str]]] = {}
        for ref, msg in incon:
            by_source_i.setdefault(ref.source_page, []).append((ref.raw_href, msg))
        total_i = 0
        for source in sorted(by_source_i):
            print(f"\n{source}")
            for href, msg in sorted(by_source_i[source]):
                print(f"  - {href}")
                print(f"      {msg}")
                total_i += 1
        print(f"\n{total_i} inconclusive link(s).")

    return 1 if items else 0


def main(argv: list[str]) -> int:
    """Entry point: crawl, check, report, exit."""
    start_url = argv[1] if len(argv) > 1 else DEFAULT_START_URL
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    print(f"Starting at {start_url}")
    pages, external_links, internal_errors, effective_host = gather_internal_pages(
        session, start_url
    )
    print(
        f"\nVisited {len(pages)} HTML page(s) on host {effective_host}; "
        f"found {len(external_links)} external URL(s) to check."
    )

    external_errors, external_inconclusive, external_bodies = check_external(
        session, external_links
    )
    fragment_errors = check_fragments(pages, external_bodies)

    return report(
        internal_errors + external_errors + fragment_errors,
        external_inconclusive,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
