import requests
from mx import DateTime
date_now = DateTime.now()+DateTime.RelativeDateTime(day=1)
#for base in ['eur', 'chf']:
date_from = DateTime.strptime('2023-01-01', '%Y-%m-%d')
feur = open('eur.txt', 'w')
fchf = open('chf.txt', 'w')

#r = requests.get('https://api.exchangeratesapi.io/history?start_at=%s&base=%s'%(date_from.strftime('%Y-%m-%d'), base.upper()))
while date_from < date_now:
    r = requests.get('https://ec.europa.eu/budg/inforeuro/api/public/monthly-rates?year=%s&month=%s&lang=fr' % (date_from.strftime('%Y'), date_from.strftime('%m')))
    d = r.json()
    feur.write("%s\n" % (date_from.strftime('%Y-%m-01'), ))
    fchf.write("%s\n" % (date_from.strftime('%Y-%m-01'), ))
    cur = {}
    for rates in d:
        if rates['isoA3Code'] != 'EUR':
            feur.write(" %s:%s\n" % (rates['isoA3Code'], rates['value']))
        cur[rates['isoA3Code']] = rates['value']

    for code in cur:
        if code != 'CHF':
            fchf.write(" %s:%s\n" % (code, cur[code]/cur['CHF']))
    date_from += DateTime.RelativeDateTime(months=1)
feur.close()
fchf.close()
