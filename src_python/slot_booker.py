#! /usr/bin/env python
import hashlib
import asyncio
from httpsRequests import ( url_class,
                              site)
from utilities import (header_base,
                        self_setup_class)
from requests.auth import AuthBase
import datetime
import random
import json
import asyncio
from site_caller import run_scavenger
import datetime
from functools import partial 

#personal secrets
#----remove after usage --------

#-------------------------------
#-----uncomment for usage---------
MOBILE='7064787056' #'7436874978'
BENEFICIARIES=[51138106481350,54676226208390]
#---------------------------------------------
#profile secrets
#CENTRES=[552724]
#PINCODES=['122001']
CENTRES=[571756,684620]
DATES=['07-07-2021','08-07-2021']
PINCODES=['444604']
DOSE=1
DOSE_AVAILABILITY=f'available_capacity_dose{DOSE}'
AGE_LIMITS=[18,]

#constant fields
HOST_URL='https://cdn-api.co-vin.in/api/v2'
header_base.update({'Connection':'Keep-Alive', 'Keep-Alive': 'timeout=120, max=10'})
HEADERS=header_base

gen_otp=url_class(name='gen_otp', 
                url='/auth/generateMobileOTP',
                additional_headers={'Content-Type' :'application/json'},
                )
validate_otp=url_class(name='validate_otp',
                        url='/auth/validateMobileOtp',
                    additional_headers={'Content-Type' :'application/json'},
                        )

check_pincode=url_class(
                        name='check_pincode', 
                        url='/appointment/sessions/calendarByPin')
check_center=url_class( 
                    name='check_centre', 
                     url='/appointment/sessions/calendarByCenter')

schedule  =   url_class( 
                    name='schedule', 
                     url='/appointment/schedule',
                     additional_headers={'Content-Type' :'application/json'},
                     )

check_api=url_class(name='api',
                    url='/appointment/beneficiaries')

URL_BUNDLE=[ gen_otp,
             validate_otp,
             check_pincode,
             check_center,
             schedule,
             check_api,
            ]

secrets=[ 
    "U2FsdGVkX1/C7fnXOFbSDgri16OJEv3dgeN01kJHfHx6+KRnL0theqWcB9sE+Y+SaA3hQQjHHusA81mwpihaiA==",
    "U2FsdGVkX1/Z13izD4JJbn7UVhAUV34Cnkg8YRHhiWZVfcQarDVrK+cw+2kZBwXSsTl/U3vZ6EKa1/VM6WeiFg==",
    "U2FsdGVkX1/tejzCmUuKbe5I3LjqxRLAY2Gu1nCI+NQ61i44vBceJ2IRqjU65HHNrLtTRMNEQWtAQB/XmgVYVg==",
    ]

class AuthConstructor(AuthBase,self_setup_class):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, dict_obj,**kwargs):
        #site_obj is instance of class:site
        # setup any auth-related data here
        tmpKey='Bearer'
        tmp_word='token'
        self.tmpKey=tmpKey
        setattr(self, self.tmpKey, 
                    dict_obj.get(tmp_word))
        super().__init__(**kwargs)
    def get_header_dict(self):
        return {'Authorization': f"{self.tmpKey} {getattr(self, self.tmpKey)}" }
    def __call__(self, r):
        # modify and return the request
        r.headers['Authorization'] = f"{self.tmpKey} {getattr(self, self.tmpKey)}"
        return r

def date_object_creator(dateString):
    day,month,year=dateString.split('-')
    obj=datetime.date(year=int(year),month=int(month),day=int(day))
    return obj.isoformat()

def get_login(mobile,secrets,url_bundle=URL_BUNDLE):
    cowin=site(host_url=HOST_URL, headers=HEADERS)
    cowin.set_url_map(url_bundle)
    cowin.start_session()
    payload={'mobile':mobile, 
            'secret': secrets[random.randint(0,len(secrets)-1)] }
    reply_id=cowin.session_url_post(gen_otp.name,payload=json.dumps(payload))
    print('login_mobile_secret:',f'{reply_id.status_code}','\n')
    reply_id=reply_id.json()
    otp=input('give_otp:\n')
    payload={'otp':hashlib.sha256(otp.encode()).hexdigest(),
             'txnId':reply_id['txnId']}
    response=cowin.session_url_post(validate_otp.name,
                                    payload=json.dumps(payload)
                                    )
    print('login_otp_response:',f'{response.status_code}','\n')
    return response,cowin

def payload_prepaper(context, **kwargs):
    result={}
    centres=context.get('centers',[])
    for centre in centres:
        if centre.get('center_id') in kwargs.get('center_id'):
            sessions=centre['sessions']
            for session in sessions:
                if (session.get('min_age_limit') in kwargs.get('min_age_limit') ) and \
                   (session.get('date') in kwargs.get('dates'))  and \
                   (session.get(DOSE_AVAILABILITY) > 0 ) :
                        result['center_id']=centre.get('center_id')
                        result['session_id']=session.get('session_id')
                        result['date']=session.get('date')
                        result['slot']=session.get('slots')[0]
                        yield result
    return result

def payload_filter(centre, **kwargs):
    #result={}
    #centre=context.get('centers',{})
    if centre.get('center_id') in kwargs.get('center_id',[]):
        sessions=centre['sessions']
        for session in sessions:
            if (session.get('min_age_limit') in kwargs.get('min_age_limit') ) and \
                (session.get('date') in kwargs.get('dates'))  and \
                (session.get(DOSE_AVAILABILITY) > 0 ) :
                    #result['center_id']=centre.get('center_id')
                    #result['session_id']=session.get('session_id')
                    #result['date']=session.get('date')
                    #result['slot']=session.get('slots')[0]
                    return True
    return False 

