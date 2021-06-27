from utilities import self_setup_class
import requests

class url_class(self_setup_class):
    def __init__(self, name,**kwargs):
        self.init_empty_setters()
        self['name']=name
        super().__init__(**kwargs)
    def init_empty_setters(self):
        keys=['additional_headers',
              'Authentication', 
              'url',
              ]
        setattr(self, keys[0], {})
        setattr(self, keys[1], False)
        setattr(self, keys[2], '/')
        return self
    def return_url(self,**kwargs):
        if kwargs.get('url_fillers') is not None:
            return self.get('url') % kwargs.get('url_fillers')
        return self.get('url')

class site(self_setup_class):
    def __init__(self,**kwargs):
        self.location=None
        self.url_map=dict()
        self.headers={}
        super().__init__(**kwargs)
    def get_headers(self,key=None):
        if key is None: 
            return self.get('headers')
        url_obj=self.get_url_map().get(key)
        auth = (self.get_auth().get_header_dict() if url_obj.get('Authentication') else {})
        return dict(**self.get_headers(key=None),**url_obj.additional_headers, **auth)        
    def set_header(self,key,value):
        self.get('headers').update({key:value})
        return self.get('headers')
    def set_headers(self,header_dict):
        if isinstance(header_dict , dict):
            self.get('headers').update(header_dict)
            return self.get('headers')
        print(f'headers was not update, {header_dict} is not a dict object')
        return None
    def get_host(self):
        return self.get('host_url')
    def get_url_map(self):
        return self.url_map
    def set_url_map(self,url_list):
        if not isinstance(url_list,list):
            raise ValueError(f"{url_list} is not a list object")
        for url in url_list:
            self.url_map[url.name]=url
        return self.url_map
    def set_url(self,url_obj,key=None):
        if not isinstance(url_obj,url_class):
            raise ValueError(f"{url_obj} is not a instance of class {url_class}")
        if key is None:
            key=url_obj.name
        self.url_map[key]=url_obj
        return self.url_map 
    def get_url(self, key,**kwargs):
        return self.get_host()+self.url_map[key].return_url(**kwargs)
    def start_session(self):
        setattr(self,'session',requests.Session())
        return self.get('session')
    def session_url_get(self,key,payload={}, auth=None, **kwargs):
        return self.get('session').get(
                                self.get_url(key,**kwargs),
                                headers=self.get_headers(key),
                                params=payload,
                                auth=auth
                                )
    def session_url_post(self,key,payload={},auth=None):
        return self.get('session').post(
                                self.get_url(key),
                                headers=self.get_headers(key),
                                data=payload,
                                auth=auth
                                )
    def get_auth(self):
        return getattr(self,'auth') 
    def save_authorization(self,auth_class):
        #derive auth_class from AuthConstructor in utilities
        setattr(self,'auth', auth_class(self))
        return getattr(self,'auth')


print('loaded')
