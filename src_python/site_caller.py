#! /usr/bin/env python
import asyncio
from httpsRequests import ( url_class,
                              site)
from utilities import header_base
import datetime
HOST_URL='https://cdn-api.co-vin.in/api/v2/appointment/sessions/public'

HEADERS=header_base

check_pincode=url_class(name='check_pincode', url='/calendarByPin')
check_center=url_class(name='check_centre', url='/calendarByCenter')
PINCODES=[444601,444602,444603,444604,444605,444606,444607,444701]
CENTRES=[605471,571756,684620,616871,605478,605474,612520,644824,645143,724661,224634,605465,612154,684584,692887,605029,702534,724829,655997,737001,617784,769142,684547, 565759,566714,604809,604846,684616,692872,612172, 684637,34732,628352,612200]

#CENTRES=[571756,684620]        
CENTRES_OPTIONAL=[699016,695702,655911,724786,656096,565412,658130, 562549,734484,638780]
FILTERS={
    'pincode':PINCODES,
    #'center_id':CENTRES+CENTRES_OPTIONAL
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

async def filter_method(output,filters={}):
    tmp_output=list()
    for dict_ in output:
        centres =dict_.get('centers',[])
        if isinstance(centres, list):
            tmp_output.extend(centres)
        else:
            tmp_output.append(centres)
    keys=list(filters.keys())
    if keys:
        for key in keys:
            tmp_output=do_filter(tmp_output,
                                filter_key=key,
                                **filters)
    return tmp_output

async def filter_processor_method(output,processor=None):
    tmp_output=list()
    for dict_ in output:
        centres =dict_.get('centers',[])
        if isinstance(centres, list):
            tmp_output.extend(centres)
        else:
            tmp_output.append(centres)
    if processor:
        tmp_output=list(filter(processor,tmp_output))
    return tmp_output

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
        print('\n item:', item,'\n \n',)

async def print_yield_result(result):
    for item in result:
        print('\n item:', item,'\n \n',)
        yield result

async def pass_result(result):
    for item in result:
        yield item

async def run_pincode(find='today', filters=None):
    cowin=site(host_url=HOST_URL,headers=HEADERS)
    cowin.set_url_map([check_pincode, check_center])
    cowin.start_session()
    if find =='today':
        payloads=payload_generator(pincode=PINCODES)
    else:
        payloads=payload_generator(pincode=PINCODES,date_req=('past',4*6))
    payloads=[i for i in payloads]
    z=0
    while True:
        result=await asyncio.gather(*(caller(cowin,
                                        url_key=check_pincode.name,
                                        payload=payload,
                                       ) for payload in payloads
                                )
                            )
        print(z)
        z=z+1
        #print(result)
        if filters is not None:
            result = asyncio.create_task(filter_method(result,filters=filters))
            result= await result
            #print(result)
        result=await asyncio.create_task(
                            result_extractor(result,
                                            'name',
                                            'center_id',
                                            'pincode',
                                            ['sessions',0,'min_age_limit'],
                                            ['sessions',0,'available_capacity'],
                                            ['sessions',0,'date']
                                            )
                                        )
        await asyncio.create_task(print_result(result))
    return result

def get_date_list(start_date,last_date):
    start=datetime.date.fromisoformat(start_date)
    end =datetime.date.fromisoformat(last_date)
    diff=(end-start).days
    #make end date inclusive in the output
    diff =diff + (1 if diff >=0 else -1)
    result=list()
    for i in range(0,diff, (-1 if diff<0 else 1)):
        date=start+datetime.timedelta(days=i)
        result.append(date.strftime('%d-%m-%Y'))
    return result

def get_payloads(centres,start_date,last_date):
    if isinstance(centres, list):
        for centre in centres:
            yield from get_payloads(centre,start_date,last_date)
        return None 
    dates=get_date_list(start_date,last_date)
    for date in dates:
        yield {'center_id':centres,'date':date}

async def run_centers(centres, start_date, last_date, filters=None):
    cowin=site(host_url=HOST_URL, headers=HEADERS)
    cowin.set_url_map([check_pincode, check_center,])
    cowin.start_session()
    payloads=get_payloads(centres,start_date,last_date)
    z=0
    #generator to list inorder to repeatedly used in while loop
    payloads = [i for i in payloads]
    while True:
        result= await asyncio.gather(*(caller(cowin,
                                        url_key=check_center.name,
                                        payload=payload,
                                       ) for payload in payloads
                                )
                            )
        print('\n \n',f"------Result({z})--------",'\n')
        z=z+1
        if filters is not None:
            result = asyncio.create_task(filter_method(result,filters=filters))
            result= await result
            #print(result)
        result=await asyncio.create_task(
                            result_extractor(result,
                                            'name',
                                            'center_id',
                                            'pincode',
                                            ['sessions',0,'min_age_limit'],
                                            ['sessions',0,'available_capacity'],
                                            ['sessions',0,'date']
                                            )
                                        )
        await asyncio.create_task(print_result(result))
    return result

async def run_scavenger(centres, start_date, last_date, filters=None, z=0):
    cowin=site(host_url=HOST_URL, headers=HEADERS)
    cowin.set_url_map([check_pincode, check_center,])
    cowin.start_session()
    payloads=get_payloads(centres,start_date,last_date)
    #generator to list inorder to repeatedly used in while loop
    payloads = [i for i in payloads]
    result= await asyncio.gather(*(caller(cowin,
                                    url_key=check_center.name,
                                    payload=payload,
                                    ) for payload in payloads
                            )
                        )
    print('\n \n',f"------Result({z})--------",'\n')
    z=z+1
    if filters is not None:
        result = asyncio.create_task(
                filter_processor_method(result,processor=filters)
                                    )
        result= await result
    result=await asyncio.create_task(
                        result_extractor(result,
                                        'name',
                                        'center_id',
                                        'pincode',
                                        ['sessions',0,'min_age_limit'],
                                        ['sessions',0,'available_capacity'],
                                        ['sessions',0,'date']
                                        )
                                    )
    #await asyncio.create_task(print_yield_result(result))
    return result



if __name__ == '__main__':
    print('initiating the run ')
    #asyncio.run(run_pincode(find='today',filters=FILTERS), debug=False)
    asyncio.run(run_centers(centres=CENTRES,start_date='2021-07-07', last_date='2021-07-08', filters={}))
    print('run complete')