def dry_run_scheduler(cowin,response,**kwargs):
    auth=AuthConstructor(response.json())
    details=cowin.session_url_get(check_api.name,
                                    auth=auth,)
    print(details.status_code,kwargs.get('count'))#)
    return details

def scheduler(cowin,response,**kwargs):
    auth = AuthConstructor(response.json())
    details=cowin.session_url_get(check_pincode.name,
                                  auth=auth,
                                  payload={
                                      'pincode': kwargs.get('pincode'),
                                      'date':kwargs.get('date'),
                                  } )
    print('session_search:',details.status_code)
    if details.status_code!=200:
        print(details.content)
    if details.content== b'{"message":"User is not authorized to access this resource with an explicit deny"}':
        yield None
    ''' not available
    details=cowin.session_url_get(check_center.name,
                                  auth=auth,
                                  payload={
                                      'center_id': kwargs.get('center_id'),
                                      'date':kwargs.get('date'),
                                  } )
    '''
    result=details.json()
    payloads=payload_prepaper(result, **kwargs)
    for payload in payloads:
        payload['beneficiaries']=kwargs.get('beneficiaries')
        payload['dose']=kwargs.get('dose')
        print(payload)
        '''payload= {"center_id":xxxxx,
                "session_id":"7xxxcb0x-xxxx-xxxx-bc43-b16xxxxc2a04",
                "beneficiaries":BENEFICIARIES,
                "slot":"09:00AM-10:00AM","dose":1}'''
        result=cowin.session_url_post(schedule.name,
                                    auth=auth,
                                    payload=json.dumps(payload))
        yield result 

async def dry_run(cowin,response,wait=5, inputs1={},inputs2={}):
    count=1
    while True:
        await asyncio.sleep(wait)
        dry_run_scheduler(cowin,response,count=count)
        count=count+1

async def run_multiple(cowin,response, wait=5,inputs1={},inputs2={},checker=None):
    stat='something'
    while stat!=checker : 
        result_gen=scheduler(cowin=cowin,response=response,**inputs1,**inputs2)
        for result in result_gen:
            stat=result.content
            print(result.content)
    await asyncio.sleep(wait)
    response,cowin=get_login(mobile=MOBILE,secrets=secrets)
    if response.status_code==200:
        await run_multiple(cowin,response)
    else:
        print('signin issue:',"\n",(response.content))

async def run_continuous( mobile, secrets, 
                            cowin=None,response=None,
                            wait=5,inputs1={},inputs2={},count=0):
    if response is None: 
        response,cowin=get_login(mobile=mobile,secrets=secrets)
    state=True
    while state:
        result_gen=scheduler(cowin=cowin,response=response,**inputs1,**inputs2)
        for result in result_gen:
            if result is not None :
                print('\n',result.content,'\n')
            if result is None:
                state=False
        print('count:',count)
        count=count+1
        await asyncio.sleep(wait)
    await run_continuous(mobile=mobile,secrets=secrets,cowin=cowin,response=None,
                         wait=wait,inputs1=inputs1,inputs2=inputs2,count=count)

async def run_loop(centres,start_date,last_date,filters={},check_wait=5,wait=5,z=0):
    inputs2=dict(beneficiaries=BENEFICIARIES, dose=DOSE, 
                        center_id=centres,
                        min_age_limit=AGE_LIMITS,
                        dates=DATES)
    filters=partial(filters,**inputs2)
    while True:
        for i in await run_scavenger(centres=centres,
                                start_date= start_date, 
                                last_date= last_date, 
                                filters=filters,z=z):
            if i :
                print(i)
                inputs1=dict(**{'pincode': [i.get('pincode')], 'date':[i.get('date')]})
                inputs2=dict(beneficiaries=BENEFICIARIES, dose=DOSE, 
                        center_id=[i.get('center_id')],
                        min_age_limit=AGE_LIMITS,
                        dates=DATES)
                await run_continuous(mobile=MOBILE,secrets=secrets,
                                wait=wait,
                                inputs1=inputs1,
                                inputs2=inputs2)
        await asyncio.sleep(check_wait)
        z=z+1

if __name__== "__main__":
    """
    inputs1=dict(**{'pincode':PINCODES[0], 'date':DATES[0]})
    inputs2=dict(beneficiaries=BENEFICIARIES, dose=DOSE, 
                    center_id=CENTRES,
                    min_age_limit=AGE_LIMITS,
                    dates=DATES)
    checker=b'child "session_id" fails because ["session_id" is required]'
    #response,cowin=get_login(mobile=MOBILE,secrets=secrets)
    #result=scheduler(cowin,response,**inputs1,**inputs2)
    '''
    asyncio.run(run_multiple(cowin,response,
                             inputs1=inputs1,
                             inputs2=inputs2,
                             checker=checker
                             ))
    '''
    #asyncio.run(dry_run(cowin,response,wait=10,))
    
    asyncio.run(
        run_continuous(mobile=MOBILE,secrets=secrets,
            wait=20,
            inputs1=inputs1,
            inputs2=inputs2))
    
    """
    #--------------------
    
    start_date=date_object_creator(DATES[0])
    last_date=date_object_creator(DATES[-1])
    asyncio.run(run_loop(centres=CENTRES,
                            start_date= start_date, 
                            last_date= last_date, 
                            filters=payload_filter,
                            check_wait=3,
                            wait=5,
                            ))
        
