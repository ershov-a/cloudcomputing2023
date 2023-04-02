DROP DATABASE IF EXISTS `botdb`;
CREATE DATABASE `botdb`;
USE `botdb`;
DROP TABLE IF EXISTS `stats`;
CREATE TABLE `stats` (
  `command` varchar(100) NOT NULL,
  `usecount` INT
);
INSERT INTO stats (command, usecount) VALUES ('weather', 0);
INSERT INTO stats (command, usecount) VALUES ('currencies', 0);
INSERT INTO stats (command, usecount) VALUES ('news', 0);
INSERT INTO stats (command, usecount) VALUES ('brief', 0);
INSERT INTO stats (command, usecount) VALUES ('feedback', 0);
INSERT INTO stats (command, usecount) VALUES ('mock', 0);