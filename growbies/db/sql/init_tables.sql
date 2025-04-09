-- Account
CREATE TABLE IF NOT EXISTS account (
    name text PRIMARY KEY
);

-- Gateway
CREATE TABLE IF NOT EXISTS gateway (
    account_name text REFERENCES account ON DELETE CASCADE,
    name text PRIMARY KEY
);

-- Device
CREATE TABLE IF NOT EXISTS device (
    gateway_name text REFERENCES gateway ON DELETE CASCADE,
    name text PRIMARY KEY
);

-- Endpoint
CREATE TABLE IF NOT EXISTS endpoint (
    device_name text REFERENCES device ON DELETE CASCADE,
    name text PRIMARY KEY
);


--INSERT INTO account VALUES ('emey_account');
--INSERT INTO gateway values ('emey_account', 'emey_gateway');
--INSERT INTO device values ('emey_gateway', 'emey_device');
--INSERT INTO endpoint values ('emey_device', 'emey_endpoint');
--CREATE TABLE IF NOT EXISTS mass_fast_buffer (ts TIMESTAMP PRIMARY KEY, data0 float);
--CREATE TABLE IF NOT EXISTS mass_mid_buffer (ts TIMESTAMP PRIMARY KEY, data0 float);
--CREATE TABLE IF NOT EXISTS mass_slow_buffer (ts TIMESTAMP PRIMARY KEY, data0 float);
--
--ALTER TABLE mass_fast_buffer ADD data1 float;
--ALTER TABLE mass_mid_buffer ADD data1 float;
--ALTER TABLE mass_slow_buffer ADD data1 float;
--
--INSERT INTO mass_fast_buffer
--    VALUES ('2025-04-07T17:22:24.064929450Z', 1.23, 3.14);
--INSERT INTO mass_mid_buffer
--    VALUES ('2025-04-07T17:22:25.064929450Z', 1.23, 4.31);
--INSERT INTO mass_slow_buffer
--    VALUES ('2025-04-07T17:22:26.064929450Z', 1.23, 41.3);

