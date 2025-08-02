from sqlmodel import create_engine, SQLModel

from . import constants

def init_tables():
    # All imported SQLModels with table=True metadata will be created as tables in the database
    # noinspection PyUnresolvedReferences
    from growbies.db import models
    engine = create_engine(constants.SQLMODEL_LOCAL_ADDRESS, echo_pool=True)
    SQLModel.metadata.create_all(engine)
