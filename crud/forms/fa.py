# -*- coding: utf-8 -*-
from formalchemy import FieldSet

class FormAlchemyFormFactory(object):

    def readonly_form(self, proxy):
        """
        returns a read-only view of a model
        """
        # Exclude stuff we're displaying as subitems
        exclude = []
        # subitems_source can be a class or a str here
        # we're only interested in str, as it's the name
        # of an attribute
        for (key, ss) in proxy.subsections.items():
            exclude.append(ss.subitems_source)

        fs = FieldSet(proxy.model)
        include = []
        # render models's fields using FA
        # TODO: there's a way to set this on the form itself
        # rather than on individual fields
        for (k, field) in fs.render_fields.items():
            if k not in exclude:
                include.append(field.readonly())
            else:
                pass

        fs.configure(include=include)
        return fs.render()

    def edit_form(self, proxy):
        """
        returns an edit form for the model
        """
        fs = FieldSet(proxy.model)
        return fs.render()

    def add_form(self, proxy, dbsession):
        """
        returns an edit form for the model
        """

        fs = FieldSet(proxy.create_subitem(), session=dbsession)

        #
        # Make the foreign key fields read-only in the add form
        #
        # 1. If it's a str, we're inside a subsection filtered by
        # our parent
        if isinstance(proxy.subitems_source, str):
            parent_wrapper = proxy.parent_model()
            parent_instance = parent_wrapper.model
            relation_attr = getattr(parent_instance.__class__, proxy.subitems_source)
            child_attr_name = getattr(relation_attr.property.backref, 'key', None)
            if child_attr_name is not None:
                fs.render_fields[child_attr_name] = fs.render_fields[child_attr_name].hidden()

        return fs.render()

    def save(self, model, data, session):
        fs = FieldSet(model, session=session)
        fs.rebind(model, data=data)
        if fs.validate():
            fs.sync()
            return True
        #TODO: need to return validation result
        return False

