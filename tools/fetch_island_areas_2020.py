#!/usr/bin/env python3
"""
Census 2020 Island Areas DHC (American Samoa, Guam, N. Mariana Islands,
U.S. Virgin Islands) -> data/census2020_island_areas.csv.
Per county-equivalent: total pop, 60+ pop (table P8), people of color
(total minus non-Hispanic white alone, table P5, same definition as CDC
SVI EP_MINRTY) and the race breakdown the county popup shows.
Needs a Census API key in ~/.census_api_key.
"""
import csv, json, os, re, urllib.request

KEY = open(os.path.expanduser("~/.census_api_key")).read().strip()
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "census2020_island_areas.csv")
NH = "Not Hispanic or Latino:!!"
RACE = {  # popup field -> P5 label tail
    "COUNTY_PCT_AFAM": NH + "One Race:!!Black or African American",
    "COUNTY_PCT_ASIAN": NH + "One Race:!!Asian",
    "COUNTY_PCT_AIAN": NH + "One Race:!!American Indian and Alaska Native",
    "COUNTY_PCT_NHPI": NH + "One Race:!!Native Hawaiian and Other Pacific Islander",
    "COUNTY_PCT_OTHERRACE": NH + "One Race:!!Some Other Race",
    "COUNTY_PCT_TWOMORE": NH + "Two or More Races",
    "COUNTY_PCT_HISP": "Hispanic or Latino (of any race)",
}


def get(url):
    return json.load(urllib.request.urlopen(url))


def label_tail(label):
    return re.sub(r"^\s*!!Total:!!", "", label).rstrip(":")


rows = []
for ds in ["dhcas", "dhcgu", "dhcmp", "dhcvi"]:
    v = get(f"https://api.census.gov/data/2020/dec/{ds}/variables.json")["variables"]
    by_tail = {label_tail(x["label"]): k for k, x in v.items()
               if x.get("group") == "P5" and k.endswith("N")}
    old = [k for k, x in v.items() if x.get("group") == "P8" and k.endswith("N")
           and re.search(r"!!(6\d|[7-9]\d) (to \d+ years|years and over)$", x["label"])]
    assert len(old) == 12, (ds, old)  # 60-64 .. 85+, both sexes
    race = {f: by_tail[t] for f, t in RACE.items()}
    white = by_tail[NH + "One Race:!!White"]
    get_vars = ["NAME", "P8_001N", "P5_001N", white] + old + list(race.values())
    data = get(f"https://api.census.gov/data/2020/dec/{ds}?get={','.join(get_vars)}"
               f"&for=county:*&key={KEY}")
    for r in data[1:]:
        x = dict(zip(data[0], r))
        tot = int(x["P8_001N"])
        p60 = sum(int(x[k]) for k in old)
        pct = lambda n: round(100 * n / tot, 1) if tot else None
        row = {"GEOID": x["state"] + x["county"], "NAME": x["NAME"], "POP_2020": tot,
               "POP_60PLUS": p60, "PCT_60PLUS": round(100 * p60 / tot, 4) if tot else None,
               "COUNTY_PCT_MINORITY": pct(tot - int(x[white]))}
        row.update({f: pct(int(x[k])) for f, k in race.items()})
        rows.append(row)

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: r["GEOID"]))
print(f"wrote {len(rows)} rows -> {OUT}")
