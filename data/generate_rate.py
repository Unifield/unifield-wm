import requests
from mx import DateTime
date_now = DateTime.now()+DateTime.RelativeDateTime(day=1)
for base in ['eur', 'chf']:
    date_from = DateTime.strptime('2016-01-01', '%Y-%m-%d')
    f = open('%s.txt'%base, 'w')

    while date_from <= date_now:
        r = requests.get('http://api.fixer.io/latest?date=%s&base=%s'%(date_from.strftime('%Y-%m-%d'), base))
        d = r.json()
        f.write("%s\n" % (date_from.strftime('%Y-%m-%d'), ))
        for r in d['rates']:
            f.write(" %s:%s\n" % (r, d['rates'][r]))
        date_from += DateTime.RelativeDateTime(months=1)
    f.close()
