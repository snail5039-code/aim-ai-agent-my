SELECT * FROM country;
SELECT name, continent from country;

SELECT country.name, country.continent FROM country;

SELECT c.name, c.continent FROM country as c;

SELECT 
    c.name as 국가명, 
    c.continent as 대륙명 
FROM country as c;

SELECT 
    c.name 국가명, 
    c.continent 대륙명 
FROM country c;

SELECT DISTINCT continent FROM country;

