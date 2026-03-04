--
-- PostgreSQL database dump
--

-- Dumped from database version 13.21
-- Dumped by pg_dump version 13.21

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: manzolo
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO manzolo;

--
-- Name: cliente; Type: TABLE; Schema: public; Owner: manzolo
--

CREATE TABLE public.cliente (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    cognome character varying(100) NOT NULL,
    codice_fiscale character varying(16) NOT NULL,
    indirizzo character varying(200),
    citta character varying(255),
    cap character varying(5),
    flag_opposizione boolean DEFAULT false
);


ALTER TABLE public.cliente OWNER TO manzolo;

--
-- Name: cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: manzolo
--

CREATE SEQUENCE public.cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cliente_id_seq OWNER TO manzolo;

--
-- Name: cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: manzolo
--

ALTER SEQUENCE public.cliente_id_seq OWNED BY public.cliente.id;


--
-- Name: costo; Type: TABLE; Schema: public; Owner: manzolo
--

CREATE TABLE public.costo (
    id integer NOT NULL,
    descrizione character varying(255) NOT NULL,
    anno_riferimento integer NOT NULL,
    data_pagamento date NOT NULL,
    totale double precision NOT NULL,
    pagato boolean
);


ALTER TABLE public.costo OWNER TO manzolo;

--
-- Name: costo_id_seq; Type: SEQUENCE; Schema: public; Owner: manzolo
--

CREATE SEQUENCE public.costo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.costo_id_seq OWNER TO manzolo;

--
-- Name: costo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: manzolo
--

ALTER SEQUENCE public.costo_id_seq OWNED BY public.costo.id;


--
-- Name: fattura; Type: TABLE; Schema: public; Owner: manzolo
--

CREATE TABLE public.fattura (
    id integer NOT NULL,
    anno integer NOT NULL,
    progressivo integer NOT NULL,
    cliente_id integer NOT NULL,
    importo_prestazione double precision NOT NULL,
    bollo boolean,
    descrizione character varying(255) NOT NULL,
    totale double precision NOT NULL,
    numero_sedute integer NOT NULL,
    data_fattura date NOT NULL,
    data_pagamento date,
    metodo_pagamento character varying(50),
    inviata_sts boolean DEFAULT false,
    protocollo_sts character varying(100),
    data_invio_sts timestamp without time zone
);


ALTER TABLE public.fattura OWNER TO manzolo;

--
-- Name: fattura_id_seq; Type: SEQUENCE; Schema: public; Owner: manzolo
--

CREATE SEQUENCE public.fattura_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fattura_id_seq OWNER TO manzolo;

--
-- Name: fattura_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: manzolo
--

ALTER SEQUENCE public.fattura_id_seq OWNED BY public.fattura.id;


--
-- Name: fattura_progressivo; Type: TABLE; Schema: public; Owner: manzolo
--

CREATE TABLE public.fattura_progressivo (
    anno integer NOT NULL,
    last_progressivo integer
);


ALTER TABLE public.fattura_progressivo OWNER TO manzolo;

--
-- Name: fattura_progressivo_anno_seq; Type: SEQUENCE; Schema: public; Owner: manzolo
--

CREATE SEQUENCE public.fattura_progressivo_anno_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fattura_progressivo_anno_seq OWNER TO manzolo;

--
-- Name: fattura_progressivo_anno_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: manzolo
--

ALTER SEQUENCE public.fattura_progressivo_anno_seq OWNED BY public.fattura_progressivo.anno;


--
-- Name: cliente id; Type: DEFAULT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.cliente ALTER COLUMN id SET DEFAULT nextval('public.cliente_id_seq'::regclass);


--
-- Name: costo id; Type: DEFAULT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.costo ALTER COLUMN id SET DEFAULT nextval('public.costo_id_seq'::regclass);


--
-- Name: fattura id; Type: DEFAULT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.fattura ALTER COLUMN id SET DEFAULT nextval('public.fattura_id_seq'::regclass);


