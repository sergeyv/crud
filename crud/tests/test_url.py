import unittest

from repoze.bfg.testing import cleanUp

from crud import Section

class ModelURLTests(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()
        
    def _callFUT(self, model, request, *elements, **kw):
        from repoze.bfg.url import model_url
        return model_url(model, request, *elements, **kw)

    def _registerContextURL(self):
        from repoze.bfg.interfaces import IContextURL
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
        
        
        about_section = Section(
            "About", 
            subsections = {
           'one' : Section('Page One!'),
           'two' : Section('A folder!',
                subsections = {
                    'uno' : Section("Uno!"),
                    'duo' : Section("Duo!"),
                })
            }
        )

        root = Section(
            "Kelpie!",
            subsections = dict(
                about = about_section 
                )
        )

        request = DummyRequest()
        about = about_section.with_parent(root, 'about')
        one = about.subsections['one'].with_parent(about,'one')
        result = self._callFUT(about_section, request)
        print "GOT RESULT: %s" % result
        self.assertEqual(result, 'http://example.com/')

        
class DummyRequest:
    application_url = 'http://example.com:5432' # app_url never ends with slash
    def __init__(self, environ=None):
        if environ is None:
            environ = {}
        self.environ = environ

