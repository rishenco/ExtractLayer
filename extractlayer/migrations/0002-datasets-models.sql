CREATE TABLE IF NOT EXISTS extractlayer.models (
    id serial PRIMARY KEY,
    extractor_id integer NOT NULL REFERENCES extractlayer.extractors (id) ON DELETE CASCADE,
    specification jsonb NOT NULL,
    known_datasets integer[] NOT NULL DEFAULT '{}',
    archived_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS models_extractor_id ON extractlayer.models (extractor_id);

ALTER TABLE extractlayer.extractors
    ADD COLUMN IF NOT EXISTS specimen_model_id integer REFERENCES extractlayer.models (id),
    ADD COLUMN IF NOT EXISTS serving_model_id integer REFERENCES extractlayer.models (id);

CREATE TABLE IF NOT EXISTS extractlayer.datasets (
    id serial PRIMARY KEY,
    extractor_id integer NOT NULL REFERENCES extractlayer.extractors (id) ON DELETE CASCADE,
    name text NOT NULL,
    description text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS datasets_extractor_id ON extractlayer.datasets (extractor_id);

CREATE TABLE IF NOT EXISTS extractlayer.dataset_rows (
    id serial PRIMARY KEY,
    dataset_id integer NOT NULL REFERENCES extractlayer.datasets (id) ON DELETE CASCADE,
    "values" jsonb NOT NULL,
    source text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dataset_rows_dataset_id ON extractlayer.dataset_rows (dataset_id);
