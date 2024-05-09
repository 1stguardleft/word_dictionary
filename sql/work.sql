-- SQLite

CREATE TABLE IF NOT EXISTS SOURCE (
    SOURCE_KEY INTEGER PRIMARY KEY,
    DATA_SOURCE TEXT NOT NULL,
    COLUMN_NAME TEXT NOT NULL,
    TABLE_NAME TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS TERM (
    SOURCE_KEY INTEGER PRIMARY KEY,
    TERMS_ORDER INTEGER PRIMAY KEY,
    TERM_NAME TEXT NOT NULL,
    TERM_ENG_NAME TEXT NULL,
    ABBR_TERM_NAME TEXT NULL
);


SELECT * FROM sqlite_master WHERE type='table';

select * from source;

select * from seperation;
select * from term;



select distinct term_name
  from seperation
 where seperation_code in ('NNG', 'NNP');