create table login_keys (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	timestamp		INTEGER NOT NULL,
	key			TEXT NOT NULL
);

create table users (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	username		text NOT NULL,
	hashed_password 	text NOT NULL
);

create table api_keys (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id			INTEGER NOT NULL,
	key			text NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id)
);

create table devices (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id			INTEGER NOT NULL,
	name			text NOT NULL,
	device_key		text NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id)
);

create table device_fields (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	device_id		INTEGER NOT NULL,
	field_id		INTEGER NOT NULL,
	field			text NOT NULL,
	FOREIGN KEY(device_id) REFERENCES devices(id)
);

create table samples (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	device_id		INTEGER NOT NULL,
	timestamp		INTEGER NOT NULL,
	voltage			REAL NOT NULL,
	current			REAL NOT NULL,
	FOREIGN KEY(device_id) REFERENCES devices(id)
);
