-- Active: 1791764239204@@127.0.0.1@5432@dvdrental
CREATE ROLE agent_reader LOGIN PASSWORD '1234';
GRANT CONNECT ON DATABASE dvdrental TO agent_reader;
GRANT USAGE ON SCHEMA public TO agent_reader;
GRANT SELECT ON actor, category, film, film_actor, film_category, "language"
TO agent_reader;

GRANT SELECT ON rental, inventory
TO agent_reader;