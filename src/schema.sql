create table users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    username            TEXT NOT NULL,
    hashed_password     TEXT NOT NULL,
    UNIQUE(username)
);

create table login_keys (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	timestamp		    INTEGER NOT NULL,
	key			        TEXT NOT NULL
);

create table devices (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id			    INTEGER NOT NULL,
	name			    TEXT NOT NULL,
	device_key		    TEXT NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id, name)
);

create table device_fields (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    field_index         INTEGER NOT NULL,
    field_name          TEXT NOT NULL,
    field_type          INTEGER NOT NULL,
    device_id           INTEGER NOT NULL,
    FOREIGN KEY(device_id) REFERENCES devices(id),
    UNIQUE(field_index, device_id),
    UNIQUE(field_name, device_id)
);

create table samples (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	device_id		    INTEGER NOT NULL,
	timestamp		    INTEGER NOT NULL,
	data                BLOB NOT NULL,
	FOREIGN KEY(device_id) REFERENCES devices(id)
);
