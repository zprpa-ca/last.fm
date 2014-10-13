#!/usr/bin/env python

''' Compare the generated correlation with Last.fm data provided by the API,
    "tag.getSimilar" and "artist.getSimilar" methods.
    For the tag comparison we use the tag "80s" and for the artist comparison
    we use "Cyndi Lauper".

    While there are many close match examples, there are also some differences
    which could be explained by the following:

    1) Tags
    -   By loading the 1000 top artists records, many tags are probably missing
        from the sample data.
    -   The generalization (filtering) applied to tags is not the same.
    -   The API provided tags rankings (count) is likely the result of the
        already applied data procesing, i.e not the original tag counts.

    2) Artists
    -   Some artist records are missing from the 1000 top artist dataset.
    -   The logic applied to get the artist correlation is different.
        The Last.fm API documentation states:
        "The list of artists which you see on an artist page as being "similar"
        is automatically created by the Last.fm Audioscrobbler, based on our
        user's listening habits: If a lot of users listen to Artist X, but also
        Artist Y and Z - Y and Z artists will become similar to X."
        Our logic is using the artists tag ranking profile.

    #--------------------------------------------------------------------------#
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
    #--------------------------------------------------------------------------#
'''

#-- standard libs
import os, sys, sqlite3, time, locale, itertools as it

#-- add-on libs
import numpy

#-- custom libs
import utils

#==============================================================================#
#--------------------------------- SETUP --------------------------------------#
#==============================================================================#

log  = utils.ZpLog(   'logs/' + os.path.basename(__file__) + '.log')
elog = utils.ZpErrLog('logs/' + os.path.basename(__file__) + '.ERROR-traceback.log')
log.write(''.ljust(150,'*'), skip_line=1, add_line=1)

#-- setup number formatting
locale.setlocale( locale.LC_ALL, "" )
fmt = locale.format

#-- setup lastfm API root url and common params
root_url = 'http://ws.audioscrobbler.com/2.0/'
params   = {'api_key':'8f208e8a9040c44673f23498da24db20',
            'format' :'json'}

#-- open database
dbs = sqlite3.connect('data/lastfm.sql3', detect_types=sqlite3.PARSE_DECLTYPES)

#==============================================================================#
#------------------------- Similar Tags comparison ----------------------------#
#==============================================================================#

log.write('Performing similar tags comparison.')

params['method'] = 'tag.getSimilar'
params['tag']    = '80s'

resp     = utils.api_request( root_url, params )
api_recs = [e['name'] for e in resp['similartags']['tag']]
log.write('Loaded %s records from Last.fm API.'%fmt('%7d',len(api_recs),True).strip())

cur = dbs.cursor()
cur.execute("""
    SELECT
        CASE WHEN tag1='80s' THEN tag2 ELSE tag1 END,
        corr_coef
    FROM tag_correlation
    WHERE tag1='80s' OR tag2='80s'
    ORDER BY 2 DESC
    """)
dbs_recs = cur.fetchall()
cur.close()
log.write('Loaded %s records from local database.'%fmt('%7d',len(dbs_recs),True).strip())

def _f( r1, r2 ):
    fld1 = ''.ljust(30) if r1==None else r1.ljust(30)
    fld2 = '' if r2==None else ''.join( (r2[0].ljust(30),str(r2[1])) )
    return '\t'.join( (fld1,fld2,'\n') )

f = open('docs/similar-tags-comparison.txt','w')
f.writelines("""
Similarity comparison between the Last.fm API data and custom calculation.

Compared tag: '80s'

Last.fm API                     Custom Calculation
------------------------------  ------------------------------------------------
""")
f.writelines((r for r in map(_f, api_recs, dbs_recs)))
f.close()
log.write('Comparison list saved in the "docs/similar-tags-comparison.txt" file.',add_line=1)

#==============================================================================#
#------------------------- Similar Tags comparison ----------------------------#
#==============================================================================#

log.write('Performing similar artists comparison.')

params['method'] = 'artist.getSimilar'
params['artist'] = 'Cyndi Lauper'

resp     = utils.api_request( root_url, params )
api_recs = [(e['name'].encode('utf-8'), e['match']) for e in resp['similarartists']['artist']]
log.write('Loaded %s records from Last.fm API.'%fmt('%7d',len(api_recs),True).strip())

cur = dbs.cursor()
cur.execute("""
    SELECT
        CASE WHEN artist1='Cyndi Lauper' THEN artist2 ELSE artist1 END,
        corr_coef
    FROM artist_correlation
    WHERE artist1='Cyndi Lauper' OR artist2='Cyndi Lauper'
    ORDER BY 2 DESC
    """)
dbs_recs = cur.fetchall()
cur.close()
log.write('Loaded %s records from local database.'%fmt('%7d',len(dbs_recs),True).strip())

def _f( r1, r2 ):
    fld1 = ''.ljust(60) if r1==None else '\t'.join( (r1[0].ljust(30),str(r1[1]).ljust(30)) )
    fld2 = ''           if r2==None else '\t'.join( (r2[0].ljust(30),str(r2[1])) )
    return ''.join( (fld1,'\t',fld2.encode('utf-8'),'\n') )

f = open('docs/similar-artists-comparison.txt','w')
f.writelines("""
Similarity comparison between the Last.fm API data and custom calculation.

Compared artist: 'Cyndi Lauper'\n
""")
f.write('\t'.join( ('Last.fm API'.ljust(30),       'Match Coeff'.ljust(30),
                    'Custom Calculation'.ljust(30),'Match Coeff'.ljust(30),'\n') ))
f.write('\t'.join((''.center(30,'-') for i in xrange(4)))+'\n')
f.writelines((r for r in map(_f, api_recs, dbs_recs)))
f.close()
log.write('Comparison list saved in the "docs/similar-artists-comparison.txt" file.',add_line=1)

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#

dbs.close()
log.write(''.ljust(150,'*'), add_line=1)
log.close()

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#
