import asyncio
from httpsRequests import ( url_class,
                              site)

import datetime
HOST_URL='https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin'

HEADERS={
    'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
}

check=url_class(name='check')
PINCODES=[444601,444602,444603,444604,444605,444606,444607]
FILTERS={
    'pincode':PINCODES,
}

def site_request(site,
                url_key,
                payload,):
    trial=site.session_url_get(url_key,
                            payload=payload
                            )
    return trial.json()

def date_provider(date_req):
    #date_req is a tuple object with len of 2 in format (str,int)
    
    current=datetime.date.today()
    weeks=0
    if date_req[0]!='today':
        weeks=date_req[1]
    ans=list()
    for i in range(0,weeks+1):
        date=current+datetime.timedelta(
            days=i*7*(-1 if date_req[0]=='past' else 1)
            )
        ans.append(date.strftime('%d-%m-%Y'))
    return ans

def payload_generator(pincode,date_req=None):
    #pincode is a int or list of int
    if date_req is None:
        date_req=('today',0)
    if isinstance(pincode,list):
        for pin in pincode:
            yield from payload_generator(pin,date_req)
            continue 
        return None
    dates=date_provider(date_req)
    #dates is a list of date strings
    for date in dates:
        yield {'pincode':pincode,'date':date}

async def caller (site,url_key,payload):
    output=site_request(site,
                        url_key=url_key,
                        payload=payload)
    #print(output)
    return output

def do_filter(centres,filter_key,**kwargs):
    result=list()
    for centre in centres:
        if centre.get(filter_key) in kwargs.get(filter_key,[]):
            result.append(centre)
    return result 

async def filter_method(output,filters):
    result=list()
    keys=list(filters.keys())
    for dict_ in output:
        centres =dict_.get('centers',[])
        ans=centres
        for key in keys:
            ans=do_filter(ans,
                        filter_key=key,
                        **filters)
            result.extend(ans)            
    return result

def get_item_value(key,item):
    if isinstance(key,str):
        return key, item[key]
    if isinstance(key,list):
        key=list(key)
        tmp=key.pop(0)
        item=item[tmp]
        if len(key)>0:  
            return get_item_value(key,item)
        return tmp, item    

async def result_extractor(result,*fields):
    final_result=list()
    keys=list(fields)
    for item in result:
        ans=dict()
        for key in keys:
            index,value=get_item_value(key,item)
            ans[index]=value
        final_result.append(ans)
    return final_result

async def print_result(result):
    for item in result:
        print(item,'\n \n')

async def main(find='today', filters=None):
    cowin=site(host_url=HOST_URL,headers=HEADERS)
    cowin.set_url_map([check,])
    cowin.start_session()
    if find =='today':
        payloads=payload_generator(pincode=PINCODES)
    else:
        payloads=payload_generator(pincode=PINCODES,date_req=('past',4*6))
    payloads=[i for i in payloads]
    z=0
    while True:
        result=await asyncio.gather(*(caller(cowin,
                                        url_key=check.name,
                                        payload=payload,
                                       ) for payload in payloads
                                )
                            )
        print(z)
        z=z+1
        #print(result)
        if filters:
            result = asyncio.create_task(filter_method(result,filters=FILTERS))
            result= await result
            #print(result)
        result=await asyncio.create_task(
                            result_extractor(result,
                                            'name',
                                            'center_id',
                                            ['sessions',0,'min_age_limit'],
                                            ['sessions',0,'available_capacity'],
                                            ['sessions',0,'date']
                                            )
                                        )
        await asyncio.create_task(print_result(result))
    return result

print('initating the run ')
asyncio.run(main(find='today',filters=FILTERS), debug=False)
print('run complete')
