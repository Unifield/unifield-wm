import requests
import time
year = time.strftime('%Y')
for base in ['eur', 'chf']:
    f = open('%s.txt'%base, 'w')
    for x in xrange(1, 11):
        r = requests.get('http://api.fixer.io/latest?date=%s-%02d-01&base=%s'%(year, x, base))
        d = r.json()
        f.write("%s-%02d-01\n"% (year, x))
        for r in d['rates']:
            f.write(" %s:%s\n" % (r, d['rates'][r]))
    f.close()
