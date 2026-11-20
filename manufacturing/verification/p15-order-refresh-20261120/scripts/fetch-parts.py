import csv,json,re,subprocess,datetime,hashlib,sys
from pathlib import Path
E=Path(__import__('os').environ.get('P15_EVIDENCE_DIR', 'tmp/p15-order-refresh')); (E/'jlc').mkdir(exist_ok=True); (E/'lcsc').mkdir(exist_ok=True)
BOM=(Path(__file__).resolve().parents[4] / 'manufacturing/releases/corner-support-review/board-p15/bom.csv')
API='https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
lines=[]
for r in csv.DictReader(BOM.open()):
    refs=[x.strip() for x in r['Designator'].split(',')]; lines.append((r['JLCPCB Part #'],r['Comment'],refs))
out={'_comment':'Read-only public catalog lookups for the board-p15 package BOM. Not a quote, cart or order.','jlc_endpoint':API,'parts':{}}
for code,comment,refs in lines:
    rec={'bom_comment':comment,'refs':refs,'qty_per_board':len(refs),'qty_2_boards':2*len(refs)}
    t=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    body=subprocess.run(['curl','-sS','-m','30','-H','Content-Type: application/json','-A','read-only parts lookup','--data',json.dumps({'keyword':code,'currentPage':1,'pageSize':25}),API],capture_output=True).stdout
    (E/'jlc'/f'{code}.json').write_bytes(body)
    try:
        hit=next((x for x in json.loads(body)['data']['componentPageInfo']['list'] or [] if x.get('componentCode')==code),None)
    except Exception as e: hit=None
    if hit:
        rec['jlc']={'retrieved_utc':t,'raw_file':f'evidence/jlc/{code}.json','raw_sha256':hashlib.sha256(body).hexdigest(),
          'model':hit.get('componentModelEn'),'brand':hit.get('componentBrandEn'),'package':hit.get('componentSpecificationEn'),
          'library_type':hit.get('componentLibraryType'),'preferredComponentFlag':hit.get('preferredComponentFlag'),
          'stock':hit.get('stockCount'),'leastPatchNumber':hit.get('leastPatchNumber'),'lossNumber':hit.get('lossNumber'),
          'minPurchaseNum':hit.get('minPurchaseNum'),'isBuyComponent':hit.get('isBuyComponent'),'noBuyReason':hit.get('noBuyReason'),
          'price_tiers_usd':[[p['startNumber'],p['endNumber'],p['productPrice']] for p in hit.get('componentPrices') or []]}
    else: rec['jlc']={'retrieved_utc':t,'status':'NOT FOUND / UNAVAILABLE'}
    url=f'https://www.lcsc.com/product-detail/{code}.html'
    t=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    html=subprocess.run(['curl','-sS','-L','-m','40','-A','Mozilla/5.0',url],capture_output=True).stdout.decode('utf-8','replace')
    i=html.find('"webData":{')
    seg=html[i:i+8000] if i>=0 else ''
    def g(k):
        m=re.search(r'"%s":("?)([^",}]*)\1'%k,seg); return m.group(2) if m else None
    pl=re.findall(r'"ladder":(\d+),"productPrice":"([0-9.]+)"',seg[:seg.find('"productImages"')] if '"productImages"' in seg else seg)
    lc={'url':url,'retrieved_utc':t,'productCode':g('productCode'),'productModel':g('productModel'),'brand':g('brandNameEn'),'encap':g('encapStandard'),
        'stockNumber':g('stockNumber'),'minBuyNumber':g('minBuyNumber'),'split':g('split'),'price_ladder_usd':[[int(a),float(b)] for a,b in pl]}
    (E/'lcsc'/f'{code}.webData.txt').write_text(seg)
    lc['webData_extract_file']=f'evidence/lcsc/{code}.webData.txt'; lc['page_sha256']=hashlib.sha256(html.encode()).hexdigest()
    if lc['productCode']!=code: lc['status']='UNAVAILABLE (page did not expose this code)'
    rec['lcsc']=lc
    out['parts'][code]=rec
    print(code, rec['jlc'].get('library_type'), rec['jlc'].get('preferredComponentFlag'), rec['jlc'].get('stock'), lc['stockNumber'], lc['productModel'],file=sys.stderr)
(E/'parts-availability-2026-11-20.json').write_text(json.dumps(out,indent=1)+'\n')
