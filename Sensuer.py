import sys, json
from botocore.vendored import requests

#Python Class to allow python to send Sensu check statuses to Sensu API.

class sensuer:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def createCheck(self, checkName, address, environment, cName, output, code, subscriptions=['default']):
        clientConfig = {
            'name':cName,
            'address':address,
            'environment':environment,
            'subscriptions':subscriptions
        }
        checkConfig = {
            'source':cName,
            'name':checkName,
            'output':output,
            "handlers": [''],
            "standalone": "true",
            "occurrences":3,
            "interval":60,
            "refresh":60,
            'status':code
        }
        headers = {'Content-Type': 'application/json'}
        serverUrl = 'https://sensu.api.endpoint.com/'

        response = requests.post(serverUrl + 'results', data=json.dumps(checkConfig), auth=(self.user, self.password),
                                 headers=headers)
        if response.status_code != 202:
            print('failed to send result of check to sensu server, status code = %d' % (response.status_code,))
            sys.exit(1)
