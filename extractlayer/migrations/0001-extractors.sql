CREATE SCHEMA IF NOT EXISTS extractlayer;

CREATE TABLE IF NOT EXISTS extractlayer.extractors (
    id serial PRIMARY KEY,
    name text NOT NULL,
    description text NOT NULL,
    schema jsonb NOT NULL,
    source_columns text[] NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
