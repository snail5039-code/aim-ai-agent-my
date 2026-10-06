-- 실습
-- 모든 문제는 dvdrental 데이터베이스를 사용한다.

-- 고객의 이름과 대여일을 조회하시오.
SELECT r.rental_date, c.first_name
FROM rental as r
JOIN customer as c
on r.customer_id = c.customer_id;

-- 배우의 이름과 해당 배우가 출연한 영화의 제목을 조회하시오.
SELECT a.first_name, f.title  
FROM film as f
JOIN film_actor as fa
ON f.film_id = fa.film_id
JOIN actor as a
on fa.actor_id = a.actor_id;

-- first_name이 'Penelope'인 배우가 출연한 영화의 제목을 조회하시오.
SELECT a.first_name, f.title  
FROM film as f
JOIN film_actor as fa
ON f.film_id = fa.film_id
JOIN actor as a
on fa.actor_id = a.actor_id
WHERE first_name = 'Penelope';


-- 배우들이 출연한 영화의 등급을 중복 없이 조회하시오.
SELECT DISTINCT f.rating
FROM film AS f
JOIN film_actor AS fa
ON f.film_id = fa.film_id;

-- 배우별로 출연한 영화의 등급을 중복 없이 조회하시오. (배우 ID, 이름(first_name, last_name), 등급)
SELECT DISTINCT a.actor_id, a.first_name, a.last_name, f.rating 
FROM film as f
JOIN film_actor as fa
ON f.film_id = fa.film_id
JOIN actor as a
on fa.actor_id = a.actor_id;

-- 고객의 이름과 해당 고객이 대여한 영화의 제목을 조회하시오.
SELECT c.first_name, c.last_name, f.title
FROM customer AS c
JOIN rental AS r
ON c.customer_id = r.customer_id
JOIN inventory AS i
ON r.inventory_id = i.inventory_id
JOIN film AS f
ON i.film_id = f.film_id;

-- 'Yentl Idaho' 영화를 대여한 고객 정보를 중복 없이 조회하시오.
SELECT DISTINCT c.*
FROM customer AS c
JOIN rental AS r
ON c.customer_id = r.customer_id
JOIN inventory AS i
ON r.inventory_id = i.inventory_id
JOIN film AS f
ON i.film_id = f.film_id
WHERE f.title = 'Yentl Idaho';

-- 직원의 이름과 근무하는 매장의 주소, 도시를 조회하시오.
SELECT s.first_name, s.last_name, a.address, c.city
FROM staff AS s
JOIN store AS st
ON s.store_id = st.store_id
JOIN address AS a
ON st.address_id = a.address_id
JOIN city AS c
ON a.city_id = c.city_id;

-- 고객별로 대여한 영화의 제목, 지불한 금액, 대여일을 조회하시오.
SELECT c.customer_id, c.first_name, c.last_name, f.title, p.amount, r.rental_date
FROM customer AS c
JOIN rental AS r
ON c.customer_id = r.customer_id
JOIN inventory AS i
ON r.inventory_id = i.inventory_id
JOIN film AS f
ON i.film_id = f.film_id
JOIN payment AS p
ON r.rental_id = p.rental_id;

-- 'Action' 카테고리의 영화에 출연한 배우를 중복 없이 조회하시오.


-- 출연 배우가 있는 영화별로 배우 수를 조회하시오.


-- 출연 배우 수가 5명 초과인 영화와 배우 수를 배우 수 내림차순으로 정렬하여 조회하시오.


-- 카테고리별 평균 대여료를 조회하시오.


-- 고객이 있는 국가별로 고객 수를 조회하시오.


-- 고객 ID가 1인 고객이 가장 많이 대여한 영화의 카테고리를 조회하시오.


-- 재고(inventory)에 등록되지 않은 영화를 조회하시오.