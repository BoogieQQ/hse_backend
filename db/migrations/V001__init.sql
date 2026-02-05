
CREATE TABLE users (
    seller_id INTEGER PRIMARY KEY,
    is_verified_seller BOOLEAN NOT NULL DEFAULT FALSE
);


CREATE TABLE advertisements (
    item_id INTEGER PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES users(seller_id) ON DELETE CASCADE,
    name VARCHAR(256) NOT NULL,
    description TEXT,
    category INTEGER NOT NULL,
    images_qty INTEGER NOT NULL DEFAULT 0
);