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

#personal secrets
MOBILE='7064787056' #'7436874978'
BENEFICIARIES=[66616675436860,98515269921110]
#profile secrets
CENTRES=[571756,684620]
DATES=['30-06-2021']
PINCODES=['444604']
DOSE=1
DOSE_AVAILABILITY=f'available_capacity_dose{DOSE}'
AGE_LIMITS=[18,]

#constant fields
HOST_URL='https://cdn-api.co-vin.in/api/v2'
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

def get_login(mobile,secrets):
    cowin=site(host_url=HOST_URL, headers=HEADERS)
    cowin.set_url_map([ gen_otp,validate_otp,
                        check_pincode,
                        check_center,
                        schedule])
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
                   (session.get('date') in kwargs.get('dates')) and \
                    (session.get(DOSE_AVAILABILITY) > 0 ) :
                   result['center_id']=centre.get('center_id')
                   result['session_id']=session.get('session_id')
                   result['date']=session.get('date')
                   result['slot']=session.get('slots')[0]
                   return result
    return result 

def scheduler(cowin,response,**kwargs):
    auth = AuthConstructor(response.json())
    details=cowin.session_url_get(check_pincode.name,
                                  auth=auth,
                                  payload={
                                      'pincode': kwargs.get('pincode'),
                                      'date':kwargs.get('date'),
                                  } )
    ''' not available
    details=cowin.session_url_get(check_center.name,
                                  auth=auth,
                                  payload={
                                      'center_id': kwargs.get('center_id'),
                                      'date':kwargs.get('date'),
                                  } )
    '''
    result=details.json()
    payload=payload_prepaper(result, **kwargs)
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
    return result

inputs1=dict(**{'pincode':PINCODES[0], 'date':DATES[0]})
inputs2=dict(beneficiaries=BENEFICIARIES, dose=DOSE, 
                    center_id=CENTRES,
                    min_age_limit=AGE_LIMITS,
                    dates=DATES)
checker=b'child "session_id" fails because ["session_id" is required]'

async def run_multiple(cowin,response, wait=5):
    stat='something'
    while stat!=checker : 
        await asyncio.sleep(wait)
        result=scheduler(cowin=cowin,response=response,**inputs1,**inputs2)
        stat=result.content
        print(result.content)
    response,cowin=get_login(mobile=MOBILE,secrets=secrets)
    if response.status_code==200:
        await run_multiple(cowin,response)
    else:
        print('signin issue:',"\n",(response.content))

if __name__== "__main__":
    response,cowin=get_login(mobile=MOBILE,secrets=secrets)
    #result=scheduler(cowin,response,**inputs1,**inputs2)
    asyncio.run(run_multiple(cowin,response))
