import requests
import mimetypes
import base64
import sys
import copy
import os
# import the standard JSON parser
import json
# import the REST library
import warnings
warnings.filterwarnings("ignore")

import urllib.parse
import logging
import configparser


class P3RESTAPI():
    def __init__(self):

        self.config = configparser.ConfigParser()

        #os.path.join(os.path.abspath(os.path.dirname(__file__)), 'conf', 'config.cfg')
        self.config.read(__file__[:-2] + 'ini')
        
        self.session = requests.Session()        

        if self.config['P3'].getboolean('test'):
            logging.info('TEST environment')            
            self.session.cert = (self.config['P3']['certificate_test'],self.config['P3']['private_key_test'])
            self.uri = self.config['P3']['p3_uri_test']
        else:
            logging.info('Production environment')
            self.session.cert = (self.config['P3']['certificate_production'],self.config['P3']['private_key_production'])
            self.uri = self.config['P3']['p3_uri_production']
        logging.warning('P3 uri: %s' % self.uri)                        
            
        self.session.verify = False
        self.session.keep_alive = False # prova per i continui drop

        self.headers = {'content-type': 'application/json',
                        'CODE_ADM':self.config['P3']['code_adm']}
        self.auth_token = None


    def pretty_print_POST(self,req):
        """
        At this point it is completely built and ready
        to be fired; it is "prepared".
        
        However pay attention at the formatting used in 
        this function because it is programmed to be pretty 
        printed and may differ from the actual request.
        """
        logging.debug('\n{}\n{}\n{}\n\n{}\n{}'.format(
            '-----------  REQUEST DUMP  -----------',
            req.method + ' ' + req.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
            '-----------END REQUEST DUMP-----------',            
        ))
        
    def CallAction(self,action, data, http_method='POST'):
        data_to_print = copy.deepcopy(data)

        if 'Document' in data_to_print:
            if 'MainDocument' in data_to_print['Document']:
                if 'Content' in data_to_print['Document']['MainDocument']:
                    if data_to_print['Document']['MainDocument']['Content'] != None:
                        data_to_print['Document']['MainDocument']['Content'] = data_to_print['Document']['MainDocument']['Content'][:300] + '....<skip file content>'
                        
        if 'File' in data_to_print:
            if 'Content' in data_to_print['File']:
                data_to_print['File']['Content'] =  data_to_print['File']['Content'][:300] + '....<skip file content>'

        logging.info('ACTION %s method [%s]' % (action, http_method))
        logging.info('data: %s' % (data_to_print))

        headers = self.headers

        if self.auth_token:
            headers['AuthToken']=self.auth_token
        headers['ROUTED_ACTION']=action

        json_data = json.dumps(data)
     
        if http_method == 'GET':
            r = requests.Request(method=http_method,url=self.uri, params=data, headers = headers)
        else:
            r = requests.Request(method=http_method,url=self.uri, data=json_data, headers = headers)

        prepared_r = self.session.prepare_request(r)
        self.pretty_print_POST(prepared_r)
        r=self.session.send(prepared_r)

        if not r.ok:
            logging.warning('Connectin error on ACTION %s method [%s], Response status code: %d, reason: %s' % (action, http_method, r.status_code, r.reason))	
            logging.debug('Connection error: %s' % r.text)
            return None
        ret_data = json.loads(r.text)

        if 'Code' in ret_data:
            if(ret_data['Code']==0) and ret_data['ErrorMessage'] == None:
                return ret_data
            else:
                logging.error('Error: %s' % ret_data)
                logging.error('data: %s' % (data_to_print))
                return None
        else:
            logging.error('Uh! something went wrong! Error: %s' % ret_data)
            return None                
        
    def Authenticate(self, username = None):
        # di default imort rubrica cosi in caso di errore si puo cancellare e ricreare
        data = { 'CodeApplication': self.config['P3']['code_application'],
                 "CodeAdm":self.config['P3']['code_adm']}
        
        if username == None:
            if self.config['P3'].getboolean('import_rubrica'):
                user = self.config['P3']['username_correspondents']
#                data['CodeRole'] =  self.config['P3']['rda_correspondents']
            else:
                user = self.config['P3']['username_protocols']
