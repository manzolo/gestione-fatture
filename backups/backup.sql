--
-- PostgreSQL database dump
--

\restrict oyiOHtaVlPVpaoIFkWgm5akBwklgxVo9TpS23jE4JCPaUOjZFc727kkV5VKkNQb

-- Dumped from database version 13.23
-- Dumped by pg_dump version 13.23

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO "user";

--
-- Name: cliente; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.cliente (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    cognome character varying(100) NOT NULL,
    codice_fiscale character varying(16) NOT NULL,
    indirizzo character varying(200),
    citta character varying(255),
    cap character varying(5),
    flag_opposizione boolean DEFAULT false,
    luogo_nascita character varying(255),
    data_nascita date
);


ALTER TABLE public.cliente OWNER TO "user";

--
-- Name: cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cliente_id_seq OWNER TO "user";

--
-- Name: cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.cliente_id_seq OWNED BY public.cliente.id;


--
-- Name: costo; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.costo (
    id integer NOT NULL,
    descrizione character varying(255) NOT NULL,
    anno_riferimento integer NOT NULL,
    data_pagamento date NOT NULL,
    totale double precision NOT NULL,
    pagato boolean,
    ricorrenza_id integer,
    periodo_riferimento character varying(7)
);


ALTER TABLE public.costo OWNER TO "user";

--
-- Name: costo_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.costo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.costo_id_seq OWNER TO "user";

--
-- Name: costo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.costo_id_seq OWNED BY public.costo.id;


--
-- Name: costo_ricorrente; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.costo_ricorrente (
    id integer NOT NULL,
    descrizione character varying(255) NOT NULL,
    totale double precision NOT NULL,
    frequenza character varying(20) NOT NULL,
    giorno_scadenza integer NOT NULL,
    data_inizio date NOT NULL,
    data_fine date,
    pagato_default boolean,
    attivo boolean
);


ALTER TABLE public.costo_ricorrente OWNER TO "user";

--
-- Name: costo_ricorrente_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.costo_ricorrente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.costo_ricorrente_id_seq OWNER TO "user";

--
-- Name: costo_ricorrente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.costo_ricorrente_id_seq OWNED BY public.costo_ricorrente.id;


--
-- Name: fattura; Type: TABLE; Schema: public; Owner: user
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
    numero_sedute double precision NOT NULL,
    data_fattura date NOT NULL,
    data_pagamento date,
    metodo_pagamento character varying(50),
    inviata_sts boolean DEFAULT false,
    protocollo_sts character varying(100),
    data_invio_sts timestamp without time zone
);


ALTER TABLE public.fattura OWNER TO "user";

--
-- Name: fattura_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.fattura_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fattura_id_seq OWNER TO "user";

--
-- Name: fattura_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.fattura_id_seq OWNED BY public.fattura.id;


--
-- Name: fattura_progressivo; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.fattura_progressivo (
    anno integer NOT NULL,
    last_progressivo integer
);


ALTER TABLE public.fattura_progressivo OWNER TO "user";

--
-- Name: fattura_progressivo_anno_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.fattura_progressivo_anno_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fattura_progressivo_anno_seq OWNER TO "user";

--
-- Name: fattura_progressivo_anno_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.fattura_progressivo_anno_seq OWNED BY public.fattura_progressivo.anno;


--
-- Name: cliente id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.cliente ALTER COLUMN id SET DEFAULT nextval('public.cliente_id_seq'::regclass);


--
-- Name: costo id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.costo ALTER COLUMN id SET DEFAULT nextval('public.costo_id_seq'::regclass);


--
-- Name: costo_ricorrente id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.costo_ricorrente ALTER COLUMN id SET DEFAULT nextval('public.costo_ricorrente_id_seq'::regclass);


--
-- Name: fattura id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.fattura ALTER COLUMN id SET DEFAULT nextval('public.fattura_id_seq'::regclass);


