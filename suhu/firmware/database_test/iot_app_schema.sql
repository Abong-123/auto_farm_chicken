--
-- PostgreSQL database dump
--

\restrict f0YP3776JbuVAKd3P5NAcY0FLHIRr4CFXJNCrS3hS40ZTNhmP60QxNSwRBDAnr3

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pakan; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA pakan;


ALTER SCHEMA pakan OWNER TO postgres;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


--
-- Name: suhu; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA suhu;


ALTER SCHEMA suhu OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: labuser
--

CREATE TYPE public.userrole AS ENUM (
    'peternak',
    'admin'
);


ALTER TYPE public.userrole OWNER TO labuser;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: users; Type: TABLE; Schema: public; Owner: labuser
--

CREATE TABLE public.users (
    id integer NOT NULL,
    nama character varying(100) NOT NULL,
    role public.userrole,
    password character varying(255) NOT NULL,
    peternakan character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO labuser;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: labuser
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO labuser;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: labuser
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: devices; Type: TABLE; Schema: suhu; Owner: labuser
--

CREATE TABLE suhu.devices (
    id integer NOT NULL,
    user_id integer,
    device_id character varying(50) NOT NULL,
    lokasi character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE suhu.devices OWNER TO labuser;

--
-- Name: devices_id_seq; Type: SEQUENCE; Schema: suhu; Owner: labuser
--

CREATE SEQUENCE suhu.devices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE suhu.devices_id_seq OWNER TO labuser;

--
-- Name: devices_id_seq; Type: SEQUENCE OWNED BY; Schema: suhu; Owner: labuser
--

ALTER SEQUENCE suhu.devices_id_seq OWNED BY suhu.devices.id;


--
-- Name: raw_logs; Type: TABLE; Schema: suhu; Owner: labuser
--

CREATE TABLE suhu.raw_logs (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    temperature double precision,
    setpoint double precision,
    setpoint_source character varying(20),
    heater_power integer,
    status character varying(20),
    condition character varying(20),
    "timestamp" bigint,
    created_at timestamp without time zone
);


ALTER TABLE suhu.raw_logs OWNER TO labuser;

--
-- Name: raw_logs_id_seq; Type: SEQUENCE; Schema: suhu; Owner: labuser
--

CREATE SEQUENCE suhu.raw_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE suhu.raw_logs_id_seq OWNER TO labuser;

--
-- Name: raw_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: suhu; Owner: labuser
--

ALTER SEQUENCE suhu.raw_logs_id_seq OWNED BY suhu.raw_logs.id;


--
-- Name: send_logs; Type: TABLE; Schema: suhu; Owner: labuser
--

CREATE TABLE suhu.send_logs (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    umur_setting_id integer,
    msg_id character varying(50) NOT NULL,
    setpoint double precision NOT NULL,
    umur_minggu integer NOT NULL,
    start_timestamp bigint NOT NULL,
    status character varying(20),
    trigger character varying(20),
    sent_at timestamp without time zone,
    acknowledged_at timestamp without time zone,
    error_message text
);


ALTER TABLE suhu.send_logs OWNER TO labuser;

--
-- Name: send_logs_id_seq; Type: SEQUENCE; Schema: suhu; Owner: labuser
--

CREATE SEQUENCE suhu.send_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE suhu.send_logs_id_seq OWNER TO labuser;

--
-- Name: send_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: suhu; Owner: labuser
--

ALTER SEQUENCE suhu.send_logs_id_seq OWNED BY suhu.send_logs.id;


--
-- Name: umur_settings; Type: TABLE; Schema: suhu; Owner: labuser
--

CREATE TABLE suhu.umur_settings (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    umur_minggu integer NOT NULL,
    setpoint_target double precision NOT NULL,
    is_active boolean,
    activated_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE suhu.umur_settings OWNER TO labuser;

--
-- Name: umur_settings_id_seq; Type: SEQUENCE; Schema: suhu; Owner: labuser
--

CREATE SEQUENCE suhu.umur_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE suhu.umur_settings_id_seq OWNER TO labuser;

--
-- Name: umur_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: suhu; Owner: labuser
--

ALTER SEQUENCE suhu.umur_settings_id_seq OWNED BY suhu.umur_settings.id;


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: labuser
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: devices id; Type: DEFAULT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.devices ALTER COLUMN id SET DEFAULT nextval('suhu.devices_id_seq'::regclass);


--
-- Name: raw_logs id; Type: DEFAULT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.raw_logs ALTER COLUMN id SET DEFAULT nextval('suhu.raw_logs_id_seq'::regclass);


--
-- Name: send_logs id; Type: DEFAULT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.send_logs ALTER COLUMN id SET DEFAULT nextval('suhu.send_logs_id_seq'::regclass);


--
-- Name: umur_settings id; Type: DEFAULT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.umur_settings ALTER COLUMN id SET DEFAULT nextval('suhu.umur_settings_id_seq'::regclass);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: labuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: raw_logs raw_logs_pkey; Type: CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.raw_logs
    ADD CONSTRAINT raw_logs_pkey PRIMARY KEY (id);


--
-- Name: send_logs send_logs_msg_id_key; Type: CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.send_logs
    ADD CONSTRAINT send_logs_msg_id_key UNIQUE (msg_id);


--
-- Name: send_logs send_logs_pkey; Type: CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.send_logs
    ADD CONSTRAINT send_logs_pkey PRIMARY KEY (id);


--
-- Name: umur_settings umur_settings_pkey; Type: CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.umur_settings
    ADD CONSTRAINT umur_settings_pkey PRIMARY KEY (id);


--
-- Name: ix_public_users_id; Type: INDEX; Schema: public; Owner: labuser
--

CREATE INDEX ix_public_users_id ON public.users USING btree (id);


--
-- Name: ix_suhu_devices_device_id; Type: INDEX; Schema: suhu; Owner: labuser
--

CREATE UNIQUE INDEX ix_suhu_devices_device_id ON suhu.devices USING btree (device_id);


--
-- Name: ix_suhu_devices_id; Type: INDEX; Schema: suhu; Owner: labuser
--

CREATE INDEX ix_suhu_devices_id ON suhu.devices USING btree (id);


--
-- Name: ix_suhu_umur_settings_id; Type: INDEX; Schema: suhu; Owner: labuser
--

CREATE INDEX ix_suhu_umur_settings_id ON suhu.umur_settings USING btree (id);


--
-- Name: devices devices_user_id_fkey; Type: FK CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.devices
    ADD CONSTRAINT devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: raw_logs raw_logs_device_id_fkey; Type: FK CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.raw_logs
    ADD CONSTRAINT raw_logs_device_id_fkey FOREIGN KEY (device_id) REFERENCES suhu.devices(device_id) ON DELETE CASCADE;


--
-- Name: send_logs send_logs_device_id_fkey; Type: FK CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.send_logs
    ADD CONSTRAINT send_logs_device_id_fkey FOREIGN KEY (device_id) REFERENCES suhu.devices(device_id) ON DELETE CASCADE;


--
-- Name: send_logs send_logs_umur_setting_id_fkey; Type: FK CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.send_logs
    ADD CONSTRAINT send_logs_umur_setting_id_fkey FOREIGN KEY (umur_setting_id) REFERENCES suhu.umur_settings(id) ON DELETE SET NULL;


--
-- Name: umur_settings umur_settings_device_id_fkey; Type: FK CONSTRAINT; Schema: suhu; Owner: labuser
--

ALTER TABLE ONLY suhu.umur_settings
    ADD CONSTRAINT umur_settings_device_id_fkey FOREIGN KEY (device_id) REFERENCES suhu.devices(device_id) ON DELETE CASCADE;


--
-- Name: SCHEMA pakan; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA pakan TO labuser;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT ALL ON SCHEMA public TO labuser;


--
-- Name: SCHEMA suhu; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA suhu TO PUBLIC;
GRANT ALL ON SCHEMA suhu TO labuser;


--
-- PostgreSQL database dump complete
--

\unrestrict f0YP3776JbuVAKd3P5NAcY0FLHIRr4CFXJNCrS3hS40ZTNhmP60QxNSwRBDAnr3

