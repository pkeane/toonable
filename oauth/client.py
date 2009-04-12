import httplib
import oauth
import urllib

class SimpleOAuthClient(oauth.OAuthClient):

    def __init__(self, server, port=httplib.HTTP_PORT, request_token_url='',
                 access_token_url='', authorization_url=''):
        self.server = server
        self.port = port
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))

    def fetch_request_token(self, oauth_request):
        self.connection.request(oauth_request.http_method,oauth_request.to_url()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def fetch_access_token(self, oauth_request):
        self.connection.request(oauth_request.http_method,oauth_request.to_url()) 
        response = self.connection.getresponse()
        print response.read()
        exit()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.read()

    def access_resource(self, oauth_request):
        # via post body
        # -> some protected resources
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        self.connection.request('POST', RESOURCE_URL, body=oauth_request.to_postdata(), headers=headers)
        response = self.connection.getresponse()
        return response.read()

