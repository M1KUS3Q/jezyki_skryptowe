-- ===========================================================================
-- GTFS timetable database - raw DDL (Task 1a)
-- ===========================================================================
-- Schema must match the ORM models in lista10.models exactly.
-- Foreign keys enforce referential integrity: you must load data in the
-- correct order (stops, routes, calendar -> trips -> stop_times).

CREATE TABLE IF NOT EXISTS stops (
    stop_id   TEXT PRIMARY KEY NOT NULL,
    stop_code TEXT NOT NULL,
    stop_name TEXT NOT NULL,
    stop_lat  REAL NOT NULL,
    stop_lon  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS routes (
    route_id         TEXT PRIMARY KEY NOT NULL,
    agency_id        TEXT NOT NULL,
    route_short_name TEXT NOT NULL,
    route_long_name  TEXT NOT NULL,
    route_desc       TEXT,
    route_type       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar (
    service_id TEXT PRIMARY KEY NOT NULL,
    monday     INTEGER NOT NULL DEFAULT 0,
    tuesday    INTEGER NOT NULL DEFAULT 0,
    wednesday  INTEGER NOT NULL DEFAULT 0,
    thursday   INTEGER NOT NULL DEFAULT 0,
    friday     INTEGER NOT NULL DEFAULT 0,
    saturday   INTEGER NOT NULL DEFAULT 0,
    sunday     INTEGER NOT NULL DEFAULT 0,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id      TEXT PRIMARY KEY NOT NULL,
    route_id     TEXT NOT NULL,
    service_id   TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    FOREIGN KEY (route_id)   REFERENCES routes(route_id),
    FOREIGN KEY (service_id) REFERENCES calendar(service_id)
);

CREATE TABLE IF NOT EXISTS stop_times (
    trip_id        TEXT NOT NULL,
    arrival_time   TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    stop_id        TEXT NOT NULL,
    stop_sequence  INTEGER NOT NULL,
    PRIMARY KEY (trip_id, stop_sequence),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);
