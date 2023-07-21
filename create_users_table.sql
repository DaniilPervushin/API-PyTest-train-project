/*CREATE TABLE `users` (
  `id` INT NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `username` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `phone` varchar(16) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);
  
ALTER TABLE `users`
 MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;*/
 
 
CREATE TABLE `users` (
	`id` INT PRIMARY KEY AUTO_INCREMENT,
 	`email` varchar(255) NOT NULL UNIQUE,
    `password` varchar(255) NOT NULL,
    `username` varchar(255) NULL UNIQUE,
    `name`  varchar(255) NULL,
    `phone`  varchar(16) NULL,
    `is_admin` bool default false,
    UNIQUE(`email`, `username`)
    ) ENGINE = InnoDB DEFAULT CHARSET=utf8mb4;