-- CRM/SaaS core schema initial migration.
-- Generated to establish base tables, indexes, and partitioning strategies.

-- Enable useful extensions for UUID generation and case-insensitive text handling.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Users table stores application accounts with role-based access.
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    email         CITEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    role          VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'manager', 'user', 'service'))
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique_idx
    ON users (email);

-- Campaigns table represents marketing campaigns.
CREATE TABLE IF NOT EXISTS campaigns (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    type        VARCHAR(50) NOT NULL,
    status      VARCHAR(30) NOT NULL DEFAULT 'draft',
    start_date  DATE,
    end_date    DATE,
    budget      NUMERIC(14,2),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT campaigns_status_check CHECK (status IN ('draft', 'running', 'paused', 'completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS campaigns_status_start_idx
    ON campaigns (status, start_date);

-- Contacts capture CRM customer data. search_vector supports full text queries.
CREATE TABLE IF NOT EXISTS contacts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    name           TEXT NOT NULL,
    email          TEXT,
    phone          TEXT,
    company        TEXT,
    address_line1  TEXT,
    address_line2  TEXT,
    city           TEXT,
    state_region   TEXT,
    postal_code    TEXT,
    country        TEXT,
    tags           TEXT[] DEFAULT '{}',
    notes          TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    search_vector  tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(email, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(phone, '')), 'C')
    ) STORED
);

-- Ensure unique contacts by email or phone where provided.
CREATE UNIQUE INDEX IF NOT EXISTS contacts_unique_email_idx
    ON contacts (lower(email))
    WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS contacts_unique_phone_idx
    ON contacts (phone)
    WHERE phone IS NOT NULL;

CREATE INDEX IF NOT EXISTS contacts_owner_idx
    ON contacts (owner_id);

CREATE INDEX IF NOT EXISTS contacts_search_vector_idx
    ON contacts USING GIN (search_vector);

-- Leads connect marketing contacts to pipeline stages.
CREATE TABLE IF NOT EXISTS leads (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id     UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    source         VARCHAR(100),
    status         VARCHAR(50) NOT NULL DEFAULT 'new',
    campaign_id    UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    owner_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    details        JSONB DEFAULT '{}'::JSONB,
    estimated_value NUMERIC(14,2),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ,
    last_contacted_at TIMESTAMPTZ,
    CONSTRAINT leads_status_check CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'lost'))
);

CREATE INDEX IF NOT EXISTS leads_contact_idx
    ON leads (contact_id);

CREATE INDEX IF NOT EXISTS leads_status_created_idx
    ON leads (status, created_at DESC);

CREATE INDEX IF NOT EXISTS leads_campaign_idx
    ON leads (campaign_id);

-- Junction table for associating leads with campaigns and tracking engagement.
CREATE TABLE IF NOT EXISTS lead_campaigns (
    lead_id      UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id  UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    engagement_status VARCHAR(30) DEFAULT 'pending',
    engaged_at   TIMESTAMPTZ,
    PRIMARY KEY (lead_id, campaign_id)
);

CREATE INDEX IF NOT EXISTS lead_campaigns_status_idx
    ON lead_campaigns (engagement_status);

