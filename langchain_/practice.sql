-- Active: 1791764239204@@127.0.0.1@5432@postgres

GRANT CONNECT ON DATABASE postgres TO agent_reader;
GRANT USAGE ON SCHEMA public TO agent_reader;

GRANT SELECT ON users, purchases, inquiries TO agent_reader;

GRANT INSERT ON inquiries TO agent_reader;

GRANT USAGE, SELECT ON SEQUENCE inquiries_inquiry_id_seq TO agent_reader;

DROP TABLE IF EXISTS inquiries;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS users;

CREATE DATABASE wiki_rag;


CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    product_name VARCHAR(100) NOT NULL,
    product_category VARCHAR(50),
    quantity INTEGER NOT NULL DEFAULT 1,
    price INTEGER NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    purchased_at TIMESTAMP NOT NULL
);

CREATE TABLE inquiries (
    inquiry_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    purchase_id INTEGER REFERENCES purchases(purchase_id),
    inquiry_type VARCHAR(30) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT '접수',
    created_at TIMESTAMP DEFAULT now()
);

INSERT INTO users (name, email, phone) VALUES
('김철수', 'chulsoo@example.com', '010-1111-1111'),
('이영희', 'younghee@example.com', '010-2222-2222'),
('박민수', 'minsoo@example.com', '010-3333-3333');

INSERT INTO purchases (user_id, product_name, product_category, quantity, price, order_status, purchased_at) VALUES
(1, '기계식 키보드', '전자기기', 1, 89000, '배송중', '2026-10-05 14:20:00'),
(1, '무선 키보드', '전자기기', 1, 59000, '배송완료', '2026-09-28 10:15:00'),
(1, '게이밍 마우스', '전자기기', 1, 45000, '배송완료', '2026-10-01 16:40:00'),
(2, '블루투스 이어폰', '전자기기', 1, 129000, '배송중', '2026-10-06 09:30:00'),
(2, '노트북 파우치', '잡화', 1, 25000, '배송완료', '2026-09-25 11:00:00'),
(3, 'USB-C 충전기', '전자기기', 2, 38000, '결제완료', '2026-10-07 18:10:00');

INSERT INTO inquiries (user_id, purchase_id, inquiry_type, content, status) VALUES
(1, 2, '배송', '무선 키보드 배송 완료라고 나오는데 아직 못 받았습니다.', '접수'),
(2, 4, '배송', '블루투스 이어폰 배송이 언제 도착하나요?', '처리중'),
(3, NULL, '일반', '회원 정보 수정은 어디서 하나요?', '접수');