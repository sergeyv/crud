##########################################
#     This file forms part of CRUD
#     Copyright: refer to COPYRIGHT.txt
#     License: refer to LICENSE.txt
##########################################


from pyramid.security import authenticated_userid
from pyramid.renderers import get_renderer


class Theme(object):

    def __init__(self, context, request, page_title=None):
        self.context = context
        self.request = request
        self.page_title = page_title

    layout_fn = 'templates/layout.pt'
    @property
    def layout(self):
        macro_template = get_renderer(self.layout_fn).implementation()
        return macro_template

    @property
    def logged_in_user_id(self):
        """
        Returns the ID of the current user
        """
        return authenticated_userid(self.request)
