from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Integer, ForeignKey, String

class Base(SQLModel, table=False):
    @classmethod
    def get_field_name(cls, ref) -> str:
        # noinspection PyTypeChecker
        for field_name in cls.model_fields:
            if getattr(cls, field_name) == ref:
                return field_name
        raise KeyError('Invalid field reference.')

class Account(Base, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='account_relation', cascade_delete=True)

class Gateway(Base, table=True):
    """Gateway configuration."""
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    account: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Account.__tablename__}.{Account.get_field_name(Account.id)}',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    account_relation: Account = Relationship(back_populates='gateways')
    devices: list['Device'] = Relationship(back_populates='gateway_relation', cascade_delete=True)

class Device(Base, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    gateway: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Gateway.__tablename__}.{Gateway.get_field_name(Gateway.id)}',
                ondelete="CASCADE"
            ),
            nullable =False
        )
    )

    gateway_relation: Gateway = Relationship(back_populates='devices')
    endpoints: list['Endpoint'] = Relationship(back_populates='device_relation',
                                               cascade_delete=True)

class Endpoint(Base, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    device: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Device.__tablename__}.{Device.get_field_name(Device.id)}',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    device_relation: Device = Relationship(back_populates='endpoints')

