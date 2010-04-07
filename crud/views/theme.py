from repoze.bfg.security import authenticated_userid

from repoze.bfg.chameleon_zpt import get_template


class Theme(object):

    def __init__(self, context, request, page_title=None):
        self.context = context
        self.request = request
        self.page_title = page_title

    layout_fn = 'templates/layout.pt'
    @property
    def layout(self):
        macro_template = get_template(self.layout_fn)
        return macro_template

    @property
    def logged_in_user_id(self):
        """
        Returns the ID od the current user
        """
        return authenticated_userid(self.request)
