import unittest

from pyramid.testing import cleanUp

from crud import Collection

class ModelURLTests(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()
        
    def _callFUT(self, model, request, *elements, **kw):
        from pyramid.url import model_url
        return model_url(model, request, *elements, **kw)

    def _registerContextURL(self):
        from pyramid.interfaces import IContextURL
        from zope.interface import Interface
        from zope.component import getSiteManager
        class DummyContextURL(object):
            def __init__(self, context, request):
                pass
            def __call__(self):
                return 'http://example.com/'
        sm = getSiteManager()
        sm.registerAdapter(DummyContextURL, (Interface, Interface),
                           IContextURL)

    def test_root_default(self):
        #self._registerContextURL()
        
        
        about_section = Collection(
            "About", 
            subsections = {
           'one' : Collection('Page One!'),
           'two' : Collection('A folder!',
                subsections = {
                    'uno' : Collection("Uno!"),
                    'duo' : Collection("Duo!"),
                })
            }
        )

        root = Collection(
            "Kelpie!",
            subsections = dict(
                about = about_section 
                )
        )

        request = DummyRequest()
        about = about_section.with_parent(root, 'about')
        one = about.subsections['one'].with_parent(about,'one')
        result = self._callFUT(about_section, request)
        self.assertEqual(result, 'http://example.com/')

        
class DummyRequest:
    application_url = 'http://example.com:5432' # app_url never ends with slash
    def __init__(self, environ=None):
        if environ is None:
            environ = {}
        self.environ = environ

