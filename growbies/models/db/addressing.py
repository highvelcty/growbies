from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Integer, ForeignKey, String


class Account(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='account_relation', cascade_delete=True)

class Gateway(SQLModel, table=True):
    """Gateway configuration."""
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    account: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Account.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    account_relation: Account = Relationship(back_populates='gateways')
    devices: list['Device'] = Relationship(back_populates='gateway_relation', cascade_delete=True)

class Device(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    gateway: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Gateway.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable =False
        )
    )

    gateway_relation: Gateway = Relationship(back_populates='devices')
    endpoints: list['Endpoint'] = Relationship(back_populates='device_relation',
                                               cascade_delete=True)

class Endpoint(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    device: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Device.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    device_relation: Device = Relationship(back_populates='endpoints')