--
-- Name: fattura_progressivo anno; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.fattura_progressivo ALTER COLUMN anno SET DEFAULT nextval('public.fattura_progressivo_anno_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.alembic_version (version_num) FROM stdin;
d9e1f3a5b7c9
\.


--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.cliente (id, nome, cognome, codice_fiscale, indirizzo, citta, cap, flag_opposizione, luogo_nascita, data_nascita) FROM stdin;
1	Lapo	Schmid	SCHLPA14L24B036G	Via Campomigliaio, 20	Scarperia e San Piero (FI)	50038	f	\N	\N
2	Stefania	Galeotti	GLTSFN89R42B036T	Via Pietro Nenni, 19	Borgo San Lorenzo (FI)	50032	f	\N	\N
3	Isabel Maya	Lasagni	LSGSLM12C45B036L	Via Casanuova, 107	Firenzuola (FI)	50033	f	\N	\N
4	Daniela	Paladini	PLDDNL94M45B036F	Via Molezzano, 61	Vicchio (FI)	50039	f	\N	\N
5	Giorgia	D’Orilia	DRLGRG03A60B036C	Via Alessandro Pieri Stella, 66/A	Ronta - Borgo San Lorenzo (FI)	50032	f	\N	\N
6	Paolo	Borselli	BRSPLA97A17B036L	Via Faentina, 144	Ronta - Borgo San Lorenzo (FI)	50032	f	\N	\N
7	Rita	Piccini	PCCRTI54E44I085O	Via Rabatta, 27	Borgo San Lorenzo (FI)	50032	f	\N	\N
8	Laura	Paladini	PLDLRA77E67B036M	Via dell’Azzurro, 5	Scarperia e San Piero (FI)	50038	f	\N	\N
9	Adele	Salimbeni	SLMDLA82S62D612M	Via Solferino, 4	Scarperia e San Piero (FI)	50038	f	\N	\N
11	Raimondo 	Della Rocca	DLLRND48M05E971M	Via Piave, 41/26	Borgo San Lorenzo (FI)	50032	f	\N	\N
10	Dario	Bulletti	BLLDRA83L25D575Z	Via Stefaneschi, 39A	Ronta - Borgo San Lorenzo (FI)	50032	f	\N	\N
\.


--
-- Data for Name: costo; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.costo (id, descrizione, anno_riferimento, data_pagamento, totale, pagato, ricorrenza_id, periodo_riferimento) FROM stdin;
\.


--
-- Data for Name: costo_ricorrente; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.costo_ricorrente (id, descrizione, totale, frequenza, giorno_scadenza, data_inizio, data_fine, pagato_default, attivo) FROM stdin;
\.


--
-- Data for Name: fattura; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.fattura (id, anno, progressivo, cliente_id, importo_prestazione, bollo, descrizione, totale, numero_sedute, data_fattura, data_pagamento, metodo_pagamento, inviata_sts, protocollo_sts, data_invio_sts) FROM stdin;
1	2025	3	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-04-01	2025-04-01	Carta di credito/debito	t	\N	\N
3	2025	1	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-03-07	2025-03-07	Carta di credito/debito	t	\N	\N
2	2025	4	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-04-29	2025-04-29	Carta di credito/debito	t	\N	\N
5	2025	5	1	58.82	t	n. 2 di Sedute di consulenza psicologica	122	2	2025-06-12	2025-06-12	Carta di credito/debito	t	\N	\N
6	2025	6	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-16	2025-07-16	Carta di credito/debito	t	\N	\N
7	2025	7	3	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-18	2025-07-18	Carta di credito/debito	t	\N	\N
8	2025	8	4	58.82	t	n. 4 di Sedute di consulenza psicologica	242	4	2025-07-18	2025-07-18	Carta di credito/debito	t	\N	\N
9	2025	9	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-21	2025-08-21	Carta di credito/debito	t	\N	\N
10	2025	10	6	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-22	2025-07-22	Carta di credito/debito	t	\N	\N
11	2025	11	7	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-24	2025-07-24	Carta di credito/debito	t	\N	\N
12	2025	12	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-24	2025-07-24	Carta di credito/debito	t	\N	\N
13	2025	13	8	58.82	t	n. 5 di Sedute di consulenza psicologica	302	5	2025-07-24	2025-07-24	Carta di credito/debito	t	\N	\N
14	2025	14	3	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-25	2025-07-25	Carta di credito/debito	t	\N	\N
15	2025	15	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-28	2025-07-28	Carta di credito/debito	t	\N	\N
16	2025	16	6	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-28	2025-07-28	Carta di credito/debito	t	\N	\N
17	2025	17	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-07-31	2025-07-31	Carta di credito/debito	t	\N	\N
18	2025	18	3	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-01	2025-08-01	Carta di credito/debito	t	\N	\N
19	2025	19	9	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-06	2025-08-06	Carta di credito/debito	t	\N	\N
20	2025	20	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-06	2025-08-06	Carta di credito/debito	t	\N	\N
21	2025	21	6	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-06	2025-08-06	Carta di credito/debito	t	\N	\N
22	2025	22	7	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-07	2025-08-07	Carta di credito/debito	t	\N	\N
23	2025	23	2	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-07	2025-08-07	Carta di credito/debito	t	\N	\N
4	2025	2	11	58.82	t	n. 4 di Sedute di consulenza psicologica	242	4	2025-03-21	2025-03-21	Carta di credito/debito	t	\N	\N
24	2025	24	10	58.82	t	n. 4 di Sedute di consulenza psicologica	242	4	2025-08-11	2025-08-11	Carta di credito/debito	t	\N	\N
25	2025	25	5	58.82	f	n. 1 di Seduta di consulenza psicologica	60	1	2025-08-11	2025-08-11	Carta di credito/debito	t	\N	\N
\.


--
-- Data for Name: fattura_progressivo; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.fattura_progressivo (anno, last_progressivo) FROM stdin;
2025	25
\.


--
-- Name: cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.cliente_id_seq', 11, true);


--
-- Name: costo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.costo_id_seq', 1, false);


--
-- Name: costo_ricorrente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.costo_ricorrente_id_seq', 1, false);


--
-- Name: fattura_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.fattura_id_seq', 25, true);


--
-- Name: fattura_progressivo_anno_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.fattura_progressivo_anno_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: cliente cliente_codice_fiscale_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_codice_fiscale_key UNIQUE (codice_fiscale);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id);


