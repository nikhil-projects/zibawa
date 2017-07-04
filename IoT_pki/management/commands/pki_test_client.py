from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
from unittest import result
logger = logging.getLogger(__name__)
import time
from requests import Request, Session
import requests
import json
import sys
import os
from IoT_pki.x509_functions import id_generator



class Command(BaseCommand):
    help = 'simulation for x509 automatic issuing and renewal. Certificate will be deleted at end of routine'

       
    
    def handle(self, *args, **options):
    #handle is being called by manage.py pki_test_client as a simulation.  The code below could be called from cron job every 24 hours on an IoT device    
        global pathToClientCert
        pathToClientCert="/tmp/tempCert.pem"  
        
        #this is the ca_cert used for SSL of your server, (NOT the ca issuing the client certificates).  
        #if using letsencrypt of similar, then should not be necessary.
        global pathToCACert
        pathToCACert=settings.PKI['path_to_ca_cert'] 
        
        global pathToToken
        pathToToken="/tmp/token.txt"#client needs to store a temporary token on file to retrieve certificate
        
        #each device must identify itself with unique common name to go on certificate
        #this must be different for each client device or user. For test purposes we generate random ID.
        #in practise you adopt your own strategy to assign unique common names to your devices
        global device_common_name 
        device_common_name= id_generator(5)#generate random ID each time we use
        
          
        #for the purposes of the simulation we will remove the old cert and token file each time!
        try:
            os.remove(pathToClientCert)
            
        except:
            pass
        try:
            os.remove(pathToToken)
        except:
            pass    
        
        haveValidCertificate=False
        while (haveValidCertificate==False):
            haveValidCertificate=processRequest()
            time.sleep(5)
        
        
    
def processRequest():                    
        #tries to renew certificate if available, if not makes request to obtain new certificate
        
     
        
        logger.info('checking for presence of certificate file')
        
        if (os.path.isfile(pathToClientCert)):
            data={}
            result=callPKI2 ('/IoT_pki/renew_cert/',data,'GET')
            if (result.status_code==201):
                with open(pathToClientCert,"wb") as f:
                    f.write(result.content)
                    test_certificate()
                    logger.info('certificate renewed..exiting')
                    return True
        
            elif (result.status_code==200):
                 logger.info('certificate valid but not due for renewal..exiting')
                 return True
            else:
                logger.info('certificate not valid')        
        else:
            logger.info('no client certificate found')
        
        try:
            token=readTokenFromFile()
            tokenIsValid=True
        except:
            tokenIsValid=False
            
        while tokenIsValid:
        #if we have a valid token we will try to collect certificate, until we get an invalid token response from the server
        #
            result=collectCertWithToken(token)
            if(result.status_code==201):
                os.remove(pathToToken)
                logger.info("collected cert with token - test renewal before exiting")
                #we should have valid cert here, but return False to force test renewal before exiting
                return False
            elif (result.status_code==404):
                logger.info('token not found')
                tokenIsValid=False
                os.remove(pathToToken)
            else:
                #unapproved token requests return 403 token is kept
                logger.debug('token is not approved, go to admin panel and approve cert_request')
                return False
                    
                
            
        logger.info('making new cert request')
        postdata={'common_name':device_common_name}
        result=callPKI ('/IoT_pki/new_request/',postdata,'POST')
        try:
            data=result.json()
        except:
            pass
        if (result.status_code==201):
            logger.info('obtained request token')
            token=data['token']
            writeTokenToFile(token)
        else:
            logger.error('unable to request new certificate')    
        return False
                
def writeTokenToFile(token):
    with open(pathToToken,"w") as f:
        f.write(token)
        f.close()

def readTokenFromFile():
    with open(pathToToken,"r") as f:
        token= f.read()
        f.close()
        logger.debug("token:%s",token)
        return token    
            
            
def collectCertWithToken(token):
        #returns result to allow us to decide what to do as function of status code
        apiurl="/IoT_pki/cert_collect/"+str(token)+"/"
        data={}
        result=callPKI2(apiurl,data,'GET')
        if (result.status_code==201):
            with open(pathToClientCert,'wb') as f:
      
    # write the contents of the response (r.content)
    # to a new file in binary mode.
                f.write(result.content)
                logger.info('client certificate saved')
            
        return result
        

def callPKI2(apiurl,data,callType):

        
    if settings.PKI['use_ssl']:
        protocol='https://'
        if settings.PKI['verify_certs']:
            #TO DO   need to distinguish between ca cert for ssl and pki!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            verifycerts= settings.PKI['path_to_ca_cert'] 
        else:
            verifycerts=False
        
    else:   
        protocol='http://'
        verifycerts=False
            
    url=protocol+settings.PKI['host']+":"+str(settings.PKI['port'])+apiurl
    
    logger.debug('making %s request to pki %s',callType,url)
    username= settings.PKI['user']
    password= settings.PKI['password']
    
    headers = {'User-agent': 'Mozilla/5.0'}
    
    s = Session()
    req = Request(callType,url,data=json.dumps(data),headers=headers,auth=(username,password))
    prepped = s.prepare_request(req)
    
    # if we have Client Cert use it
    if (os.path.isfile(pathToClientCert)):
        cert=pathToClientCert
    else:
        cert=None
        
    result = s.send(prepped,verify=verifycerts,cert=cert)
    logger.info("status code received %s" , result.status_code)
    
        
    return result  

def callPKI(apiurl,data,callType):

        
    if settings.PKI['use_ssl']:
        protocol='https://'
        if settings.PKI['verify_certs']:
            #TO DO   need to distinguish between ca cert for ssl and pki!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            verifycerts= settings.PKI['path_to_ca_cert'] 
        else:
            verifycerts=False
        
    else:   
        protocol='http://'
        verifycerts=False
            
    url=protocol+settings.PKI['host']+":"+str(settings.PKI['port'])+apiurl
    
    logger.debug('making %s request to pki %s',callType,url)
    username= settings.PKI['user']
    password= settings.PKI['password']
    
    headers = {'Accept': 'application/json',
                   'Content-Type' : 'application/json','User-agent': 'Mozilla/5.0'}
    
    s = Session()
    req = Request(callType,  url, data=json.dumps(data), headers=headers, auth=(username,password))

    prepped = s.prepare_request(req)
    result = s.send(prepped,verify=verifycerts,)

    logger.info("status code received %s" , result.status_code)
    
    try:
        logger.debug('pki response %s',result.json())
    except:
        logger.debug('pki no json received')
    return result



def test_certificate():
    #check access to test page gives good result
    #the test page could also be used as signal to revoke all previous certificates for user (to do)
    #copy temporary file to definitive certificate file
    return True
