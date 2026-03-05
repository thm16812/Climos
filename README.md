# Climos — Kentucky County Emergency Operations Plans (EOP) Archive

Public records collection of Emergency Operations Plans (EOPs) from all **120 Kentucky counties**, gathered per the Kentucky Open Records Act (KRS 61.870–61.884) and KRS 39A.

---

## What's Here

| Path | Description |
|------|-------------|
| `scraper.py` | Main collector script — downloads PDFs and crawls county EOP pages |
| `requirements.txt` | Python dependencies |
| `data/metadata.json` | Structured record of all 120 counties: URLs, titles, download status |
| `data/eops/` | Downloaded EOP PDFs (populated after running the scraper locally) |
| `data/scraper.log` | Run log |

---

## Confirmed Public EOP Sources (pre-verified)

### State-Level Plans
| Document | URL |
|----------|-----|
| Kentucky State EOP (KYEM) | https://kyem.ky.gov/sitecontacts/Documents/State%20EOP.pdf |
| Updated Kentucky EOP (KYEM) | https://kyem.ky.gov/Documents/Updated%20Kentucky%20Emergency%20Operations%20Plan.pdf |
| Kentucky EOP — Energy & Environment Cabinet | https://eec.ky.gov/Energy/Programs/Documents/Emergency%20Operation%20Plan.pdf |

### County Plans (Direct PDF Links Found)
| County | Document | URL |
|--------|----------|-----|
| **Campbell** | EOP – Search & Rescue Plan | https://campbellcountyky.gov/egov/documents/1735852403_1093.pdf |
| **Campbell** | ESF-13 Public Safety & Security Annex | https://campbellcountyky.gov/egov/documents/1759437436_67386.pdf |
| **Fayette** (Lexington) | EOP Basic Plan (2024) | https://www.bereadylexington.com/wp-content/uploads/2024/09/Fayette-County-Basic-EOP-2024.pdf |
| **Fayette** (Lexington) | EOP Basic Plan (2021) | https://www.bereadylexington.com/wp-content/uploads/2021/06/Basic-Plan.pdf |
| **Fayette** (Lexington) | EOP Index (all ESF annexes) | https://www.bereadylexington.com/emergency-operations-plan/ |
| **Hardin** | Executive Order 2025-001 (EOP adoption) | https://www.hardincountyky.gov/DocumentCenter/View/2862/Executive-Order-2025-001-Emergency-Mgmt-Operations-Plan |
| **Jefferson** (Louisville) | Louisville/Jefferson County EOP 2025 | https://louisvilleky.gov/sites/default/files/2025-10/2025%20Louisville%20Jefferson%20CO%20EOP%20FINAL%2004-07-2025.pdf |
| **Kenton** | EOP Basic Plan | https://www.kentoncounty.org/DocumentCenter/View/298/Kenton-County-Emergency-Operations-Plan-EOP-PDF |
| **Kenton** | EOP Full Version 2022 | https://edgewoodky.gov/wp-content/uploads/2023/07/2022-KCEOP-Full-Version-059-02-2023.pdf |
| **Kenton** | ESF-1 Transportation | https://kentoncounty.org/DocumentCenter/View/297/Emergency-Support-Functions-Transportation-PDF |
| **Kenton** | ESF-3 Public Works & Infrastructure | https://www.kentoncounty.org/DocumentCenter/View/294/Emergency-Support-Functions-Public-Works-Infrastructure-Management-PDF |
| **Kenton** | ESF Hazardous Materials | https://www.kentoncounty.org/DocumentCenter/View/303/Emergency-Support-Functions-Hazardous-Materials-PDF |
| **Kenton** | Incident Management System Plan | https://www.kentoncounty.org/DocumentCenter/View/2804/1A-Incident-Management-System-Plan-PDF |
| **Kenton** | Point of Distribution Plan | https://kentoncounty.org/DocumentCenter/View/2801/Point-of-Distribution-Plan-PDF |
| **Kenton** | Aircraft Incident Response Plan | https://kentoncounty.org/DocumentCenter/View/2816/Aircraft-Emergency-Response-Plan-PDF |
| **Kenton** | Railroad Incident Response Plan | https://www.kentoncounty.org/DocumentCenter/View/2838/Railroad-Emergency-Response-Plan-PDF |
| **Kenton** | Earthquake Preparedness Plan | https://kentoncounty.org/DocumentCenter/View/2830/Earthquake-Preparedness-Plan-PDF |

---

## Running the Scraper Locally

```bash
# 1. Clone the repo
git clone https://github.com/thm16812/Climos.git
cd Climos

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the scraper
python scraper.py
```

