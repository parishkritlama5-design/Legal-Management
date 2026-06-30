-- =============================================================================
-- 01_create_tables.sql
-- Legal Case Management Intelligence Platform - Schema (DDL)
-- Dialect: PostgreSQL 13+  (ANSI-friendly; notes inline for other engines)
-- -----------------------------------------------------------------------------
-- Star-ish operational model:
--   Dimensions : clients, attorneys, case_managers
--   Core fact  : cases  (one row per matter; carries denormalized operational
--                        metrics used by the dashboards & ML feature store)
--   Sub-facts  : activities, documents, medical_records, settlements, call_logs
-- =============================================================================

DROP TABLE IF EXISTS call_logs        CASCADE;
DROP TABLE IF EXISTS settlements      CASCADE;
DROP TABLE IF EXISTS medical_records  CASCADE;
DROP TABLE IF EXISTS documents        CASCADE;
DROP TABLE IF EXISTS activities       CASCADE;
DROP TABLE IF EXISTS cases            CASCADE;
DROP TABLE IF EXISTS case_managers    CASCADE;
DROP TABLE IF EXISTS attorneys        CASCADE;
DROP TABLE IF EXISTS clients          CASCADE;

-- -----------------------------------------------------------------------------
-- Dimension: clients
-- -----------------------------------------------------------------------------
CREATE TABLE clients (
    client_id         VARCHAR(12)  PRIMARY KEY,
    first_name        VARCHAR(60),
    last_name         VARCHAR(60),
    date_of_birth     DATE,
    gender            VARCHAR(2),
    state             CHAR(2),
    phone             VARCHAR(20),
    email             VARCHAR(120),          -- nullable: ~3% missing by design
    intake_date       DATE         NOT NULL,
    referral_source   VARCHAR(40),           -- nullable: ~2% missing by design
    marketing_channel VARCHAR(30)
);

-- -----------------------------------------------------------------------------
-- Dimension: attorneys
-- -----------------------------------------------------------------------------
CREATE TABLE attorneys (
    attorney_id       VARCHAR(12)  PRIMARY KEY,
    attorney_name     VARCHAR(120),
    bar_state         CHAR(2),
    specialty         VARCHAR(40),
    years_experience  INTEGER,
    hire_date         DATE
);

-- -----------------------------------------------------------------------------
-- Dimension: case_managers
-- -----------------------------------------------------------------------------
CREATE TABLE case_managers (
    case_manager_id   VARCHAR(12)  PRIMARY KEY,
    manager_name      VARCHAR(120),
    team              VARCHAR(40),
    hire_date         DATE,
    monthly_capacity  INTEGER                 -- target matters worked / month
);

-- -----------------------------------------------------------------------------
-- Core fact: cases
-- -----------------------------------------------------------------------------
CREATE TABLE cases (
    case_id                  VARCHAR(14)  PRIMARY KEY,
    client_id                VARCHAR(12)  NOT NULL REFERENCES clients(client_id),
    case_type                VARCHAR(40),
    state                    CHAR(2),
    intake_date              DATE,
    date_opened              DATE,
    date_closed              DATE,                 -- NULL while case is open
    case_status              VARCHAR(30),
    current_stage            VARCHAR(30),          -- workup funnel stage
    assigned_case_manager    VARCHAR(12)  REFERENCES case_managers(case_manager_id),
    attorney_id              VARCHAR(12)  REFERENCES attorneys(attorney_id),
    days_in_stage            INTEGER,
    medical_records_received SMALLINT,             -- 1 = at least one record in
    missing_documents        SMALLINT,             -- count outstanding docs
    communication_count      INTEGER,              -- touchpoints to date
    workup_completed         SMALLINT,             -- 1 = reached "Workup Complete"+
    case_outcome             VARCHAR(20),
    settlement_amount        NUMERIC(14,2),        -- NULL unless settled
    workup_completed_date    DATE,                 -- date reached Workup Complete (NULL if not)
    last_activity_date       DATE
);

CREATE INDEX idx_cases_cm        ON cases(assigned_case_manager);
CREATE INDEX idx_cases_attorney  ON cases(attorney_id);
CREATE INDEX idx_cases_status    ON cases(case_status);
CREATE INDEX idx_cases_stage     ON cases(current_stage);
CREATE INDEX idx_cases_intake    ON cases(intake_date);

-- -----------------------------------------------------------------------------
-- Sub-fact: activities  (case-manager touchpoints / time tracking)
-- -----------------------------------------------------------------------------
CREATE TABLE activities (
    activity_id       VARCHAR(14)  PRIMARY KEY,
    case_id           VARCHAR(14)  NOT NULL REFERENCES cases(case_id),
    case_manager_id   VARCHAR(12)  REFERENCES case_managers(case_manager_id),
    activity_type     VARCHAR(40),
    activity_date     DATE,
    duration_minutes  INTEGER
);
CREATE INDEX idx_act_case ON activities(case_id);
CREATE INDEX idx_act_cm   ON activities(case_manager_id);

-- -----------------------------------------------------------------------------
-- Sub-fact: documents
-- -----------------------------------------------------------------------------
CREATE TABLE documents (
    document_id       VARCHAR(14)  PRIMARY KEY,
    case_id           VARCHAR(14)  NOT NULL REFERENCES cases(case_id),
    document_type     VARCHAR(40),
    status            VARCHAR(15),            -- Received | Missing | Pending
    requested_date    DATE,
    received_date     DATE
);
CREATE INDEX idx_doc_case ON documents(case_id);

-- -----------------------------------------------------------------------------
-- Sub-fact: medical_records
-- -----------------------------------------------------------------------------
CREATE TABLE medical_records (
    record_id         VARCHAR(14)  PRIMARY KEY,
    case_id           VARCHAR(14)  NOT NULL REFERENCES cases(case_id),
    provider_name     VARCHAR(80),
    requested_date    DATE,
    received_date     DATE,
    status            VARCHAR(15),            -- Received | Outstanding
    num_pages         INTEGER
);
CREATE INDEX idx_mr_case ON medical_records(case_id);

-- -----------------------------------------------------------------------------
-- Sub-fact: settlements
-- -----------------------------------------------------------------------------
CREATE TABLE settlements (
    settlement_id     VARCHAR(12)  PRIMARY KEY,
    case_id           VARCHAR(14)  NOT NULL REFERENCES cases(case_id),
    settlement_amount NUMERIC(14,2),
    settlement_date   DATE,
    attorney_fee      NUMERIC(14,2),
    lien_amount       NUMERIC(14,2),
    case_costs        NUMERIC(14,2),
    net_to_client     NUMERIC(14,2)
);
CREATE INDEX idx_set_case ON settlements(case_id);

-- -----------------------------------------------------------------------------
-- Sub-fact: call_logs
-- -----------------------------------------------------------------------------
CREATE TABLE call_logs (
    call_id           VARCHAR(14)  PRIMARY KEY,
    case_id           VARCHAR(14)  REFERENCES cases(case_id),
    client_id         VARCHAR(12)  REFERENCES clients(client_id),
    case_manager_id   VARCHAR(12)  REFERENCES case_managers(case_manager_id),
    call_date         DATE,
    direction         VARCHAR(10),            -- Inbound | Outbound
    duration_seconds  INTEGER,
    outcome           VARCHAR(30)
);
CREATE INDEX idx_call_case ON call_logs(case_id);
CREATE INDEX idx_call_cm   ON call_logs(case_manager_id);

-- =============================================================================
-- End of schema
-- =============================================================================
