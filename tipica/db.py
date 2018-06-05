#!/usr/bin/env python

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext import declarative
from sqlalchemy.orm import collections
from sqlalchemy.orm import exc as sa_exc

from tipica import config


_MAKER = None
_ENGINE = None


def get_engine(sql_conn=config.CFG['sql_connection']):
    global _ENGINE

    if _ENGINE is None:
        _ENGINE = sa.create_engine(sql_conn)
        try:
            _ENGINE.connect()
        except Exception as e:
            Exception("Failed to get session to DB backend: %s" % e)
            raise

    return _ENGINE


def get_session(sql_conn=config.CFG['sql_connection']):
    global _MAKER
    global _ENGINE

    if _MAKER is None:
        if _ENGINE is None:
            get_engine(sql_conn)
        _MAKER = sa.orm.sessionmaker(bind=_ENGINE, autoflush=True)

    return _MAKER()


class ModelBase(object):

    def add(self, session):
        session.add(self)
        session.commit()
        return self

    def update(self, session, values):
        for k, v in values.iteritems():
            setattr(self, k, v)
        session.add(self)
        session.commit()
        return self

    def delete(self, session):
        session.delete(self)
        session.commit()

    def to_dict(self, excludes=[]):
        d = {}
        tn = self.__tablename__
        model_names = [tn, tn.rstrip('s'), (tn.rstrip('s') + '_ref')]
        next_excludes = excludes + model_names
        for p in self.__mapper__.iterate_properties:
            k = p.key
            v = getattr(self, k)
            #print "@%s   k %s v %s %s" % (self.__tablename__, k, v, type(v))
            if k in model_names:
                continue
            elif k in excludes:
                continue
            elif k in self.__table__.columns:
                d[k] = v
            elif hasattr(v, "to_dict"):
                d[k] = v.to_dict(next_excludes)
            elif isinstance(v, collections.InstrumentedList):
                d[k] = [i.to_dict(next_excludes) for i in v]
            else:
                d[k] = None
                #raise Exception("Unkown key [%s] in %s" % (k, self))
        return d


DB_DEC = declarative.declarative_base(cls=ModelBase)


class UserModel(DB_DEC):
    __tablename__ = 'users'
    name = sa.Column(sa.String(36), primary_key=True)


class ImageModel(DB_DEC):
    __tablename__ = 'images'
    name = sa.Column(sa.String(36), primary_key=True)
    user_name = sa.Column(sa.String(36))
    user_pass = sa.Column(sa.String(36))
    description = sa.Column(sa.String(255))


class NodeModel(DB_DEC):
    __tablename__ = 'nodes'
    name = sa.Column(sa.String(36), primary_key=True)
    mgmt_type = sa.Column(sa.String(36))
    mgmt_account = sa.Column(sa.String(36))
    mgmt_password = sa.Column(sa.String(36))
    user = sa.Column(
        sa.String(36), sa.ForeignKey('users.name'))
    user_ref = orm.relationship(
        UserModel,
        backref=orm.backref('nodes', lazy='joined'))
    image = sa.Column(
        sa.String(36), sa.ForeignKey('images.name'))
    image_ref = orm.relationship(
        ImageModel,
        backref=orm.backref('nodes', lazy='joined'))
    description = sa.Column(sa.String(255))


MODEL_MAP = {
    'node': NodeModel,
    'image': ImageModel,
    'user': UserModel,
}


def initialize():
    engine = get_engine()
    DB_DEC.metadata.drop_all(engine)
    DB_DEC.metadata.create_all(engine)


def get(resource, name):
    session = get_session()
    query = session.query(MODEL_MAP[resource])
    try:
        obj = query.filter_by(name=name).one()
    except:
        raise Exception("%(r)s %(n)s could not be found." %
                        {'r': resource.title(), 'n': name})
    return obj.to_dict()


def list(resource, filters={}):
    session = get_session()
    query = session.query(MODEL_MAP[resource])
    ret = []
    for obj in query.filter_by(**filters).all():
        ret.append(obj.to_dict())
    return ret


def table(resource, filters={}):
    session = get_session()
    modelclass = MODEL_MAP[resource]
    query = session.query(modelclass)
    fields = [i.key for i in modelclass.__mapper__.iterate_properties
              if not i.key.endswith('_ref')]
    rows = []
    for obj in query.filter_by(**filters).all():
        o = obj.to_dict()
        r = {}
        for f in fields:
            i = o[f]
            if isinstance(i, __builtins__['list']):
                i = ' '.join([j.get('name') for j in i])
            r[f] = i
        rows.append(r)

    return (fields, rows)


def add(resource, **values):
    session = get_session()
    model = MODEL_MAP[resource](**values)
    try:
        entry = model.add(session)
    except:
        raise Exception("Failed to add %(r)s %(n)s (maybe duplicated name)." %
                        {'r': resource.title(), 'n': values.get('name')})
    return entry.to_dict()


def update(resource, name, **values):
    session = get_session()
    query = session.query(MODEL_MAP[resource])
    obj = query.filter_by(name=name).one()
    if obj:
        return obj.update(session, values).to_dict()
    else:
        values['name'] = name
        return add(resource, **values).to_dict()


def delete(resource, name):
    session = get_session()
    query = session.query(MODEL_MAP[resource])
    try:
        obj = query.filter_by(name=name).one()
        obj.delete(session)
    except sa_exc.NoResultFound:
        raise Exception("%(r)s %(n)s could not be found." %
                        {'r': resource.title(), 'n': name})