--
-- Name: costo costo_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.costo
    ADD CONSTRAINT costo_pkey PRIMARY KEY (id);


--
-- Name: costo_ricorrente costo_ricorrente_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.costo_ricorrente
    ADD CONSTRAINT costo_ricorrente_pkey PRIMARY KEY (id);


--
-- Name: fattura fattura_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.fattura
    ADD CONSTRAINT fattura_pkey PRIMARY KEY (id);


--
-- Name: fattura_progressivo fattura_progressivo_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.fattura_progressivo
    ADD CONSTRAINT fattura_progressivo_pkey PRIMARY KEY (anno);


--
-- Name: costo uq_costo_ricorrenza_periodo; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.costo
    ADD CONSTRAINT uq_costo_ricorrenza_periodo UNIQUE (ricorrenza_id, periodo_riferimento);


--
-- Name: fattura fattura_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.fattura
    ADD CONSTRAINT fattura_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id);


--
-- Name: costo fk_costo_ricorrenza_id_costo_ricorrente; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.costo
    ADD CONSTRAINT fk_costo_ricorrenza_id_costo_ricorrente FOREIGN KEY (ricorrenza_id) REFERENCES public.costo_ricorrente(id);


--
-- PostgreSQL database dump complete
--

\unrestrict oyiOHtaVlPVpaoIFkWgm5akBwklgxVo9TpS23jE4JCPaUOjZFc727kkV5VKkNQb

