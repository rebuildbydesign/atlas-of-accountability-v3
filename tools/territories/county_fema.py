import json,collections,re
def norm(s): return re.sub(r' (County|Parish|Municipio|Island|District|Municipality)$','',(s or '').strip())
def totals(st, decl=None):
    d=json.load(open(f'{st}.json'))
    pa=[x for x in d['pa'] if '2011'<=x['declarationDate'][:4]<='2024' and x.get('incidentType')!='Biological' and (decl is None or x['disasterNumber'] in decl)]
    P=collections.Counter(); H=collections.Counter()
    for x in pa:
        if x['county'] not in ('Statewide',None): P[norm(x['county'])]+=x['federalShareObligated'] or 0
    for x in d['hm']:
        amt=x.get('totalObligatedAmount') or 0
        if not amt: continue
        parts=[norm(p) for p in re.split(r'[;,]',x.get('benefitingCounties') or '') if p.strip()]
        if len(set(parts))==1: H[parts[0]]+=amt
    return P,H