The scraper will:
1. Download all pre-confirmed PDF links into `data/eops/<CountyName>/`
2. Crawl known EOP index pages for additional PDFs
3. Record every county's status in `data/metadata.json`
4. Log all activity to `data/scraper.log`

---

## About Kentucky County EOPs

All 120 Kentucky counties are **legally required** to maintain and submit Emergency Operations Plans under:
- **KRS 39A** — Emergency Management — General Provisions
- **KRS 39B** — Local Emergency Management
- **KYEM guidance** — Plans submitted annually to the Kentucky Division of Emergency Management by May 1 each year

County EOPs establish the organizational structure, policies, procedures, and guidelines for coordinating disaster and emergency response. They include Emergency Support Function (ESF) annexes covering transportation, public health, hazardous materials, communications, and more.

### Counties Without Publicly Indexed PDFs

Many county EOPs are stored in KYEM's internal SharePoint and are not publicly posted online. To obtain those plans, submit a **Kentucky Open Records Act request** (KRS 61.870–61.884):

1. Identify the county's official website (see `data/metadata.json`)
2. Contact the county's Emergency Management Agency (EMA) or County Judge/Executive's office
3. Request a copy of the current County EOP and ESF annexes
4. Requests must be fulfilled within **3 business days** under KRS 61.880

KYEM Contact: https://www.kyem.ky.gov
County ESF & EOP info: https://kyem.ky.gov/programs/Pages/County-ESF-and-EOP.aspx

---

## Data Structure (`data/metadata.json`)

Each record contains:
```json
{
  "county": "Jefferson",
  "title": "Louisville/Jefferson County Metro Government EOP 2025",
  "url": "https://louisvilleky.gov/sites/default/...",
  "source_type": "direct_pdf",
  "notes": null,
  "file": "data/eops/Jefferson/jefferson_00_abc12345.pdf",
  "downloaded": true,
  "timestamp": "2026-03-05T18:04:52Z"
}
```

`source_type` values:
- `direct_pdf` — confirmed direct PDF download link
- `crawled_pdf` — PDF found by crawling a county EOP index page
- `page_no_pdfs` — index page crawled but no PDFs extracted
- `reference` — no public PDF found; URL is county's official site for Open Records request

---

## KYEM Area Office Structure

KYEM organizes all 120 counties through 10 regional area offices. Each area office manager reviews and concurs on local EOPs. Contacting your area office is another path to obtaining county EOPs.

| Area | Office Location | Counties |
|------|----------------|---------|
| 1 | Benton | Ballard, Caldwell, Calloway, Carlisle, Fulton, Graves, Hickman, Livingston, Lyon, Marshall, McCracken, Trigg |
| 2 | Glasgow | Allen, Barren, Butler, Edmonson, Grayson, Green, Hart, Logan, Metcalfe, Monroe, Simpson, Warren |
| 3 | Louisville | Breckinridge, Bullitt, Hardin, Henry, Jefferson, Larue, Meade, Nelson, Oldham, Spencer, Shelby, Trimble |
| 4 | Lexington | Anderson, Bourbon, Boyle, Clark, Fayette, Franklin, Jessamine, Marion, Mercer, Nicholas, Washington, Woodford |
| 5 | Northern KY | Boone, Bracken, Campbell, Carroll, Gallatin, Grant, Harrison, Kenton, Owen, Pendleton, Robertson, Scott |
| 6 | Morehead | Bath, Boyd, Carter, Elliott, Fleming, Greenup, Lewis, Mason, Menifee, Montgomery, Morgan, Rowan |
| 7 | Prestonsburg | Breathitt, Floyd, Johnson, Knott, Lawrence, Leslie, Letcher, Magoffin, Martin, Perry, Pike, Wolfe |
| 8 | Harlan | Bell, Clay, Estill, Garrard, Harlan, Jackson, Knox, Laurel, Lee, Madison, Owsley, Powell, Whitley |
| 9 | Lake Cumberland | Adair, Casey, Clinton, Cumberland, Lincoln, McCreary, Pulaski, Rockcastle, Russell, Taylor, Wayne |
| 10 | Owensboro | Christian, Crittenden, Daviess, Hancock, Henderson, Hopkins, McLean, Muhlenberg, Ohio, Todd, Union, Webster |

KYEM Area Offices: https://www.kyem.ky.gov/inside-kyem/area-offices

---

## Contributing

To add more confirmed county EOP links, edit the `KNOWN_SOURCES` dict in `scraper.py` and submit a pull request.
