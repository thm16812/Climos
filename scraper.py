"""
Kentucky County Emergency Operations Plans (EOP) Scraper
=========================================================
Collects publicly available EOPs from all 120 Kentucky counties.
EOPs are public records per KRS 39A and 61.870-61.884 (Open Records Act).

Strategy:
  1. Download pre-confirmed direct PDF / document links
  2. For counties with known EOP index pages, crawl those pages for PDFs
  3. For remaining counties, record status and reference URLs for manual retrieval
     or Open Records Act requests
"""

import os
import re
import json
import time
import hashlib
import logging
import datetime
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("data/eops")
META_FILE  = Path("data/metadata.json")
LOG_FILE   = Path("data/scraper.log")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; KY-EOP-PublicRecords-Collector/1.0; "
        "Public Records Research; +https://github.com/thm16812/Climos)"
    )
}
REQUEST_TIMEOUT = 15
DELAY = 1.0   # seconds between requests

# ---------------------------------------------------------------------------
# Pre-verified EOP sources
# Format: county -> list of {url, title, type}
# type: "pdf"   = direct PDF link (download)
#       "page"  = HTML index page (crawl for embedded PDF links)
#       "ref"   = reference only (no public PDF found; note for Open Records)
# ---------------------------------------------------------------------------
KNOWN_SOURCES = {

    # ── STATE-LEVEL PLANS (for reference) ───────────────────────────────────
    "_STATE_KY": [
        {"url": "https://kyem.ky.gov/sitecontacts/Documents/State%20EOP.pdf",
         "title": "Kentucky State Emergency Operations Plan (KYEM)",
         "type": "pdf"},
        {"url": "https://kyem.ky.gov/Documents/Updated%20Kentucky%20Emergency%20Operations%20Plan.pdf",
         "title": "Updated Kentucky Emergency Operations Plan (KYEM)",
         "type": "pdf"},
        {"url": "https://eec.ky.gov/Energy/Programs/Documents/Emergency%20Operation%20Plan.pdf",
         "title": "Kentucky EOP – Energy & Environment Cabinet",
         "type": "pdf"},
    ],

    # ── COUNTY PLANS ────────────────────────────────────────────────────────
    "Campbell": [
        {"url": "https://campbellcountyky.gov/egov/documents/1735852403_1093.pdf",
         "title": "Campbell County EOP – Search & Rescue Plan", "type": "pdf"},
        {"url": "https://campbellcountyky.gov/egov/documents/1759437436_67386.pdf",
         "title": "Campbell County ESF-13 Public Safety & Security Annex", "type": "pdf"},
        {"url": "https://campbellcountyky.gov/division/blocks.php?structureid=73",
         "title": "Campbell County EOP Index Page", "type": "page"},
    ],

    "Fayette": [
        {"url": "https://www.bereadylexington.com/wp-content/uploads/2021/06/Basic-Plan.pdf",
         "title": "Lexington-Fayette County EOP – Basic Plan (2021)", "type": "pdf"},
        {"url": "https://www.bereadylexington.com/emergency-operations-plan/",
         "title": "Lexington-Fayette County EOP Index", "type": "page"},
    ],

    "Hardin": [
        {"url": "https://www.hardincountyky.gov/DocumentCenter/View/2862/Executive-Order-2025-001-Emergency-Mgmt-Operations-Plan",
         "title": "Hardin County EOP Executive Order 2025-001", "type": "pdf"},
    ],

    "Jefferson": [
        {"url": "https://louisvilleky.gov/sites/default/files/2025-10/2025%20Louisville%20Jefferson%20CO%20EOP%20FINAL%2004-07-2025.pdf",
         "title": "Louisville/Jefferson County Metro Government EOP 2025", "type": "pdf"},
    ],

    "Kenton": [
        {"url": "https://www.kentoncounty.org/DocumentCenter/View/298/Kenton-County-Emergency-Operations-Plan-EOP-PDF",
         "title": "Kenton County EOP – Basic Plan", "type": "pdf"},
        {"url": "https://edgewoodky.gov/wp-content/uploads/2023/07/2022-KCEOP-Full-Version-059-02-2023.pdf",
         "title": "Kenton County EOP Full Version 2022 (via Edgewood KY)", "type": "pdf"},
        {"url": "https://www.kentoncounty.org/DocumentCenter/View/2804/1A-Incident-Management-System-Plan-PDF",
         "title": "Kenton County EOP – Incident Management System Plan", "type": "pdf"},
        {"url": "https://kentoncounty.org/DocumentCenter/View/297/Emergency-Support-Functions-Transportation-PDF",
         "title": "Kenton County ESF-1 Transportation", "type": "pdf"},
        {"url": "https://www.kentoncounty.org/DocumentCenter/View/294/Emergency-Support-Functions-Public-Works-Infrastructure-Management-PDF",
         "title": "Kenton County ESF-3 Public Works & Infrastructure", "type": "pdf"},
        {"url": "https://www.kentoncounty.org/DocumentCenter/View/303/Emergency-Support-Functions-Hazardous-Materials-PDF",
         "title": "Kenton County ESF Hazardous Materials", "type": "pdf"},
        {"url": "https://kentoncounty.org/DocumentCenter/View/2801/Point-of-Distribution-Plan-PDF",
         "title": "Kenton County EOP – Point of Distribution Plan", "type": "pdf"},
        {"url": "https://kentoncounty.org/DocumentCenter/View/2816/Aircraft-Emergency-Response-Plan-PDF",
         "title": "Kenton County EOP – Aircraft Incident Response Plan", "type": "pdf"},
        {"url": "https://www.kentoncounty.org/DocumentCenter/View/2838/Railroad-Emergency-Response-Plan-PDF",
         "title": "Kenton County EOP – Railroad Incident Response Plan", "type": "pdf"},
        {"url": "https://kentoncounty.org/DocumentCenter/View/2830/Earthquake-Preparedness-Plan-PDF",
         "title": "Kenton County EOP – Earthquake Preparedness Plan", "type": "pdf"},
        {"url": "https://www.kentoncounty.org/210/Kenton-County-Emergency-Operation-Plans",
         "title": "Kenton County EOP Index Page", "type": "page"},
    ],
}

