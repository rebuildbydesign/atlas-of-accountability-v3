import json,urllib.request,urllib.parse,sys
def pull(ds,flt):
    B='https://www.fema.gov/api/open/'+ds; rows=[];skip=0; key=ds.split('/')[1]
    while True:
        q={"$filter":flt,"$top":10000,"$skip":skip}
        r=json.load(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(q),timeout=300))[key]; rows+=r
        if len(r)<10000: return rows
        skip+=10000
st=sys.argv[1]
pa=pull('v2/PublicAssistanceFundedProjectsDetails',f"stateAbbreviation eq '{st}'")
hm=pull('v2/HmaSubapplications',f"subapplicantStateAbbreviation eq '{st}'")
json.dump({'pa':pa,'hm':hm},open(f'{st}.json','w')); print(st,len(pa),len(hm))
