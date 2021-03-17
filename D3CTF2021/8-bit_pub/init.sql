DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `username` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

LOCK TABLES `users` WRITE;

INSERT INTO `users` VALUES ('admin','42718156440184983021777620573528');

UNLOCK TABLES;
