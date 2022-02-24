
create table devices (
    DEVICE_ID   integer     not null,
    NAME        text        not null,
    PRIMARY KEY(DEVICE_ID)
);

create table samples (
    ID          text        not null,
    NUM         integer     not null,
    DEVICE_ID   integer     not null,
    TIME        integer     not null,
    TIME_MICRO  integer     not null,
    CURRENT     real        not null,
    VOLTAGE     real        not null,
    PRIMARY KEY(ID),
    FOREIGN KEY(DEVICE_ID) REFERENCES devices(DEVICE_ID)
);