-- Interactions store timeline of communications.
CREATE TABLE IF NOT EXISTS interactions (
    id                 BIGSERIAL PRIMARY KEY,
    contact_id         UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    associated_lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    interaction_type   VARCHAR(30) NOT NULL,
    channel            VARCHAR(100),
    subject            TEXT,
    content            TEXT,
    metadata           JSONB,
    occurred_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_read            BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS interactions_contact_occurred_idx
    ON interactions (contact_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS interactions_lead_idx
    ON interactions (associated_lead_id);

-- Partial index for unread interactions to power inbox-like views.
CREATE INDEX IF NOT EXISTS interactions_unread_idx
    ON interactions (contact_id, occurred_at DESC)
    WHERE is_read = FALSE;

-- Appointments manage scheduling with contacts.
CREATE TABLE IF NOT EXISTS appointments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id      UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    owner_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    location        TEXT,
    status          VARCHAR(30) NOT NULL DEFAULT 'scheduled',
    start_datetime  TIMESTAMPTZ NOT NULL,
    end_datetime    TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ,
    CONSTRAINT appointments_status_check CHECK (status IN ('scheduled', 'completed', 'canceled')),
    CONSTRAINT appointments_time_check CHECK (end_datetime > start_datetime)
);

CREATE INDEX IF NOT EXISTS appointments_contact_idx
    ON appointments (contact_id, start_datetime);

CREATE INDEX IF NOT EXISTS appointments_status_idx
    ON appointments (status);

-- Email templates for outbound communication.
CREATE TABLE IF NOT EXISTS email_templates (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    subject     TEXT NOT NULL,
    body        TEXT NOT NULL,
    created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS email_templates_creator_idx
    ON email_templates (created_by);

-- Webhook logs capture third-party payloads for observability.
CREATE TABLE IF NOT EXISTS webhook_logs (
    id             BIGSERIAL PRIMARY KEY,
    source         VARCHAR(100) NOT NULL,
    payload        JSONB NOT NULL,
    received_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed      BOOLEAN NOT NULL DEFAULT FALSE,
    status_code    INTEGER,
    error_message  TEXT
);

CREATE INDEX IF NOT EXISTS webhook_logs_received_idx
    ON webhook_logs (received_at DESC);

CREATE INDEX IF NOT EXISTS webhook_logs_processed_idx
    ON webhook_logs (processed) WHERE processed = FALSE;

-- Task logs are partitioned to handle high ingestion volumes.
CREATE TABLE IF NOT EXISTS task_logs (
    id            BIGINT GENERATED ALWAYS AS IDENTITY,
    task_name     VARCHAR(150) NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    status        VARCHAR(40) NOT NULL,
    detail        TEXT,
    PRIMARY KEY (id, started_at)
)
PARTITION BY RANGE (started_at);

-- Default partition ensures we do not lose records while waiting for monthly partitions.
CREATE TABLE IF NOT EXISTS task_logs_default
    PARTITION OF task_logs DEFAULT;

-- Example monthly partition for January 2025.
CREATE TABLE IF NOT EXISTS task_logs_2025_01
    PARTITION OF task_logs
    FOR VALUES FROM ('2025-01-01T00:00:00Z') TO ('2025-02-01T00:00:00Z');

CREATE INDEX IF NOT EXISTS task_logs_status_idx
    ON task_logs (status);

-- Page audits track SEO crawl outcomes. A unique constraint prevents duplicate audits per URL/date.
CREATE TABLE IF NOT EXISTS page_audits (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    audit_date  TIMESTAMPTZ NOT NULL,
    summary     TEXT,
    score       INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ,
    CONSTRAINT page_audits_unique_daily UNIQUE (url, audit_date)
);

CREATE INDEX IF NOT EXISTS page_audits_url_date_idx
    ON page_audits (url, audit_date DESC);

-- Audit issues attach detailed findings to audits.
CREATE TABLE IF NOT EXISTS audit_issues (
    id           BIGSERIAL PRIMARY KEY,
    audit_id     BIGINT NOT NULL REFERENCES page_audits(id) ON DELETE CASCADE,
    description  TEXT NOT NULL,
    severity     VARCHAR(30) NOT NULL,
    resolved     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS audit_issues_audit_idx
    ON audit_issues (audit_id, severity);

CREATE INDEX IF NOT EXISTS audit_issues_resolved_idx
    ON audit_issues (resolved) WHERE resolved = FALSE;

-- Change log captures AI suggested modifications requiring review.
CREATE TABLE IF NOT EXISTS change_log (
    id          BIGSERIAL PRIMARY KEY,
    module      VARCHAR(100) NOT NULL,
    change_type VARCHAR(100) NOT NULL,
    details     TEXT,
    status      VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ,
    CONSTRAINT change_log_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'applied'))
);

CREATE INDEX IF NOT EXISTS change_log_status_idx
    ON change_log (status, created_at DESC);

-- Content drafts and version history support collaborative authoring.
CREATE TABLE IF NOT EXISTS content_drafts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    content     TEXT,
    author_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    source      VARCHAR(30) NOT NULL DEFAULT 'human',
    status      VARCHAR(30) NOT NULL DEFAULT 'draft',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS content_drafts_status_idx
    ON content_drafts (status, created_at DESC);

CREATE TABLE IF NOT EXISTS content_versions (
    id           BIGSERIAL PRIMARY KEY,
    draft_id     UUID NOT NULL REFERENCES content_drafts(id) ON DELETE CASCADE,
    version_num  INTEGER NOT NULL,
    content      TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by   UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT content_versions_unique_version UNIQUE (draft_id, version_num)
);

CREATE INDEX IF NOT EXISTS content_versions_draft_idx
    ON content_versions (draft_id, created_at DESC);

-- Additional indexes to optimize joins and filters.
CREATE INDEX IF NOT EXISTS appointments_owner_idx
    ON appointments (owner_id);

CREATE INDEX IF NOT EXISTS leads_owner_idx
    ON leads (owner_id);

CREATE INDEX IF NOT EXISTS content_drafts_author_idx
    ON content_drafts (author_id);

-- Future high-volume SERP or analytics tables should follow the partitioning
-- pattern demonstrated in task_logs to maintain manageable index sizes.