#                data['CodeRole'] =  self.config['P3']['rda_protocols']
        else:
            user = username

        data['Username']=user
                           
        ret = self.CallAction('GetToken',data)
        logging.info("Username: %s" % data['Username'])

        if not ret:
            logging.error('Authentication error')
            return False 
        self.auth_token=ret['Token']
        return True

        
      
    def GetDocument(self,id_doc, getfile=False, withsignature="0"):      
        data  = {"IdDocument": id_doc , "GetFile": getfile, "GetFileWithSignature" : withsignature}
        ret = self.CallAction('GetDocument',data)
        
        logging.info("IdDocument: %s" % data['IdDocument'])

        return(ret)


    def GetFileDocumentById(self, id_doc,signed=False):
        data  = {"IdDocument": id_doc}
        if signed:
            data['VersionId']='SIGNED'

        ret = self.CallAction('GetFileDocumentById',data, http_method='GET')
        
        logging.info("IdDocument: %s" % data['IdDocument'])
 
        return(ret)
    

    def EditDocument(self, document, register=None):
        if not register:
            register=self.config['P3']['default_register']
            
        data = {'Document':document,
                'CodeRegister':register}
        ret = self.CallAction('EditDocument',data,'POST')
        print(document)
        logging.info("IdDocument: %s" % document['Id'])
        return(ret)

    def CreateDocument(self, document, register=None):
        if not register:
            register=self.config['P3']['default_register']

        
        data = {'Document':document,
                'CodeRegister':register}
        
        ret = self.CallAction('CreateDocument',data,'PUT')
        logging.info("IdDocument: %s" % data['Document']['Object'])        

        return(ret)
    
    def CreateDocumentAndAddInProject(self, document, register=None, codeProject='1', classificationSchemeId=None):
        if not register:
            register=self.config['P3']['default_register']

        
        data = {'Document':document,
                'CodeRegister':register,
                'CodeProject':codeProject, 
                'ClassificationSchemeId':classificationSchemeId}
        
        ret = self.CallAction('CreateDocumentAndAddInProject',data,'PUT')
        logging.info("IdDocument: %s" % data['Document']['Object'])        

        return(ret)
    

    def ImportPreviousDocument(self,document,register=None):
        if not register:
            register=self.config['P3']['default_register']
        
        data = {'CodeRegister': register,
                'Document': document}

        logging.warning(data)        
        ret = self.CallAction('ImportPreviousDocument',data,'PUT')
        logging.info("ProtocolNumber: %s Object: %s" % (data['Document']['ProtocolNumber'], data['Document']['Object']))

        return(ret)

    def ExecuteTransmissionDocument(self,transmission):
        data = transmission

        ret = self.CallAction('ExecuteTransmissionDocument',data,'POST')
        logging.info("Receiver: %s" % data["Receiver"])

        return(ret)
    
    def SearchDocuments(self,filters):
        data = {}
        data['Filters']=[filters,]

        return(self.CallAction('SearchDocuments',data,'POST'))

    def GetModifiedDocuments(self,datefrom,dateto):
        data = {}
        data['dateFrom']=datefrom
        data['dateTo']=dateto
        data['security']='asd'
        data['allEvents']='true'
        data['modifiedOnly']='false'
        
        return(self.CallAction('GetModifiedDocuments',data,'GET'))        

    def UploadFileToDocument(self,filetoupload):
        data = filetoupload

        ret = self.CallAction('UploadFileToDocument',data,'PUT')

        logging.info('Filename %s' % filetoupload['File']['Name'])

        return(ret)        
    
    def GetCorrespondent(self,id_correspondent):
        data = {}
        data['IdCorrespondent']=id_correspondent

        ret=self.CallAction('GetCorrespondent',data,'GET')
        logging.info('IdCorrespondent %s' % id_correspondent)        
        return(ret['Correspondent'])

    def AddCorrespondent(self, correspondent):       
        data = { "Correspondent": correspondent }
        ret  =self.CallAction('AddCorrespondent',data,'PUT')

        logging.info('Correspondent id %s description %s ' % (correspondent['Description'], correspondent['Code']))        

        return(ret)

    def SearchCorrespondents(self,filters):
        data = {}
        data['Filters']=filters

        ret = self.CallAction('SearchCorrespondents',data,'POST')

        return(ret)

    def EditCorrespondent(self, correspondent):       
        data = { "Correspondent": correspondent }
        ret  =self.CallAction('EditCorrespondent',data,'POST')

        logging.info('Correspondent id %s description %s ' % (correspondent['Description'], correspondent['Code']))        

        return(ret)


    def GetActiveClassificationScheme(self):       
        data = {}
        ret = self.CallAction('GetActiveClassificationScheme',data,'GET')
        return(ret)

    def GetAllClassificationSchemes(self):       
        data = {}
        ret = self.CallAction('GetAllClassificationSchemes',data,'GET')
        return(ret)

    def GetProject(self,project):
        data = project
        ret = self.CallAction('GetProject',data,'GET')
        return(ret)

    def AddDocInProject(self,project):
        data = project
        ret = self.CallAction('AddDocInProject',data,'POST')
