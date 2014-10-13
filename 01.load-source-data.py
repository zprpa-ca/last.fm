#!/usr/bin/env python

''' Create the SQLite database and retrieve the Last.fm source data using the API.

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
import os, sys, sqlite3, time
from collections import deque

#-- custom libs
import utils

#-- setup number formatting
import locale
locale.setlocale( locale.LC_ALL, "" )
fmt = locale.format

#==============================================================================#
#--------------------------------- SETUP --------------------------------------#
#==============================================================================#

log  = utils.ZpLog(   'logs/' + os.path.basename(__file__) + '.log')
elog = utils.ZpErrLog('logs/' + os.path.basename(__file__) + '.ERROR-traceback.log')
log.write(''.ljust(150,'*'), skip_line=1, add_line=1)

#-- setup lastfm API root url and common params
root_url = 'http://ws.audioscrobbler.com/2.0/'
params   = {'api_key':'8f208e8a9040c44673f23498da24db20',
            'format' :'json'}

#--------------------------------------#
#-- create database                    #
#--------------------------------------#

log.write('Create and setup database...')

dbs = sqlite3.connect('data/lastfm.sql3', detect_types=sqlite3.PARSE_DECLTYPES)
cur = dbs.cursor()
with open('create-tables.sql','r') as f: stream = f.read()
cur.executescript( stream )
cur.close()
dbs.commit()

log.write_add('Done!')
log.write(''.ljust(150,'*'), add_line=1)

#==============================================================================#
#------------------------- Load source data -----------------------------------#
#==============================================================================#

#--------------------------------------#
#-- load Top-1000 artists              #
#--------------------------------------#

log.write('Loading Top-1000 artists...', skip_line=1)

''' Request 10 pages, with 100 artists each.
    The maximum allowd by the API is 1000.
'''
params['method'] = 'chart.getTopArtists'
params['limit']  = '100'

dataset_len = 0
cur = dbs.cursor()
for pg_num in xrange(1,11):
    params['page'] = str(pg_num)

    resp = utils.api_request( root_url, params )

    recnum = int(resp['artists']['@attr']['perPage'])
    log.write('Received pg# ' + str(resp['artists']['@attr']['page']) + ' with ' + str(recnum) + ' records.')
    dataset_len += recnum

    #-- generate and load record tuples
    cur.executemany("INSERT INTO artists VALUES (?,?,?)",
                    ((e['name'],int(e['listeners']),int(e['playcount'])) for e in resp['artists']['artist']))

    #-- pause 1.5 sec to avoid API request overload
    time.sleep(1.5)
cur.close()
dbs.commit()

log.write('Loaded %s records.'%fmt('%20d',dataset_len,True).strip())
log.write(''.ljust(150,'*'), add_line=1)

#--------------------------------------#
#-- load tags for all Top-1000 artists #
#--------------------------------------#

log.write('Loading tags for Top-1000 artists...')

params['method'] = 'artist.getTopTags'

''' Get the list of collected artists, which is going to drive the
    download of the TopTags for each artist.
    Use the queue, so we can rotate the entry to the back of the queue,
    when download fails. Manual user input (answer) will give an opportunity
    to stop the download in case of the repeated/multiple failure.
'''
cur = dbs.cursor()
cur.execute("SELECT name FROM artists ORDER BY name DESC")
artists = deque([r[0] for r in cur])

i = 0
while len(artists) > 0:
    ''' Because the response occasionally failes to provide a correct dictionary,
        skip over such entry and push it to the back of the queue.
    '''
    try:
        #-- encode non-ascii chars in the url path
        params['artist'] = artists[-1].encode('utf-8')

        resp = utils.api_request( root_url, params )

        #-- generate and load record tuples, sqlite3 handles text data as unicode by default
        cur.executemany("INSERT INTO top_artist_tags VALUES (?,?,?)",
                        ((artists[-1],e['name'],int(e['count'])) for e in resp['toptags']['tag']))

        #-- for writing to the log file, encode the non-ascii chars in artist name
        log.write('Loaded %s tags for the artist %s.'%(fmt('%6d',cur.rowcount,True),artists[-1].encode('utf-8')))
        dbs.commit()

        #-- remove the processed entry from the queue
        artists.pop()

        #-- pause 1.5 sec to avoid API request overload
        time.sleep(1.5)
    except:
        err_type,err_value,_ = sys.exc_info()
        log.write('Loading tags for the artist %s failed!'%artists[-1].encode('utf-8'), skip_line=1)
        log.write('Error type:\n'+str(err_type))
        log.write('Error value:\n'+str(err_value), add_line=1)

        ''' Rotate the entry to the back, where it will be requested again
            once the queue is consumed.
        '''
        artists.rotate()

        ''' The possibility for the user to stop the download and processing.
            Once when the failed entries (at the end of the queue) are reached,
            the user can try to cycle through several times and attempt to get
            correct download. Once when it is OK or in case of the repeated
            failures, the process can be stopped.
        '''
        answer = raw_input('\nContinue and skip to the next artist [y]: ')
        if answer == 'n':
            break

    ''' Pause for 5 minutes after each 100 artists processed.
        This should not be necessary accordingly to the API docs, if we pause
        between the requests, just to be fair and not overload the API.
        Comment out if necessary.
    '''
#    i += 1
#    if i >= 100:
#        log.write('Pausing for 5 minutes...')
#        i = 0
#        time.sleep(301)

cur.execute("SELECT count(*) FROM top_artist_tags")
rec_count = cur.fetchone()[0]
cur.close()
dbs.close()
log.write('Loaded total of %s records.'%fmt('%12d',rec_count,True).strip())
log.write(''.ljust(150,'*'), add_line=1)

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#
