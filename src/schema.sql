create table users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    username            TEXT NOT NULL,
    hashed_password     TEXT NOT NULL,
);

create table login_keys (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	timestamp		    INTEGER NOT NULL,
	key			        TEXT NOT NULL
);

create table api_keys (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id			    INTEGER NOT NULL,
	key			        text NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id)
);

create table devices (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id			    INTEGER NOT NULL,
	name			    TEXT NOT NULL,
	device_key		    TEXT NOT NULL,
    structure           BLOB NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id)
);

create table samples (
	id			        INTEGER PRIMARY KEY AUTOINCREMENT,
	device_id		    INTEGER NOT NULL,
	timestamp		    INTEGER NOT NULL,
	data                BLOB NOT NULL,
	FOREIGN KEY(device_id) REFERENCES devices(id)
);
