from sqlmodel import Field, Relationship, SQLModel

class Base(SQLModel, table=False):
    @classmethod
    def get_field_name(cls, ref) -> str:

        # noinspection PyTypeChecker
        # Eric Meyer: false positive
        #   pycharm 2025.1.3.1 and sqlmodel 0.0.24
        for field_name in cls.model_fields:
            if getattr(cls, field_name) == ref:
                return field_name
        raise KeyError('Invalid field reference.')

class Account(Base, table=True):
    name: str = Field(primary_key=True)
    gateways: list['Gateway'] = Relationship(back_populates='gateway', cascade_delete=True)

class Gateway(Base, table=True):
    account_name: str = Field(foreign_key=f'{Account.__tablename__}.'
                                          f'{Account.get_field_name(Account.name)}')
    name: str = Field(primary_key=True)
    account: Account = Relationship(back_populates=Account.__tablename__)

class Device(Base, table=True):
    gateway_name: str = Field(foreign_key=f'{Gateway.__tablename__}.'
                                          f'{Gateway.get_field_name(Gateway.name)}')
    name: str = Field(primary_key=True)

class Endpoint(Base, table=True):
    device_name: str = Field(foreign_key=f'{Device.__tablename__}.'
                                         f'{Device.get_field_name(Device.name)}')
    name: str = Field(primary_key=True)

assert (Gateway.__tablename__ == Account.gateways.prop.back_populates)
