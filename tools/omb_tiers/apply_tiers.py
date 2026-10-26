# Adds OMB 2023 tiers to data/Atlas_FEMA_V2.geojson (REB-596). Same CSV as the workbook's County Totals AA/AB.
import csv, json, sys
SRC = 'data/Atlas_FEMA_V2.geojson'
raw = open(SRC, encoding='utf-8').read()
d = json.loads(raw)
assert json.dumps(d) == raw, 'round-trip changes bytes; stop'
tiers = {r['GEOID'].zfill(5): r for r in csv.DictReader(open('tools/omb_tiers/county_tiers_omb2023.csv'))}
# DC is mapped but not in the workbook: Washington-Arlington-Alexandria metro, 6.3M (Census 2024)
tiers['11001'] = {'TIER': 'Large metro', 'URBAN': 'True', 'CBSA Title': 'Washington-Arlington-Alexandria, DC-VA-MD-WV'}
n = 0
# One-off fix: Dona Ana County, NM name was stored garbled (Mac Roman mojibake)
for f in d['features']:
    if f['properties']['GEOID'] == '35013': f['properties']['NAMELSAD'] = 'Do\u00f1a Ana County'
for f in d['features']:
    p = f['properties']; t = tiers.get(p['GEOID'])
    if not t: continue
    p['OMB_CLASS'] = 'Urban' if t['URBAN'] == 'True' else 'Rural'
    p['OMB_TIER'] = t['TIER']
    p['OMB_AREA'] = t['CBSA Title'] or None
    n += 1
print('features updated', n, 'of', len(d['features']))
open(SRC, 'w', encoding='utf-8').write(json.dumps(d))
