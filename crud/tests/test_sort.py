# -*- coding: utf-8 -*-

import sqlalchemy as sa
import schemaish as sc

import crud
from crud.models import DBSession

from crud.tests import Base

from nose.tools import raises

session = None

# Our test models

class Country(Base):
    __tablename__ = "countries"
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String)

class School(Base):
    __tablename__ = "schools"
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String)
    established = sa.Column(sa.String)
    country_id = sa.Column(sa.Integer, sa.ForeignKey("countries.id"))
    country = sa.orm.relationship(Country, backref="schools")

class Student(Base):
    __tablename__ = "students"
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String)
    school_id = sa.Column(sa.Integer, sa.ForeignKey("schools.id"))
    school = sa.orm.relationship(School, backref="students")



@crud.resource(School)
class SchoolResource(crud.Resource):
    pass


@crud.resource(Student)
class StudentResource(crud.Resource):
    pass

class SchoolsCollection(crud.Collection):
    subitems_source = School

class StudentsCollection(crud.Collection):
    subitems_source = Student

class RestRootCollection(crud.Collection):
    """
    """

    subsections = {
        'schools' : SchoolsCollection,
        'students' : StudentsCollection,
    }





def setUp():
    global session
    session = crud.models.DBSession
    pass


def tearDown():
    crud.models.DBSession.rollback()



def test_add_students():
    """
    Serialize an object and see if it contains the values
    """
    mzb = Country(name="Mozambique")
    zbv = Country(name="Zimbabwe")

    school_x = School(name = "X", established = "1930", country=mzb)
    school_y = School(name = "Y", established = "1950", country=zbv)
    session.add(school_x)
    session.add(school_y)
    session.add(Student(name = "C", school = school_x))
    session.add(Student(name = "A", school = school_x))
    session.add(Student(name = "B", school = school_y))
    session.add(Student(name = "D"))
    session.add(Student(name = "E"))
    session.flush()

    students = session.query(Student).all()
    assert len(students) == 5

    #session.rollback()


def test_adhoc_collections():
    """
    Create some on-the fly collections and see if they work
    """


    coll = crud.Collection(title="Schools", subitems_source=School)
    schools = coll.get_items()
    assert len(schools) == 2

    coll = crud.Collection(title="Students", subitems_source=Student)
    students = coll.get_items()
    assert len(students) == 5

def test_adhoc_simple_sort():
    """
    Sort students by name
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="name")
    students = coll.get_items()
    assert len(students) == 5
    assert students[0].model.name == "A"
    assert students[1].model.name == "B"
    assert students[2].model.name == "C"

def test_adhoc_simple_sort_desc():
    """
    Sort students by name desc
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="-name")
    students = coll.get_items()
    assert len(students) == 5
    assert students[0].model.name == "E"
    assert students[1].model.name == "D"
    assert students[2].model.name == "C"
    assert students[3].model.name == "B"
    assert students[4].model.name == "A"

@raises(AttributeError)
def test_sort_missing_attr():
    """
    Sort students by name desc
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="last_name")
    students = coll.get_items()

@raises(AttributeError)
def test_sort_missing_attr_desc():
    """
    Sort students by name desc
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="-last_name")
    students = coll.get_items()

@raises(AttributeError)
def test_sort_relationship():
    """
    Sort students by name desc
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="school")
    students = coll.get_items()

def test_sort_relationship_attr():
    """
    Sort students by relationship attribute
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="school.name")
    students = coll.get_items()
    assert len(students) == 5
    assert students[0].model.school is None
    assert students[1].model.school is None
    assert students[2].model.school.name == "X"
    assert students[3].model.school.name == "X"
    assert students[4].model.school.name == "Y"

def test_sort_relationship_attr_desc():
    """
    Sort students by relationship attribute desc
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="-school.name")
    students = coll.get_items()
    assert len(students) == 5
    assert students[0].model.school.name == "Y"
    assert students[1].model.school.name == "X"
    assert students[2].model.school.name == "X"
    assert students[3].model.school is None
    assert students[4].model.school is None

@raises(AttributeError)
def test_sort_relationship_missingattr():
    """
    Sort students by a missing relationship attribute
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="school.school_name")
    students = coll.get_items()

def test_sort_relationship_nested():
    """
    Sort students by "nested" relationship attribute
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="school.country.name")
    students = coll.get_items()
    assert len(students) == 5
    assert students[0].model.school is None
    assert students[1].model.school is None
    assert students[2].model.school.country.name == "Mozambique"
    assert students[3].model.school.country.name == "Mozambique"
    assert students[4].model.school.country.name == "Zimbabwe"

def test_sort_relationship_nested_desc():
    """
    Sort students by "nested" relationship attribute desc
    """
    coll = crud.Collection(title="Students", subitems_source=Student, order_by="-school.country.name")
    students = coll.get_items()
    assert len(students) == 5
    assert students[0].model.school.country.name == "Zimbabwe"
    assert students[1].model.school.country.name == "Mozambique"
    assert students[2].model.school.country.name == "Mozambique"
    assert students[3].model.school is None
    assert students[4].model.school is None
