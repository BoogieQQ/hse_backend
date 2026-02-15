CREATE TABLE moderation_results (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES advertisements(item_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_violation BOOLEAN,
    probability FLOAT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
