USE `delta-sigma-phi87`;

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES('09219d8dbb19') ON DUPLICATE KEY UPDATE version_num=VALUES(version_num);

CREATE TABLE IF NOT EXISTS settings (
    id INT NOT NULL AUTO_INCREMENT, 
    google_form_link VARCHAR(255) NOT NULL, 
    PRIMARY KEY (id)
);
INSERT INTO settings (id, google_form_link) VALUES(1,'https://docs.google.com/forms/d/e/1FAIpQLSeOjs5WVTtI2n2jXxi0duBsEUF10bR-UdW81gRtAvODBGL4Dw/viewform?usp=sf_link') ON DUPLICATE KEY UPDATE google_form_link=VALUES(google_form_link);

CREATE TABLE IF NOT EXISTS user (
    id INT NOT NULL AUTO_INCREMENT, 
    canCreateEvents BOOLEAN NOT NULL, 
    username VARCHAR(100) NOT NULL, 
    email VARCHAR(80) NOT NULL, 
    password_hash VARCHAR(200) NOT NULL, 
    is_admin BOOLEAN NOT NULL, 
    is_approved BOOLEAN NOT NULL, 
    profile_picture VARCHAR(150), 
    PRIMARY KEY (id), 
    UNIQUE (email), 
    UNIQUE (username)
);
INSERT INTO user (id, canCreateEvents, username, email, password_hash, is_admin, is_approved, profile_picture) VALUES
(1,1,'Joosh','joshuaoliver2021@gmail.com','pbkdf2:sha256:600000$RohlYpa03wFSV2sV$9c02414b773d3301df72c96ef3cfaf1b8b524313a591d492352a27235f858290',1,1,'DeltaSigmaPhiHouse.jpeg'),
(2,0,'Dummy','dummy@gmail.com','pbkdf2:sha256:600000$l2hk0HmQrOR2ydEy$6faf5cbe5af946f192edf6467d02ac321b01e23583c9343da810e95e71826272',0,1,'Joshua_Oliver_Photo.jpeg'),
(3,0,'Test','test@gmail.com','pbkdf2:sha256:600000$AcLEkzTCbYa9F4FP$df36a14f25c8b4094af1c5fd0bfc4508faed2969da61b40a9e6ae7900876fd3e',0,1,NULL),
(4,0,'BoogeyBoi','booger@gmail.com','pbkdf2:sha256:600000$33p8RQkZqnKuKTmC$4aecd30d5147c74e03bdcb5c9b8977ae1be91c7fa7b8f121ece1765366ab2eba',0,0,NULL),
(5,0,'goober','gooby@gmail.com','pbkdf2:sha256:600000$RLa8A4JRcMNisazp$d39f8c3c7944199e2e716f301705da7deff14c929998f3bece6725d9afa052a3',0,0,NULL),
(6,0,'nooby','nooby@gmail.com','pbkdf2:sha256:600000$y1q5p9BdInErrV75$83eb804e2f2ec161f75b4481d067b14a9f2d9974dbb7d97f77a1a6e34b5dd1d4',0,0,NULL),
(7,0,'neews','neews@gmail.com','pbkdf2:sha256:600000$GGDNHQxZsuFxXvKi$a5301bb9439b207c67868ab0ee2f511b6edd402889a5a166161903bb20b60fcd',0,0,NULL)
ON DUPLICATE KEY UPDATE username=VALUES(username), email=VALUES(email), password_hash=VALUES(password_hash), is_admin=VALUES(is_admin), is_approved=VALUES(is_approved), profile_picture=VALUES(profile_picture);

CREATE TABLE IF NOT EXISTS event (
    id INT NOT NULL AUTO_INCREMENT, 
    title VARCHAR(255) NOT NULL, 
    description TEXT, 
    start DATETIME NOT NULL, 
    end DATETIME NOT NULL, 
    creator_id INT NOT NULL, 
    event_type VARCHAR(50), 
    event_color VARCHAR(120), 
    PRIMARY KEY (id), 
    FOREIGN KEY (creator_id) REFERENCES user (id)
);
INSERT INTO event (id, title, description, start, end, creator_id, event_type, event_color) VALUES
(5,'df','sdf','2024-06-14 23:00:00','2024-06-14 23:30:00',1,'recruitment','#FFD700'),
(6,'new','sd','2024-06-15 22:00:00','2024-06-15 22:30:00',1,'programming','#8A2BE2'),
(7,'nwewed','wd','2024-06-15 23:30:00','2024-06-17 23:00:00',1,'brotherhood','#1E90FF'),
(8,'adsf','af','2024-06-16 23:00:00','2024-06-16 23:30:00',1,'brotherhood','#1E90FF')
ON DUPLICATE KEY UPDATE title=VALUES(title), description=VALUES(description), start=VALUES(start), end=VALUES(end), creator_id=VALUES(creator_id), event_type=VALUES(event_type), event_color=VALUES(event_color);

COMMIT;
