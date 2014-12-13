CREATE DATABASE test_database;

USE test_database;

CREATE TABLE test_entry(id INT NOT NULL AUTO_INCREMENT,
	title VARCHAR(100) NOT NULL,
   	gen_date DATE,
   	PRIMARY KEY ( id ));

INSERT INTO test_entry (title, gen_date) VALUES ('entry_1', '2012-7-04');
INSERT INTO test_entry (title, gen_date) VALUES ('entry_2', '2013-7-04');
INSERT INTO test_entry (title, gen_date) VALUES ('entry_3', CURDATE());
