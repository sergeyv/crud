# -*- coding: utf-8 -*-
##########################################
#     This file forms part of CRUD
#     Copyright: refer to COPYRIGHT.txt
#     License: refer to LICENSE.txt
##########################################


from pyramid.renderers import render_to_response

from webob.exc import HTTPFound
from crud.models import DBSession


from crud.views.theme import Theme


def index(context, request):
    # context is a Collection object here
    theme = Theme(context, request)

    return render_to_response('templates/index.pt',
                  value=dict(
                    context=context,
                    request=request,
                    theme=theme,
                    )
                 )


def view(context, request):
    #context is Resource here
    theme = Theme(context, request)

    return render_to_response('templates/view.pt',
                   value=dict(
                     context=context,
                     form=context.form_factory.readonly_form(context),
                     request=request,
                     theme=theme,
                     )
                  )


def edit(context, request):
    # context is Resource here
    theme = Theme(context, request)
    #fs = FieldSet(context.model)
    import schemaish
    import formish
    schema = schemaish.Structure()
    schema.add('title', schemaish.String())
    form = formish.Form(schema, 'form')
    #form.addAction(save, 'Save')
    #form.addAction(add, 'Cancel')

    #form['title'].widget = formish.Input(strip=True)
    form['title'].default = "Hello!"
    return render_to_response('templates/edit.pt',
                  value=dict(
                      context=context,
                      theme=theme,
                      form=context.form_factory.edit_form(context),
                      request=request,
                      )
                 )


def add(context, request):
    # context is Collection here
    theme = Theme(context, request)
    dbsession = DBSession()
    resource = context.create_subitem(wrap=True)

    form = resource.form_factory.add_form(context, dbsession)

    return render_to_response('templates/add.pt',
                  value=dict(
                      instance=resource.model,
                      theme=theme,
                      form=form,
                      context=context,
                      request=request,
                      )
                 )


def save(context, request):
    success_url = request.path_url.rpartition('/')[0] + '/'
    failure_url = request.path_url.rpartition('/')[0] + '/edit'

    instance = context.model

    if 'form.button.cancel' in request.params:
        return HTTPFound(location=success_url)

    dbsession = DBSession()
    success = context.form_factory.save(
        model=instance,
        data=request.params,
        session=dbsession)
    if success:
        return HTTPFound(location=success_url)
    return HTTPFound(location=failure_url)


def save_new(context, request):
    success_url = request.path_url.rpartition('/')[0] + '/'
    failure_url = request.path_url.rpartition('/')[0] + '/edit'

    if 'form.button.cancel' in request.params:
        return HTTPFound(location=success_url)
    resource = context.create_subitem(wrap=True)
    dbsession = DBSession()
    success = resource.form_factory.save(model=resource.model, data=request.params, session=dbsession)
    if success:
        dbsession.add(resource.model)
        return HTTPFound(location=success_url)
    return HTTPFound(location=failure_url)


def delete(context, request):
    success_url = context.parent_url(request)
    theme = Theme(context, request)

    if 'form.button.cancel' in request.params:
        return HTTPFound(location=success_url)
    if 'form.button.confirm_delete' in request.params:
        #dbsession = DBSession()
        #dbsession.delete(context.model)
        context.delete_item(request)

        return HTTPFound(location=success_url)
    return render_to_response('templates/delete.pt',
                  value=dict(
                      instance=context.model,
                      context=context,
                      request=request,
                      theme=theme,
                      )
                 )

