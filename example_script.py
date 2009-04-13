from oauth import client
import time
import oauth.oauth as oauth 

def run_example():
    SERVER = 'www.google.com'
    PORT = 80
    REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
    ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'
    AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'
    CALLBACK_URL = 'http://toonable.appspot.com'
    RESOURCE_URL = 'https://mail.google.com/mail/feed/atom'
    SCOPE = 'https://mail.google.com/mail/feed/atom'
    CONSUMER_KEY = 'toonable.appspot.com'  
    CONSUMER_SECRET = 'NdT5Uuut1ze6HYyRfFa+J3i0'

    scope = {'scope':SCOPE}

    # setup
    print '** OAuth Python Library Example **'
    simple_client = client.SimpleOAuthClient(SERVER, PORT, REQUEST_TOKEN_URL,
                               ACCESS_TOKEN_URL, AUTHORIZATION_URL)
    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
    signature_method_plaintext = oauth.OAuthSignatureMethod_PLAINTEXT()
    signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()
    pause()

    # get request token
    print '* Obtain a request token ...'
    pause()
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
                                                               http_url=simple_client.request_token_url,parameters=scope)
    oauth_request.sign_request(signature_method_hmac_sha1, consumer, None)
    print 'REQUEST (via headers)'
    print 'parameters: %s' % str(oauth_request.parameters)
    pause()
    token = simple_client.fetch_request_token(oauth_request)
    print 'GOT'
    print 'key: %s' % str(token.key)
    print 'secret: %s' % str(token.secret)
    pause()

    print '* Authorize the request token ...'
    pause()
    oauth_request = oauth.OAuthRequest.from_token_and_callback(token=token, callback=CALLBACK_URL, http_url=simple_client.authorization_url)
    print 'REQUEST (via url query string)'
    print 'parameters: %s' % str(oauth_request.parameters)
    pause()
    # this will actually occur only on some callback
    response = simple_client.authorize_token(oauth_request)
    print 'GOT'
    print response
    pause()

    # get access token
    print '* Obtain an access token ...'
    pause()
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
                                                               token=token,
                                                               http_url=simple_client.access_token_url,parameters=scope)
    oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
    print 'REQUEST (via headers)'
    print 'parameters: %s' % str(oauth_request.parameters)
    pause()
    token = simple_client.fetch_access_token(oauth_request)
    print 'GOT'
    print 'key: %s' % str(token.key)
    print 'secret: %s' % str(token.secret)
    pause()

    # access some protected resources
    print '* Access protected resources ...'
    pause()
    parameters = {'file': 'vacation.jpg', 'size': 'original', 'oauth_callback': CALLBACK_URL} # resource specific params
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='POST', http_url=RESOURCE_URL, parameters=parameters)
    oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
    print 'REQUEST (via post body)'
    print 'parameters: %s' % str(oauth_request.parameters)
    pause()
    params = simple_client.access_resource(oauth_request)
    print 'GOT'
    print 'non-oauth parameters: %s' % params
    pause()

def pause():
    print ''
    time.sleep(1)

if __name__ == '__main__':
    run_example()
    print 'Done.'
