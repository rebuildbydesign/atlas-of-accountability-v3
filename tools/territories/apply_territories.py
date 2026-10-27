"""DC + U.S. territories: fill map fields from the Atlas+ workbook's US Territories tab.

Source: data/us_territories_workbook.csv (export of the workbook tab, 27 Oct 2026).
Race/ethnicity breakdown: CDC SVI 2022 (Puerto Rico) and U.S. Census 2020 Island Areas,
same files as tools/fetch_island_areas_2020.py. Also fixes the swapped USVI names (78020/78030) and the swapped American Samoa shapes (60040/60050).
Run from the repo root: python3 tools/territories/apply_territories.py
"""
import csv, json

SRC = 'data/Atlas_FEMA_V2.geojson'
raw = open(SRC, encoding='utf-8').read()
d = json.loads(raw)
assert json.dumps(d) == raw, 'round-trip changes bytes; stop'

wb = {r['GEOID']: r for r in csv.DictReader(open('data/us_territories_workbook.csv'))}
isl = {r['GEOID']: r for r in csv.DictReader(open('data/census2020_island_areas.csv'))}
svi = {r['FIPS'].zfill(5): r for r in csv.DictReader(open('data/svi2022_pr_county.csv', encoding='utf-8-sig'))}

NAMES = {'60040': 'Swains Island', '60050': 'Western District',  # after the shape swap below
         '78020': 'Saint John Island', '78030': 'Saint Thomas Island'}
RACE = ['COUNTY_PCT_AFAM', 'COUNTY_PCT_HISP', 'COUNTY_PCT_ASIAN', 'COUNTY_PCT_AIAN',
        'COUNTY_PCT_NHPI', 'COUNTY_PCT_TWOMORE', 'COUNTY_PCT_OTHERRACE']
SVI_RACE = {'COUNTY_PCT_AFAM': 'EP_AFAM', 'COUNTY_PCT_HISP': 'EP_HISP', 'COUNTY_PCT_ASIAN': 'EP_ASIAN',
            'COUNTY_PCT_AIAN': 'EP_AIAN', 'COUNTY_PCT_NHPI': 'EP_NHPI', 'COUNTY_PCT_TWOMORE': 'EP_TWOMORE',
            'COUNTY_PCT_OTHERRACE': 'EP_OTHERRACE'}

def tier(n):
    return (None if n == 0 else 'Low (1-4)' if n < 5 else 'Moderate (5-9)' if n < 10
            else 'High (10-14)' if n < 15 else 'Extreme (15+)')

done = set()
for f in d['features']:
    p = f['properties']
    g = p['GEOID']
    if g not in wb:
        continue
    w = wb[g]
    assert int(p['COUNTY_DISASTER_COUNT']) == int(w['COUNTY_DISASTER_COUNT']), g
    if g in NAMES:
        p['NAMELSAD'] = NAMES[g]
    pop, o60 = float(w['COUNTY_TOTAL_POP']), float(w['POP_60PLUS'])
    if p['COUNTY_POPULATION'] in (None, 'NULL'):
        p['COUNTY_POPULATION'] = str(int(pop))
    if pop > 0:
        p['county-level-older-adults_TOTAL POP'] = pop
        p['county-level-older-adults_60+ POP'] = o60
        p['county-level-older-adults_PCT POP 60+'] = round(o60 / pop * 100, 1)
        p['county-level-older-adults_DISASTER TIER'] = tier(int(w['COUNTY_DISASTER_COUNT']))
    delineated = w['OMB_CLASS'] in ('Urban', 'Rural')
    p['OMB_CLASS'] = w['OMB_CLASS'] if delineated else None
    p['county-level-older-adults_OMB CLASS'] = p['OMB_CLASS'] if pop > 0 else None
    p['OMB_TIER'] = w['OMB_TIER'] if delineated else None
    p['OMB_AREA'] = w['OMB_AREA'] if delineated else None
    if w['PCT_PEOPLE_OF_COLOR']:
        p['COUNTY_PCT_MINORITY'] = round(float(w['PCT_PEOPLE_OF_COLOR']) * 100, 1)
        if g in isl:
            for k in RACE:
                p[k] = float(isl[g][k]) if isl[g][k] else None
        elif g in svi:
            for k in RACE:
                v = float(svi[g][SVI_RACE[k]])
                p[k] = None if v < 0 else v
    done.add(g)

assert done == set(wb), set(wb) - done

# American Samoa: the 60040 (Swains) and 60050 (Western District) shapes sit under each other's GEOID.
# Swap the geometry so each GEOID's data draws in the right place.
f40, f50 = [next(f for f in d['features'] if f['properties']['GEOID'] == g) for g in ('60040', '60050')]
f40['geometry'], f50['geometry'] = f50['geometry'], f40['geometry']
open(SRC, 'w', encoding='utf-8').write(json.dumps(d))
print('updated', len(done), 'DC and territory areas')