#        logging.info("Receiver: %s" % data["Receiver"])
        return(ret)


    
        
if __name__=="__main__":
    api = P3RESTAPI()
    if not api.Authenticate():
        logging.error("Error: Can't authenticate")
        sys.exit(1)

    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)
     
    
    test = [
#        'getdocument',
#        'getfiledocumentbyid',
#        'editdocument',
        'searchdocument'
#        'createdocument',
#        'getmodifieddocuments',
#        'addcorrespondent',
#        'getcorrespondent',        
#        'searchcorrespondent',
#        'editcorrespondent',        
#        'executetransmission',
#        'getactiveclassificationscheme',
#        'getallclassificationschemes',
#        'adddocinproject',
#        'getproject'
    ]        

    if 'getdocument' in test:
        #iddoc="79785989" # per il test
        iddoc="230054419" #per produzione    
        print(api.GetDocument(iddoc))

    if 'getfiledocumentbyid' in test:
        #iddoc="79785989" # per il test
        iddoc="230054419" #per produzione    
        print(api.GetFileDocumentById(iddoc, signed=True))


    if 'searchdocument' in test:                        
        filter = {'Name':'OBJECT','Value':'Oggetto'}
        print(api.SearchDocuments(filter))

    if 'editdocument' in test:
        document=api.GetDocument("79798660")['Document']
        document['LinkedDocuments']=[
            {'Id':79785964},
#            {'Id':79810046}
        ] 
        print('Editing %s: "%s"' % (document['DocNumber'], document['Object']))
        print(api.EditDocument(document))              

    if 'createdocument' in test:        
        filename = "test.pdf"
        document = {}
        document['Object']="Oggetto"
        document['DocumentType']="A"
        
        sender1 = {}      
        sender1['Description'] = "Nuovo corrispondente"
        sender1['CorrespondentType'] = "O"
        
        document['Sender']=sender1
        
        main_document = {}
        
        main_document['Name']=filename
        main_document['MimeType']=mimetypes.guess_type(filename)[0]
        
        f = open(filename,'rb')
        
        main_document['Content'] = base64.b64encode(f.read()).decode()
        
        document['MainDocument']=main_document
        
        newdoc = api.CreateDocument(document)
        print(newdoc['Document']['DocNumber'])
        print(api.GetDocument(newdoc['Document']['DocNumber']))


    if 'getmodifieddocuments' in test:
        from datetime import datetime, timedelta

        logging.warning('Getting last 30 days docs')
        now = datetime.now()
        yesterday = datetime.now() - timedelta(days=30)
        
        datefrom=urllib.parse.quote(yesterday.strftime("%d/%m/%Y"), safe='')
        dateto=urllib.parse.quote(now.strftime("%d/%m/%Y"), safe='')        
        docs = api.GetModifiedDocuments(datefrom,dateto)
        print(docs['TotalDocumentsNumber'])
#        for doc in docs['Documents']:
#            print(doc)
        
    if 'getcorrespondent' in test:                
