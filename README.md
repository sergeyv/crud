General Overview of `crud`
--------------------------

Crud is a Pyramid app/library inspired by the Django automatic admin app.
:mod:`crud` allows to register an SQLAlchemy model with it and quickly get a basic
CRUD interface to create, list, edit and delete instances of that model.

Unlike the Django admin, which is essentially flat, crud allows to define
a hierarchical tree-like structure based on the relations defined in the
SQLAlchemy models, so the resulting application more resembles Zope's ZMI
with 'folderish' and 'contentish' objects.

For example, the home screen of an application may list some Courses,
when clicking on a course a user will get a list of Students enrolled to that course,
so the URL to access a Student will look like `/courses/123/students/234`.

This makes crud useful not only as a standalone 'backend' app, but also as a tool
to quickly build a tree-like structure of nested 'folderish' and 'contentish' objects
to which we can attach some views etc.

The two main concepts of crud are Resources and Collections.

Resource is a wrapper around a single SQLAlchemy object, which is dynamically
created during the URL traversal. Resource class contains all the logic necessary
to display a SA-mapped object in crud, so the model itself need not to be subclassed
off any special class - it's just plain SQLAlchemy model::

    @crud.resource(models.Book)
    class BookResource(crud.Resource):
        pass

Collection is a "virtual" folder-like thing which has no representation
in the database. In the simplest case, a Collection can act as a leaf node
in the URL graph, in which case we can use it to, say, attach a template::

    class DocsCollection(crud.Collection):
        pass

    @view_config(context=DocsCollection, name="page1")
    def page1_view(context, request):
        return "Hello, I'm page 1!"

    @view_config(context=DocsCollection, name="page2")
    def page2_view(context, request):
        return "Hello, I'm page 2"

Alternatively, a Collection can act as a folder for Resources::

    class CoursesCollection(crud.Collection):
        subitems_source = models.Course

The above code will create a collection, subitems of which will be instances of Course class. There are two possible uses of
the subitems_source property: if we provide a class, the collection will contain all objects of that class. Alternatively,
if we provide a string and if our collection is a sub-collection of some Resource, it'll look for a relationship attribute
defined on the model of that Resource and use it as a source of its subitems::

    @crud.resource(model.Course)
    class CourseResource(crud.Resource):
        subsections = {
        'students': StudentsCollection("Students enrolled to this course", "students")
        }

Finally, we need to register one collection as a root collection, from which URL traversal will start::

    class RootCollection(crud.Collection):
        subsections = {
        'courses' : CoursesCollection("Courses"),
        'docs': DocsCollection("Static documentation"),
        'books': crud.Collection("We don't have to subclass it", subitems_source=models.Book),
        }

To make crud aware of the hierarchy we've built, we register the root collection::

    crud.crud_init(RootCollection, DBSession)
