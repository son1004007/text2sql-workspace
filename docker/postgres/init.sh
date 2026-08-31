#!/bin/sh
set -eu

: "${ANALYTICS_READER_PASSWORD:?ANALYTICS_READER_PASSWORD is required}"

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=ON_ERROR_STOP=1 \
  --set=reader_password="$ANALYTICS_READER_PASSWORD" <<'SQL'
CREATE ROLE analytics_reader LOGIN PASSWORD :'reader_password';
ALTER ROLE analytics_reader SET default_transaction_read_only = on;
ALTER ROLE analytics_reader SET statement_timeout = '1000ms';

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO analytics_reader;
GRANT CONNECT ON DATABASE analytics TO analytics_reader;

CREATE TABLE customers (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    order_month TEXT NOT NULL
);

CREATE TABLE order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DOUBLE PRECISION NOT NULL
);

INSERT INTO customers(id, name) VALUES
    (1, 'Acme'),
    (2, 'Bravo');

INSERT INTO products(id, name, category) VALUES
    (1, 'Notebook', 'office'),
    (2, 'Monitor', 'electronics'),
    (3, 'Keyboard', 'electronics');

INSERT INTO orders(id, customer_id, order_month) VALUES
    (1, 1, '2026-01'),
    (2, 2, '2026-01'),
    (3, 1, '2026-02');

INSERT INTO order_items(id, order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 2, 5.0),
    (2, 1, 2, 1, 200.0),
    (3, 2, 3, 2, 80.0),
    (4, 3, 2, 2, 200.0);

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_reader;
SQL
