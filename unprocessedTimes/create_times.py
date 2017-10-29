import requests
from bs4 import element
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

routes = []
routes_response = requests.get('https://realtimetcatbus.availtec.com/InfoPoint/rest/Routes/GetVisibleRoutes')
routes_json = routes_response.json()

for route in routes_json:
    routeNum = route['RouteId']

    route = requests.get('https://tcatbus.com/route{}/'.format(routeNum))
    soup = BeautifulSoup(route.text, "lxml")
    tables = BeautifulSoup(route.text, parse_only=SoupStrainer('table'))
    # tables = BeautifulSoup(route.text, "lxml", parse_only=SoupStrainer('table'))

    # title is contained in h2 or span, but so difficult to parse!
    # so you have to manually do it
    # h2 = BeautifulSoup(route.text, "lxml", parse_only=SoupStrainer('h2')).contents[1:]
    # span = BeautifulSoup(route.text, "lxml", parse_only=SoupStrainer('span')).contents[1:]

    i=0
    for table in tables.contents:
        try:
            if not isinstance(table, element.Doctype):
                i+=1
                fileName = str(routeNum)+'_'+str(i)+'.txt'
                fid = open(fileName,'w')
                # get stops
                stops=''
                for stop in table.thead.tr:
                    try:
                        # need to get id for stop names from stop table
                        stops = stops+','+(stop.contents[2].strip())
                    except:
                        None
                # remove beginning comma
                fid.write(stops[1:]+'\n')
                # get times
                for tr in table.tbody.contents:
                    if not isinstance(tr, element.NavigableString):
                        times = ''
                        for td in tr.children:
                            if (not isinstance(td, element.NavigableString)):
                                try:
                                    if ':' not in (td.contents[0]):
                                        # line of times has an error; manually fix
                                        times = times+','+('ERROR')
                                    else:
                                        abbrev = td.contents[0][-1:]
                                        time = td.contents[0][:-1].strip()
                                        if abbrev == 'P':
                                            h,m = time.split(':')
                                            h = str(int(h)+12)
                                            time = h+':'+m
                                            if time != '':
                                                time = time+':00'
                                        times = times+','+('{}'.format(time))
                                except:
                                    pass
                        # remove beginning comma
                        fid.write(times[1:]+'\n')
                fid.close()
        except Exception as e:
            pass