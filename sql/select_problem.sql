-- 인구가 800만 이상인 도시의 name, population을 조회하시오
 SELECT city.name, city.population
 FROM city
 WHERE city.population >= 8000000;

-- 한국(KOR)에 있는 도시의 name, countrycode를 조회하시오
 SELECT name, countrycode
 FROM city
 WHERE countrycode = 'KOR';

SELECT * FROM country ;
-- 유럽 대륙에 속한 나라들의 name과 region을 조회하시오.
 SELECT country.name, country.region
 FROM country
 WHERE country.continent = 'Europe'; 

-- 이름이 'San'으로 시작하는 도시의 name을 조회하시오
SELECT name
 FROM city
 WHERE name LIKE 'San%';

-- 독립 연도(IndepYear)가 1901년 이상인 나라의 name, indepyear를 조회하시오.
 SELECT country.name, country.indepyear
 FROM country
 WHERE country.indepyear >= 1901;

-- 인구가 100만에서 200만 사이인 한국 도시의 name을 조회하시오
SELECT city.name
FROM city
WHERE city.population BETWEEN 1000000 AND 2000000 AND city.countrycode = 'KOR';

-- 인구가 500만 이상인 한국, 일본, 중국의 도시의 name, countrycode, population 을 조회하시오
SELECT city.name
FROM city
WHERE city.population >= 5000000 
AND city.countrycode IN ('KOR', 'JPN', 'CHN'); 

SELECT * FROM city;
-- 도시 이름이 'A'로 시작하고 'a'로 끝나는 도시의 name을 조회하시오.
SELECT city.name
FROM city
WHERE city.name LIKE 'A%a'; 


-- 동남아시아(Southeast Asia) 지역(Region)에 속하지 않는 아시아(Asia) 대륙 나라들의 name, region을 조회하시오.
SELECT country.name, country.region
FROM country
WHERE country.continent = 'Asia' AND country.region != 'Southeast Asia'; 

SELECT * FROM country;
-- 오세아니아 대륙에서 기대수명의 데이터가 없는 나라의 name, lifeexpectancy, continent를 조회하시오.
SELECT * FROM country;
SELECT name, lifeexpectancy, continent 
FROM country
WHERE continent = 'Oceania'
    AND lifeexpectancy IS NULL;

-- country 테이블에서 대륙별로 정렬하고, 같은 대륙 내에서는 GNP가 높은 순으로 정렬하여 name, continent, GNP를 조회하시오.
SELECT name, continent, gnp
FROM country
ORDER BY continent, gnp DESC;

SELECT * FROM country;

-- country 테이블에서 기대수명이 높은 순으로 정렬하되, NULL값은 마지막에 나오도록 정렬하여 name, lifeexpectancy를 조회하시오.
SELECT name, lifeexpectancy 
FROM country
ORDER BY lifeexpectancy DESC NULLS LAST;

-- city 테이블에서 인구수가 가장 적은 도시 5개를 조회하시오.
SELECT * FROM city
ORDER BY population
LIMIT 5;
 

-- country 테이블에서 면적(surfacearea)이 가장 넓은 순서대로 11위부터 20위까지의 국가를 조회하시오.
 SELECT * FROM country
 ORDER BY surfacearea DESC
 LIMIT 10 OFFSET 10;


-- country 테이블에서 기대수명이 높은 순서대로 1위부터 5위까지의 국가를 조회하시오.
SELECT name FROM country
ORDER BY lifeexpectancy DESC NULLS LAST
LIMIT 5;

-- 대륙별 총 인구수를 구하시오.
 SELECT continent, sum(population) 
 FROM country 
 GROUP BY continent;

-- 대륙별 평균 GNP와 평균 인구를 구하시오.
 SELECT continent, avg(gnp), avg(population) 
 FROM country
 GROUP BY continent;

-- 인구가 50만 이상 100만 이하인 도시들을 대상으로, CountryCode와 District별 도시 수를 구하시오.
SELECT countrycode, district, count(*)
FROM city
WHERE population >= 500000 AND population <= 10000000
GROUP BY countrycode, district;

-- 아시아 대륙 국가들의 Region별 총 GNP를 구하시오.
 SELECT region, sum(gnp) 
 FROM country
 WHERE continent = 'Asia'
 GROUP BY region;

-- 대륙별 국가 수가 많은 순서대로 Continent, 국가 수를 조회하시오.
 SELECT continent, count(*) 
 FROM country
 GROUP BY continent
 ORDER BY count(*) DESC;

-- 독립년도가 있는 국가들의 대륙별 평균 기대수명이 높은 순서대로 Continent, 평균 기대수명을 조회하시오.
 SELECT continent, avg(lifeexpectancy) 
 FROM country
 WHERE indepyear IS NOT NULL
 GROUP BY continent
 ORDER BY avg(lifeexpectancy) DESC;

-- Region별 총 GNP를 구하고, 총 GNP가 가장 높은 Region을 조회하시오. (GNP: 국민 총생산)
SELECT region, sum(gnp)
FROM country
GROUP BY region
ORDER BY sum(gnp) DESC
LIMIT 1;



-- 각 국가별 도시가 10개 이상인 국가의 CountryCode, 도시 수를 조회하시오.
 SELECT countrycode, count(*) 
 FROM city
 GROUP BY countrycode
 HAVING count(*) >= 10
 ORDER BY count(*) DESC; 

-- CountryCode와 District별로 집계하여, 평균 인구가 100만 이상이면서 도시 수가 3개 이상인 그룹의 CountryCode, District, 도시 수, 총 인구를 구하시오.
 SELECT countrycode, district, count(*), sum(population) 
 FROM city
 GROUP BY countrycode, district
 HAVING avg(population) >= 1000000 OR count(*) >= 3;

SELECT * FROM country;
-- 아시아 대륙의 국가들 중에서, Region별 평균 GNP가 1000 이상인 Region, 평균 GNP를 조회하시오.
 SELECT region, avg(gnp) 
 FROM country
 WHERE continent = 'Asia'
 GROUP BY region
 HAVING avg(gnp) >= 1000;

-- 독립년도가 1900년 이후인 국가들 중에서, 대륙별 평균 기대수명이 70세 이상인 Continent, 평균 기대수명을 조회하시오.
 SELECT continent, avg(lifeexpectancy) 
 FROM country
 WHERE indepyear >= 1900
 GROUP BY continent
 HAVING avg(lifeexpectancy) >= 70;

-- 도시 평균 인구가 100만 이상이고, 도시 최소 인구가 50만 이상인 국가의 CountryCode, 총 도시 수, 총 인구수를 조회하시오.
 SELECT countrycode, count(*), sum(population) 
 FROM city
 GROUP BY countrycode
 HAVING avg(population) >= 1000000 AND min(population) >= 500000;

-- 인구가 50만 이상인 도시만 대상으로 국가별로 집계하여, 평균 인구가 100만 이상인 국가의 CountryCode, 해당 도시 수, 해당 도시들의 인구 합계를 조회하시오.
SELECT countrycode, count(*), sum(population) 
FROM city
WHERE population >= 500000
GROUP BY countrycode
HAVING avg(population) >= 1000000;