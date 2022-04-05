
drop table image_lib;

CREATE TABLE image_lib
(
   id BIGSERIAL PRIMARY KEY,
   guid uuid,
   filehash char(64),
   faces jsonb,
   tags jsonb,
   latitude varchar(16),
   longitude varchar(16),
   gpsdata jsonb,
   exifdata jsonb,
   address jsonb,
   address_full text,
   imageyear int,
   imagemonth int,
   imageday int,
   imagedate date,
   originalname char(64),
   description text,
   textonpic text,
   thumbnail bytea,
   sourcepath text,
   taken_at timestamp,
   insdat timestamp DEFAULT now() NOT NULL
);

COMMENT ON COLUMN image_lib.id IS 'Autoincrement';
COMMENT ON COLUMN image_lib.guid IS 'Unique file GUID for sharing, etc.';
COMMENT ON COLUMN image_lib.filehash IS 'SHA256 hash of current file for duplicates detection';
COMMENT ON COLUMN image_lib.faces IS 'Faces(names), detected on pic';
COMMENT ON COLUMN image_lib.tags IS 'Tags of pic';
COMMENT ON COLUMN image_lib.latitude IS 'GPS latitude of pic';
COMMENT ON COLUMN image_lib.longitude IS 'GPS longitude of pic';
COMMENT ON COLUMN image_lib.gpsdata IS 'Full GPS data of pic';
COMMENT ON COLUMN image_lib.exifdata IS 'Full EXIF data of pic';
COMMENT ON COLUMN image_lib.address IS 'Address elements from Nominatim reverse geocoding';
COMMENT ON COLUMN image_lib.address IS 'Full address line from Nominatim reverse geocoding';
COMMENT ON COLUMN image_lib.imageyear IS 'Year of picture, if impossible to find from EXIF tag';
COMMENT ON COLUMN image_lib.imagemonth IS 'Month of picture, if impossible to find from EXIF tag';
COMMENT ON COLUMN image_lib.imageday IS 'Day of picture, if impossible to find from EXIF tag';
COMMENT ON COLUMN image_lib.imagedate IS 'Date of picture, entered somehow alternatively, if impossible to find from EXIF tag';
COMMENT ON COLUMN image_lib.originalname IS 'Name of original image file';
COMMENT ON COLUMN image_lib.description IS 'Description of picture (by cognitive services)';
COMMENT ON COLUMN image_lib.textonpic IS 'Text, detected on picture';
COMMENT ON COLUMN image_lib.thumbnail IS 'Image preview thumbnail';
COMMENT ON COLUMN image_lib.sourcepath IS 'Image source path to download original from';
COMMENT ON COLUMN image_lib.taken_at IS 'Date/time when pic was taken, usually, from EXIF tag';
COMMENT ON COLUMN image_lib.insdat IS 'Date/time of particular DB record';

--CREATE INDEX idx_image_lib_ctr ON image_lib(country);

CREATE INDEX idx_image_hash_2 ON image_lib (left(filehash, 2) varchar_pattern_ops);

-- And then search: SELECT * FROM image_lib WHERE left(filehash, 2)='29' AND filehash='2971b8d8f8411e279503cd0d126cc864'
-- left(filehash, 2)='29' ==> to make index work

-- https://www.postgresql.org/docs/9.4/functions-json.html
-- Do any of these key/element strings exist?
SELECT * FROM image_lib WHERE (tags->'tags')::jsonb ?| array['child', 'c']
SELECT * FROM image_lib WHERE (faces->'faces')::jsonb ?| array['elina', 'dima']