
from repoze.bfg.chameleon_zpt import render_template_to_response as render
from repoze.bfg import traversal

from webob.exc import HTTPFound
from formalchemy import FieldSet
from crud.models import DBSession

from crud import IModel, ISection, ModelProxy

from crud.views.theme import Theme

def index(context,request):
    # context is a Section object here
    theme = Theme(context, request)
    
    return render('templates/index.pt',
                  context=context,
                  request = request,
                  theme = theme,
                 )
                                       
def view(context, request):
    #context is ModelProxy here
    theme = Theme(context, request)

    return render('templates/view.pt',
                   context = context,
                   form = context.form_factory.readonly_form(context),
                   request = request,
                   theme = theme,
                  )

def edit(context, request):
    # context is ModelProxy here
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
    return render('templates/edit.pt',
                  context = context,
                  theme=theme,
                  form = context.form_factory.edit_form(context),
                  request = request,
                 )

def add(context, request):
    # context is Section here
    theme = Theme(context, request)
    dbsession = DBSession()
    instance = context.create_subitem()
    proxy = context.wrap_child(name=None, model=instance)
    #fs = FieldSet(instance, session=dbsession)
    form = proxy.form_factory.add_form(context,dbsession)
    
    return render('templates/add.pt',
                  instance = instance,
                  theme = theme,
                  form = form,
                  context = context,
                  request = request,
                 )

def save(context, request):
    success_url = request.path_url.rpartition('/')[0]+ '/'
    failure_url = request.path_url.rpartition('/')[0] + '/edit'

    instance = context.model

    if 'form.button.cancel' in request.params:
        return HTTPFound(location=success_url)

    dbsession = DBSession()
    success = context.form_factory.save(model = instance, data=request.params, session=dbsession)
    if success:
        return HTTPFound(location=success_url)
    return HTTPFound(location=failure_url)

def save_new(context, request):
    success_url = request.path_url.rpartition('/')[0]+ '/'
    failure_url = request.path_url.rpartition('/')[0] + '/edit'

    if 'form.button.cancel' in request.params:
        return HTTPFound(location=success_url)
    instance = context.create_subitem()
    proxy = context.wrap_child(name=None, model=instance)
    dbsession = DBSession()
    #fs = FieldSet(instance, session=dbsession)
    #fs.rebind(instance, data=request.params)
    #if fs.validate(): 
    #    fs.sync()
    success = proxy.form_factory.save(model=instance, data=request.params, session=dbsession)
    if success:
        dbsession.add(instance)
        return HTTPFound(location=success_url)
    return HTTPFound(location=failure_url)
    
def delete(context, request):
    success_url = context.parent_url(request)
    theme = Theme(context, request)
        
    if 'form.button.cancel' in request.params:
        return HTTPFound(location=success_url)
    if 'form.button.confirm_delete' in request.params:
        dbsession = DBSession()
        dbsession.delete(context.model)
        return HTTPFound(location=success_url)
    return render('templates/delete.pt',
                  instance = context.model,
                  context = context,
                  request = request,
                  theme=theme,
                 )

