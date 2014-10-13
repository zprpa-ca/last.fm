/*
Copyright (C) 2014, Zlatko Prpa <zprpa.ca@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/*============================================================================*/
/*------------------------- SOURCE Data --------------------------------------*/
/*============================================================================*/

DROP TABLE IF EXISTS top_artist_tags;
DROP TABLE IF EXISTS artists;

CREATE TABLE artists (
    name        varchar(256)    not null,
    listeners   int             not null default 0,
    play_count  int             not null default 0
);
CREATE UNIQUE INDEX artists_pk ON artists (name);

CREATE TABLE top_artist_tags (
    artist_name     varchar(256)    not null,
    tag             varchar(256)    not null,
    count           int             not null default 0
);
CREATE UNIQUE INDEX top_artist_tags_pk ON top_artist_tags (artist_name,tag);

/*============================================================================*/
/*------------------------- TARGET Data --------------------------------------*/
/*============================================================================*/

DROP TABLE IF EXISTS tag_correlation;
DROP TABLE IF EXISTS artist_correlation;

CREATE TABLE tag_correlation (
    tag1        varchar(256)    not null,
    tag2        varchar(256)    not null,
    corr_coef   real            not null default 0
);
CREATE UNIQUE INDEX tag_correlation_pk ON tag_correlation (tag1,tag2);

CREATE TABLE artist_correlation (
    artist1     varchar(256)    not null,
    artist2     varchar(256)    not null,
    corr_coef   real            not null default 0
);
CREATE UNIQUE INDEX artist_correlation_pk ON artist_correlation (artist1,artist2);

/*============================================================================*/
/*----------------------------------------------------------------------------*/
/*============================================================================*/