#        print(api.GetCorrespondent("79798886"))
        print(api.GetCorrespondent("79771801"))


    if 'addcorrespondent' in test:                        
        correspondent = {"Description": "string",
                         "Code": "codice20",
                         "Type": "U",
                         "CodeRegisterOrRF": "C_H330",
                         "CorrespondentType": "P",
                         "PreferredChannel": "MAIL",
                         "Name": "Nome",
                         "Surname": "Cognome",
                         "Email": "1234567890",                     
                         "IsCommonAddress": False }
        
        print(api.AddCorrespondent(correspondent))

    if 'searchcorrespondent' in test:                        
        filters = [
                   {'Name':'OFFICES','Value':'TRUE'},
                   {'Name':'USERS','Value':'TRUE'},
#                   {'Name':'REGISTRY_OR_RF','Value':'C_H330'},
                   {'Name':'TYPE','Value':'GLOBAL'},
#                   {'Name':'DESCRIPTION','Value':'AGRARIA R'},
                   {'Name':'CODE','Value':'132313'},
#                   {'Name':'CODE','Value':'PAT-RFS120'},
                   {'Name': 'EXTENDED_SEARCH_NO_REG', 'Value':'TRUE'},
                   {'Name': 'COMMON_ADDRESSBOOK', 'Value':'TRUE'},
#                   {'Name':'EXACT_CODE','Value':'codice18'}
                   ]

        # per ricercare direttamente dal codice rubrica esatto [{'Name':'EXACT_CODE','Value':corr['code']},        
        
        print(api.SearchCorrespondents(filters))

    if 'editcorrespondent' in test:    
        filters = [
                   {'Name':'OFFICES','Value':'TRUE'},
                   {'Name':'USERS','Value':'TRUE'},
#                   {'Name':'REGISTRY_OR_RF','Value':'C_H330'},
                   {'Name':'TYPE','Value':'GLOBAL'},
#                   {'Name':'DESCRIPTION','Value':'Cognome N'},
                   {'Name':'CODE','Value':'codice18'},
#                   {'Name': 'EXTENDED_SEARCH_NO_REG', 'Value':'TRUE'},
#                   {'Name':'EXACT_CODE','Value':'codice18'}
                   ]
        
        result=api.SearchCorrespondents(filters)
        if not result['Correspondents']:
            print("Nessun risultato")
            quit()
        print(result['Correspondents'][0]['Id'])

#        correspondent=api.GetCorrespondent(result['Correspondents'][0]['Id'])
#        print(correspondent)

        correspondent['Id']=result['Correspondents'][0]['Id']
        correspondent['Code']=result['Correspondents'][0]['Code']
        correspondent['CorrespondentType']=result['Correspondents'][0]['CorrespondentType']

        correspondent['Name']="NuovoNomeOggi"
        correspondent['Email']="miamail@pec.it"
        print(api.EditCorrespondent(correspondent))



    if 'executetransmission' in test:                                
        transmission = {"IdDocument": "79785964",
                        "TransmissionReason": "CONOSCENZA",
#                        "Receiver": {"Id": "79787253",}, #ufficio 25 sindaco
                        "Receiver": {"Code": "25",}, #ufficio 25 sindaco                        
                        "Notify": True,
                        "TransmissionType": "S"
        }

        print(api.ExecuteTransmissionDocument(transmission))

    if 'getactiveclassificationscheme' in test:                
        print(api.GetActiveClassificationScheme())

    if 'getallclassificationschemes' in test:                
        print(api.GetAllClassificationSchemes())

    if 'getproject' in test:                                
        project = {"ClassificationSchemeId": "79787618",
                   "CodeProject": "2.1"
        }

        print(api.GetProject(project))


    if 'adddocinproject' in test:                                
        project = {
#                   "IdDocument": "79834923",
                   "IdDocument": "79832588",
                   "CodeProject": "1"
#                   "IdProject": "79787745"
        }

        print(api.AddDocInProject(project))

    if 'adddocinprojectcomplete' in test:     
        logging.info("ProtocolNumber: %s Object: %s" % (data['Document']['ProtocolNumber'], data['Document']['Object']))
        idtitolario=api.GetActiveClassificationScheme()
                           
        project = {"IdDocument": "79834923",
                   "IdProject": "79787745"
        }

        print(api.AddDocInProject(project))


