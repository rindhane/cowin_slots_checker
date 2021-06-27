import base64
import brotlicffi
import json
import requests
from requests.auth import AuthBase

#helps
#https://stackoverflow.com/questions/49584929/unable-to-decode-python-web-request

#supporting data
header_base={
    'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
}
#other optional headers:
'''
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    Connection: keep-alive
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept': 'application/json, text/plain, */*',
    Upgrade-Insecure-Requests: 1, 
    'Referer':'https://www.example.com',
    'Content-Type': 'application/x-www-form-urlencoded',
    Pragma: no-cache
    Cache-Control: no-cache
'''

def dict_from_cookieJar(cookie_jar):
    return requests.utils.dict_from_cookiejar(cookie_jar)

def output_formatter(response, output):
    if output=='cookies':
        return response.cookies
    if output=='compressed_json':
        return json.loads(
            brotlicffi.decompress(response.content).decode('utf-8')
                            )
    if output=='json':
        return json.loads(response.content.decode('utf-8'))
    raise Exception(f'following format: {output} is not available')

class self_setup_class : 
    '''helper class to setup class which can create attributes from 
    the passed key value pairs during initalization of instance'''
    def __init__(self,**kwargs):
        self.set_inputs(**kwargs)
    def set_inputs(self,**inputs):
        for key in inputs:
            setattr(self,key,inputs.get(key))
    def __getitem__(self,tag):
        if not isinstance(tag,str):
            raise ValueError (f"{tag} is not string , provide key in string format" )
        return getattr(self,tag,None)
    def __setitem__(self,tag,value):
        if not isinstance(tag,str):
            raise ValueError (f"{tag} is not string , provide key in string format" )
        setattr(self,tag,value)
        return value
    def keys(self):
        return list(vars(self).keys())
    def items(self):
        return list(vars(self).items())
    def get(self,key,default=None):
        if self.__getitem__(key) is None :
            return default
        return self.__getitem__(key)

class AuthConstructor(AuthBase,self_setup_class):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, site_obj,**kwargs):
        #site_obj is instance of class:site
        # setup any auth-related data here
        tmpKey='enctoken'
        self.tmpKey=tmpKey
        setattr(self, self.tmpKey, 
                    site_obj.get('session').cookies.get(tmpKey))
        super().__init__(**kwargs)
    def get_header_dict(self):
        return {'Authorization': f"{self.tmpKey} {getattr(self, self.tmpKey)}" }
    def __call__(self, r):
        # modify and return the request
        r.headers['Authorization'] = f"{self.tmpKey} {getattr(self, self.tmpKey)}"
        return r

