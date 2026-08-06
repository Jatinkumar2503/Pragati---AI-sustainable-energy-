-- PRAGATI AI — TimescaleDB & PostgreSQL Production Schema
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry_type VARCHAR(128) NOT NULL,
    discom_state VARCHAR(64) DEFAULT 'Haryana',
    contract_demand_kva NUMERIC(10, 2) DEFAULT 1000.0,
    bee_pat_target_toe NUMERIC(10, 2) DEFAULT 500.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users & RBAC Table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(128),
    role VARCHAR(32) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Telemetry Hypertable
CREATE TABLE IF NOT EXISTS telemetry_logs (
    time TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    active_power_kw NUMERIC(10, 3) NOT NULL,
    reactive_lagging_kvarh NUMERIC(10, 3) DEFAULT 0.0,
    reactive_leading_kvarh NUMERIC(10, 3) DEFAULT 0.0,
    power_factor NUMERIC(5, 4) DEFAULT 0.90,
    grid_voltage_v NUMERIC(6, 2) DEFAULT 415.0,
    phase_current_r NUMERIC(8, 2) DEFAULT 0.0,
    phase_current_y NUMERIC(8, 2) DEFAULT 0.0,
    phase_current_b NUMERIC(8, 2) DEFAULT 0.0,
    transformer_temp_c NUMERIC(5, 2) DEFAULT 45.0,
    scope1_co2_kg NUMERIC(10, 4) DEFAULT 0.0,
    scope2_co2_kg NUMERIC(10, 4) DEFAULT 0.0,
    scope3_co2_kg NUMERIC(10, 4) DEFAULT 0.0,
    PRIMARY KEY (time, tenant_id, device_id)
);

-- Convert to TimescaleDB Hypertable partitioned by 1-day chunks
SELECT create_hypertable('telemetry_logs', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);