--
-- Name: fattura_progressivo anno; Type: DEFAULT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.fattura_progressivo ALTER COLUMN anno SET DEFAULT nextval('public.fattura_progressivo_anno_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: manzolo
--

COPY public.alembic_version (version_num) FROM stdin;
a1b2c3d4e5f6
\.


--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: manzolo
--

COPY public.cliente (id, nome, cognome, codice_fiscale, indirizzo, citta, cap) FROM stdin;
1	Mario	Rossi	RSSMRA80A01H501Z	Via Roma, 1	Roma (RM)	00100
2	Anna	Bianchi	BNCNNA85B42F205X	Via Milano, 10	Milano (MI)	20100
3	Luca	Verdi	VRDLCU90C15D612Y	Via Firenze, 5	Firenze (FI)	50100
4	Sara	Neri	NRESRA92D45H501W	Via Napoli, 20	Napoli (NA)	80100
5	Elena	Ferri	FRRLNE88E60G702V	Via Torino, 8	Torino (TO)	10100
6	Marco	Galli	GLLMRC95A17B354U	Via Bologna, 15	Bologna (BO)	40100
7	Rita	Conti	CNTRTA75F44D969T	Via Genova, 3	Genova (GE)	16100
8	Laura	Mori	MROLRA82G67L219S	Via Venezia, 12	Venezia (VE)	30100
9	Giulia	Serra	SRRGLI86H62A944R	Via Palermo, 7	Palermo (PA)	90100
10	Paolo	Longo	LNGPLA83L25C351Q	Via Bari, 22	Bari (BA)	70100
11	Franco	Costa	CSTFNC70M05E625P	Via Cagliari, 9	Cagliari (CA)	09100
\.


--
-- Data for Name: costo; Type: TABLE DATA; Schema: public; Owner: manzolo
--

COPY public.costo (id, descrizione, anno_riferimento, data_pagamento, totale, pagato) FROM stdin;
\.


--
-- Data for Name: fattura; Type: TABLE DATA; Schema: public; Owner: manzolo
--

COPY public.fattura (id, anno, progressivo, cliente_id, importo_prestazione, bollo, descrizione, totale, numero_sedute, data_fattura, data_pagamento, metodo_pagamento, inviata_sts) FROM stdin;
1	2025	3	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-04-01	2025-04-01	Carta di credito/debito	t
3	2025	1	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-03-07	2025-03-07	Carta di credito/debito	t
2	2025	4	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-04-29	2025-04-29	Carta di credito/debito	t
5	2025	5	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-06-12	2025-06-12	Carta di credito/debito	t
6	2025	6	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-16	2025-07-16	Carta di credito/debito	t
7	2025	7	3	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-18	2025-07-18	Carta di credito/debito	t
8	2025	8	4	58.82	t	n. 4 di Sedute di consulenza psicologica	242	4	2025-07-18	2025-07-18	Carta di credito/debito	t
9	2025	9	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-21	2025-08-21	Carta di credito/debito	t
10	2025	10	6	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-22	2025-07-22	Carta di credito/debito	t
11	2025	11	7	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-24	2025-07-24	Carta di credito/debito	t
12	2025	12	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-24	2025-07-24	Carta di credito/debito	t
13	2025	13	8	58.82	t	n. 5 di Sedute di consulenza psicologica	302	5	2025-07-24	2025-07-24	Carta di credito/debito	t
14	2025	14	3	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-25	2025-07-25	Carta di credito/debito	t
15	2025	15	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-28	2025-07-28	Carta di credito/debito	t
16	2025	16	6	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-28	2025-07-28	Carta di credito/debito	t
17	2025	17	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-31	2025-07-31	Carta di credito/debito	t
18	2025	18	3	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-01	2025-08-01	Carta di credito/debito	t
19	2025	19	9	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-06	2025-08-06	Carta di credito/debito	t
20	2025	20	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-06	2025-08-06	Carta di credito/debito	t
21	2025	21	6	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-06	2025-08-06	Carta di credito/debito	t
22	2025	22	7	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-07	2025-08-07	Carta di credito/debito	t
23	2025	23	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-07	2025-08-07	Carta di credito/debito	t
4	2025	2	11	58.82	t	n. 4 di Sedute di consulenza psicologica	242	4	2025-03-21	2025-03-21	Carta di credito/debito	t
24	2025	24	10	58.82	t	n. 4 di Sedute di consulenza psicologica	242	4	2025-08-11	2025-08-11	Carta di credito/debito	t
25	2025	25	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-11	2025-08-11	Carta di credito/debito	t
\.


--
-- Data for Name: fattura_progressivo; Type: TABLE DATA; Schema: public; Owner: manzolo
--

COPY public.fattura_progressivo (anno, last_progressivo) FROM stdin;
2025	25
\.


--
-- Name: cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: manzolo
--

SELECT pg_catalog.setval('public.cliente_id_seq', 11, true);


--
-- Name: costo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: manzolo
--

SELECT pg_catalog.setval('public.costo_id_seq', 1, false);


--
-- Name: fattura_id_seq; Type: SEQUENCE SET; Schema: public; Owner: manzolo
--

SELECT pg_catalog.setval('public.fattura_id_seq', 25, true);


--
-- Name: fattura_progressivo_anno_seq; Type: SEQUENCE SET; Schema: public; Owner: manzolo
--

SELECT pg_catalog.setval('public.fattura_progressivo_anno_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: cliente cliente_codice_fiscale_key; Type: CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_codice_fiscale_key UNIQUE (codice_fiscale);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id);


--
-- Name: costo costo_pkey; Type: CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.costo
    ADD CONSTRAINT costo_pkey PRIMARY KEY (id);


--
-- Name: fattura fattura_pkey; Type: CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.fattura
    ADD CONSTRAINT fattura_pkey PRIMARY KEY (id);


--
-- Name: fattura_progressivo fattura_progressivo_pkey; Type: CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.fattura_progressivo
    ADD CONSTRAINT fattura_progressivo_pkey PRIMARY KEY (anno);


--
-- Name: fattura fattura_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: manzolo
--

ALTER TABLE ONLY public.fattura
    ADD CONSTRAINT fattura_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- PostgreSQL database dump complete
--