# ---------------------------------------------------------------------------
# All 120 KY Counties with best-known official website
# Counties not in KNOWN_SOURCES will be recorded with reference URLs
# ---------------------------------------------------------------------------
KY_COUNTIES = {
    "Adair":        "https://www.adaircounty.ky.gov",
    "Allen":        "https://www.allencounty.ky.gov",
    "Anderson":     "https://www.andersoncountyky.gov",
    "Ballard":      "https://www.ballardcountyky.gov",
    "Barren":       "https://www.barrencounty.org",
    "Bath":         "https://www.bathcountyky.org",
    "Bell":         "https://www.bellcountyky.gov",
    "Boone":        "https://www.boonecountyky.org",
    "Bourbon":      "https://www.bourboncountyky.gov",
    "Boyd":         "https://www.boydcountyky.org",
    "Boyle":        "https://www.boylecountyky.gov",
    "Bracken":      "https://www.brackencountyky.gov",
    "Breathitt":    "https://www.breathittcountyky.gov",
    "Breckinridge": "https://www.breckinridgecounty.ky.gov",
    "Bullitt":      "https://www.bullittcounty.net",
    "Butler":       "https://www.butlercountyky.gov",
    "Caldwell":     "https://www.caldwellcountyky.gov",
    "Calloway":     "https://www.callowaycountyky.gov",
    "Campbell":     "https://campbellcountyky.gov",
    "Carlisle":     "https://www.carlislecountyky.gov",
    "Carroll":      "https://www.carrollcountyky.gov",
    "Carter":       "https://www.cartercountyky.org",
    "Casey":        "https://www.caseycountyky.gov",
    "Christian":    "https://www.christiancounty.net",
    "Clark":        "https://www.clarkcountyky.gov",
    "Clay":         "https://www.claycountyky.gov",
    "Clinton":      "https://www.clintoncountyky.gov",
    "Crittenden":   "https://www.crittendencountyky.gov",
    "Cumberland":   "https://www.cumberlandcountyky.gov",
    "Daviess":      "https://www.daviesscounty.net",
    "Edmonson":     "https://www.edmonson.ky.gov",
    "Elliott":      "https://www.elliottcountyky.gov",
    "Estill":       "https://www.estillcounty.ky.gov",
    "Fayette":      "https://www.bereadylexington.com",
    "Fleming":      "https://www.flemingcountyky.gov",
    "Floyd":        "https://www.floydcountyky.org",
    "Franklin":     "https://www.franklincountyky.gov",
    "Fulton":       "https://www.fultoncountyky.gov",
    "Gallatin":     "https://www.gallatincountyky.gov",
    "Garrard":      "https://www.garrardcountyky.gov",
    "Grant":        "https://www.grantcountyky.org",
    "Graves":       "https://www.gravescountyky.gov",
    "Grayson":      "https://www.graysoncountyky.gov",
    "Green":        "https://www.greencountyky.gov",
    "Greenup":      "https://www.greenupky.org",
    "Hancock":      "https://www.hancockcountyky.gov",
    "Hardin":       "https://www.hardincountyky.gov",
    "Harlan":       "https://www.harlancounty.ky.gov",
    "Harrison":     "https://www.harrisoncountyky.gov",
    "Hart":         "https://www.hartcountyky.gov",
    "Henderson":    "https://www.hendersoncountyky.org",
    "Henry":        "https://www.henrycountyky.gov",
    "Hickman":      "https://www.hickmancountyky.gov",
    "Hopkins":      "https://www.hopkinscountyky.gov",
    "Jackson":      "https://www.jacksoncountyky.gov",
    "Jefferson":    "https://www.louisvilleky.gov",
    "Jessamine":    "https://www.jessamineco.com",
    "Johnson":      "https://www.johnsoncountyky.gov",
    "Kenton":       "https://www.kentoncounty.org",
    "Knott":        "https://www.knottcountyky.gov",
    "Knox":         "https://www.knoxcountyky.gov",
    "Larue":        "https://www.laruecountyky.gov",
    "Laurel":       "https://www.laurelcountyky.gov",
    "Lawrence":     "https://www.lawrencecountyky.gov",
    "Lee":          "https://www.leecountyky.gov",
    "Leslie":       "https://www.lesliecountyky.gov",
    "Letcher":      "https://www.letchercountyky.gov",
    "Lewis":        "https://www.lewiscountyky.gov",
    "Lincoln":      "https://www.lincolncountyky.gov",
    "Livingston":   "https://www.livingstoncountyky.gov",
    "Logan":        "https://www.logancountyky.gov",
    "Lyon":         "https://www.lyoncountyky.gov",
    "McCracken":    "https://mccrackencountyky.gov",
    "McCreary":     "https://www.mccrearyky.com",
    "McLean":       "https://www.mcleancountyky.gov",
    "Madison":      "https://www.madisoncountyky.us",
    "Magoffin":     "https://www.magoffincountyky.gov",
    "Marion":       "https://www.marioncountyky.org",
    "Marshall":     "https://www.marshallcountyky.gov",
    "Martin":       "https://www.martincountyky.gov",
    "Mason":        "https://www.masoncountyky.gov",
    "Meade":        "https://www.meadecountyky.org",
    "Menifee":      "https://www.menifeecountyky.gov",
    "Mercer":       "https://www.mercercountyky.org",
    "Metcalfe":     "https://www.metcalfecountyky.gov",
    "Monroe":       "https://www.monroecountyky.gov",
    "Montgomery":   "https://www.montgomerycountyky.gov",
    "Morgan":       "https://www.morgancountyky.gov",
    "Muhlenberg":   "https://www.muhlenbergcountyky.gov",
    "Nelson":       "https://www.nelsoncountyky.gov",
    "Nicholas":     "https://www.nicholascountyky.gov",
    "Ohio":         "https://www.ohiocountyky.gov",
    "Oldham":       "https://www.oldhamcountyky.gov",
    "Owen":         "https://www.owencountyky.gov",
    "Owsley":       "https://www.owsleycountyky.gov",
    "Pendleton":    "https://www.pendletoncountyky.gov",
    "Perry":        "https://www.perrycountyky.gov",
    "Pike":         "https://www.pikecountyky.gov",
    "Powell":       "https://www.powellcountyky.gov",
    "Pulaski":      "https://www.pulaskicountyky.gov",
    "Robertson":    "https://www.robertsoncountyky.gov",
    "Rockcastle":   "https://www.rockcastlecounty.org",
    "Rowan":        "https://www.rowancountyky.gov",
    "Russell":      "https://www.russellcountyky.gov",
    "Scott":        "https://www.scottcountyky.gov",
    "Shelby":       "https://www.shelbycountyky.gov",
    "Simpson":      "https://www.simpsoncountyky.gov",
    "Spencer":      "https://www.spencercountyky.gov",
    "Taylor":       "https://www.taylorcountyky.gov",
    "Todd":         "https://www.toddcountyky.gov",
    "Trigg":        "https://www.triggcountyky.gov",
    "Trimble":      "https://www.trimblecountyky.gov",
    "Union":        "https://www.unioncountyky.org",
    "Warren":       "https://www.warrencountyky.gov",
    "Washington":   "https://www.washingtoncountyky.gov",
    "Wayne":        "https://www.waynecountyky.gov",
    "Webster":      "https://www.webstercountyky.gov",
    "Whitley":      "https://www.whitleycounty.ky.gov",
    "Wolfe":        "https://www.wolfecountyky.gov",
    "Woodford":     "https://www.woodfordcountyky.gov",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def safe_get(session, url, stream=False):
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT, stream=stream,
                        allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception as exc:
        log.debug("GET %s -> %s", url, exc)
        return None


def is_pdf_url(url: str) -> bool:
    return url.lower().split("?")[0].endswith(".pdf")


def safe_filename(county: str, url: str, idx: int = 0) -> str:
    ext  = ".pdf" if is_pdf_url(url) else ".html"
    slug = re.sub(r"[^\w]+", "_", county.lower())
    h    = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{slug}_{idx:02d}_{h}{ext}"


def download(session, url: str, dest: Path) -> bool:
    if dest.exists():
        log.info("    Already exists: %s", dest.name)
        return True
    r = safe_get(session, url, stream=True)
    if r is None:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as fh:
        for chunk in r.iter_content(65536):
            fh.write(chunk)
    log.info("    Saved %s (%d bytes)", dest.name, dest.stat().st_size)
    return True


def crawl_page_for_pdfs(session, page_url: str) -> list[dict]:
    """Fetch an HTML page and return list of {url, title} for all PDF links."""
    r = safe_get(session, page_url)
    if r is None:
        return []
    soup = BeautifulSoup(r.text, "lxml")
    results = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        abs_url = urljoin(page_url, href)
        text = a.get_text(" ", strip=True)
        if is_pdf_url(abs_url) or any(kw in (text + abs_url).lower() for kw in
                                       ["eop", "emergency operations", "esf", "annex"]):
            if abs_url.startswith("http"):
                results.append({"url": abs_url, "title": text or abs_url})
    return results


# ---------------------------------------------------------------------------
# Process a single county
# ---------------------------------------------------------------------------
def process_county(session, county: str, county_url: str) -> list[dict]:
    log.info("=== %s County ===", county)
    eop_dir = OUTPUT_DIR / county.replace(" ", "_")
    eop_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    sources = KNOWN_SOURCES.get(county, [])

    if not sources:
        # No confirmed sources — record reference only
        log.info("  No confirmed public EOP found. Recording reference URL.")
        saved.append({
            "county": county,
            "title": None,
            "url": county_url,
            "source_type": "reference",
            "notes": (
                "No publicly indexed EOP PDF found via web search. "
                "Submit Kentucky Open Records Act request to: " + county_url
            ),
            "file": None,
            "downloaded": False,
            "timestamp": _ts(),
        })
        return saved

    # Process each known source
    for idx, src in enumerate(sources):
        url   = src["url"]
        title = src["title"]
        stype = src["type"]

        if stype == "pdf":
            fname = safe_filename(county, url, idx)
            dest  = eop_dir / fname
            ok    = download(session, url, dest)
            saved.append({
                "county": county,
                "title": title,
                "url": url,
                "source_type": "direct_pdf",
                "notes": None,
                "file": str(dest.relative_to(Path("."))) if ok else None,
                "downloaded": ok,
                "timestamp": _ts(),
            })
            time.sleep(DELAY)

        elif stype == "page":
            log.info("  Crawling index page: %s", url)
            sub_links = crawl_page_for_pdfs(session, url)
            log.info("  Found %d sub-links on index page", len(sub_links))
            if sub_links:
                for j, lnk in enumerate(sub_links):
                    fname = safe_filename(county, lnk["url"], idx * 100 + j)
                    dest  = eop_dir / fname
                    ok    = download(session, lnk["url"], dest)
                    saved.append({
                        "county": county,
                        "title": lnk["title"],
                        "url": lnk["url"],
                        "source_type": "crawled_pdf",
                        "notes": f"Found via index page: {url}",
                        "file": str(dest.relative_to(Path("."))) if ok else None,
                        "downloaded": ok,
                        "timestamp": _ts(),
                    })
                    time.sleep(DELAY)
            else:
                saved.append({
                    "county": county,
                    "title": f"EOP Index: {url}",
                    "url": url,
                    "source_type": "page_no_pdfs",
                    "notes": "Index page crawled but no PDF sub-links extracted",
                    "file": None,
                    "downloaded": False,
                    "timestamp": _ts(),
                })
            time.sleep(DELAY)

        elif stype == "ref":
            saved.append({
                "county": county,
                "title": title,
                "url": url,
                "source_type": "reference",
                "notes": src.get("notes", "Reference URL; no direct PDF"),
                "file": None,
                "downloaded": False,
                "timestamp": _ts(),
            })

    return saved


def _ts():
    return datetime.datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = _session()
    all_metadata = []

    log.info("Kentucky County EOP Collector")
    log.info("Counties with confirmed sources: %d", len(KNOWN_SOURCES))
    log.info("Total counties tracked: %d", len(KY_COUNTIES))

    # Process state-level plans first
    log.info("--- Downloading State-Level KY EOP Documents ---")
    state_dir = OUTPUT_DIR / "_State_Kentucky"
    state_dir.mkdir(parents=True, exist_ok=True)
    for idx, src in enumerate(KNOWN_SOURCES.get("_STATE_KY", [])):
        fname = safe_filename("state_ky", src["url"], idx)
        dest  = state_dir / fname
        ok    = download(session, src["url"], dest)
        all_metadata.append({
            "county": "Kentucky (State)",
            "title": src["title"],
            "url": src["url"],
            "source_type": "direct_pdf",
            "notes": "State-level plan",
            "file": str(dest.relative_to(Path("."))) if ok else None,
            "downloaded": ok,
            "timestamp": _ts(),
        })
        time.sleep(DELAY)

    # Process each of the 120 counties
    for county, county_url in KY_COUNTIES.items():
        try:
            results = process_county(session, county, county_url)
            all_metadata.extend(results)
        except KeyboardInterrupt:
            log.warning("Interrupted.")
            break
        except Exception as exc:
            log.error("[%s] Error: %s", county, exc)

    # Save metadata
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, "w") as fh:
        json.dump(all_metadata, fh, indent=2)
    log.info("Metadata -> %s", META_FILE)

    # Summary
    downloaded  = [r for r in all_metadata if r["downloaded"]]
    counties_ok = {r["county"] for r in downloaded}
    log.info("")
    log.info("=== SUMMARY ===")
    log.info("Total documents downloaded : %d", len(downloaded))
    log.info("Counties with downloads    : %d / %d", len(counties_ok), len(KY_COUNTIES))
    log.info("Metadata records           : %d", len(all_metadata))
    log.info("Output directory           : %s", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
