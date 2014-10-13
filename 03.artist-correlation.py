#!/usr/bin/env python

''' Calculate the correlation between the artists. Intermediate datasets are
    saved in the HDF5 file and the final dataset is saved in the database as
    well. The artist correlation matrix is saved only for the single
    selected artist, used in the final step for the similarity comparison.

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
import numpy, h5py

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

#-- open the HDF5 file for the storage of the intermediate datasets
h5f = h5py.File('data/artist-correlation-datasets.h5','w')
vlen_dtype = h5py.special_dtype(vlen=str)

#==============================================================================#
#------------------------- Load and process data ------------------------------#
#==============================================================================#

#--------------------------------------#
#-- load data and apply basic filter   #
#--------------------------------------#
''' Load the records from the artist/tag table.
    There is no reason to apply any filter to this basic dataset, as opposite
    to the tag correlation procedure. We do not need to generalize any
    specific artist, as we had to do with tag data.
    Otherwise, the whole processing logic is very much the same.
'''
log.write('Load data.')
dbs = sqlite3.connect('data/lastfm.sql3', detect_types=sqlite3.PARSE_DECLTYPES)
cur = dbs.cursor()
cur.execute("SELECT t.artist_name, t.tag, t.count FROM top_artist_tags t")
recs = numpy.array([r for r in cur],dtype=[('art','O'),('tag','O'),('count','i4')])
cur.close()
dbs.close()
log.write('Loaded %s records.'%fmt('%12d',recs.shape[0],True).strip())

#--------------------------------------#
#-- prepare data for correlation calc  #
#--------------------------------------#

log.write('Prepare data for the correlation calc.')

#-- Get unique list of artists and tags.
unique_art  = numpy.unique( recs['art'] )
unique_tags = numpy.unique( recs['tag'] )

''' Create 2d array to hold the vector for each artist. The vector size is 2x
    the length of the list of the unique tags. First part will have the
    value 0/1, depending if the given artist is associated with the given tag.
    The second part will have the tag ranking (count) value, at the same
    position for the given tag.

    Assuming the following tuples in the basic dataset [recs]:
    (art1,tag1,90), (art1,tag2,80), (art1,tag3,60),
    (art2,tag1,80),                 (art2,tag3,90),
                    (art3,tag2,90), (art3,tag3,80),
    (art4,tag1,50), (art4,tag2,70), (art4,tag3,70)

    The "unique_art"  list is:  [art1,art2,art3,art4]
    The "unique_tags" list is:  [tag1,tag2,tag3]
    offset = 3
    Single artist vector is [0,0,0,0,0,0], with logical mask as
    [tag1,tag2,tag3,rank1,rank2,rank3].

    Based on the above described data, the complete matrix "tags_mx"
    will have 4 vectors with following values:
    [[1,1,1,90,80,60],
     [1,0,1,80, 0,90],
     [0,1,1, 0,90,80],
     [1,1,1,50,70,70]]

    The sample data (tags for 1000 artists) is very small and this executes
    fast, otherwise this loop would be a strong candidate for parallel
    execution.
'''
offset = unique_tags.shape[0]
art_mx = numpy.zeros((unique_art.shape[0],offset*2),'i4')

for i in xrange(unique_art.shape[0]):
    #-- find indicies for all records in the basic dataset for given artist
    idx = numpy.where( recs['art']==unique_art[i] )[0]
    #-- get all tags and counts for the given artist
    tags   = recs['tag'].take(idx)
    counts = recs['count'].take(idx)
    #-- find the index positions in the tag unique list, for all tag artists
    idx = unique_tags.searchsorted(tags)
    #-- fill in the first part of the artist vector with 1, for each tag found
    numpy.put( art_mx[i], idx, 1 )
    #-- fill in the tag count (rank) in the second part of the artist vector
    numpy.put( art_mx[i], idx+offset, counts )

ds = h5f.create_dataset('unique_art', unique_art.shape, dtype=vlen_dtype)
ds[...] = unique_art
ds = h5f.create_dataset('unique_tags', unique_tags.shape, dtype=vlen_dtype)
ds[...] = unique_tags
ds = h5f.create_dataset('art_mx', art_mx.shape, dtype=art_mx.dtype)
ds[...] = art_mx
h5f.flush()
log.write('Saved following datasets:')
log.write('unique_art:  shape->%s\tdtype->%s'%(unique_art.shape, unique_art.dtype))
log.write('unique_tags: shape->%s\tdtype->%s'%(unique_tags.shape,unique_tags.dtype))
log.write('art_mx:      shape->%s\tdtype->%s'%(art_mx.shape,     art_mx.dtype), add_line=1)

#--------------------------------------#
#-- calculate artist correlation       #
#--------------------------------------#

log.write('Calculate artist correlation.')

''' Calculate correlation for each distinct pair of artist vectors.
    Again, in case of high data volume, this could be executed in parallel
    using the pool of worker processes.
    For the present dataset, the approx size of the artist correlation matrix
    is around 500K recs.
'''
#-- first iterator to get the matrix size
itr  = ((i,j) for i in xrange(unique_art.shape[0]) for j in xrange(i+1,unique_art.shape[0]))
size = sum(1 for _ in itr)
corr = numpy.empty( size, dtype=[('art1','O'),('art2','O'),('c','f8')] )
#-- full iterator
itr = it.izip(  ((i,j) for i in xrange(unique_art.shape[0]) for j in xrange(i+1,unique_art.shape[0])),
                (k for k in xrange(size)) )
t = time.time()
for (x,y),z in itr:
    c = numpy.corrcoef( art_mx[x], art_mx[y] )[0,1]
    corr[z] = (unique_art[x], unique_art[y], c)
    #-- update progres every 10K recs
    if z%10000==0:
        log.write_timing1( z, size, t, time.time(), out_type='TTY')

''' Because the full dataset is somewhat big, save only the sample used later
    in the "similar artist" comparison.
    Comment out if you want to re-run and get all records.
'''
log.write('Full artist correlation matrix: [corr] shape->%s\tdtype->%s'%(corr.shape,corr.dtype))
sample_artist = 'Cyndi Lauper'
i = numpy.where( (corr['art1']==sample_artist)|(corr['art2']==sample_artist) )[0]
corr = corr.take(i)
log.write('Sample artist correlation matrix: [corr] shape->%s\tdtype->%s'%(corr.shape,corr.dtype))

ds = h5f.create_dataset('corr', corr.shape, dtype=[('art1',vlen_dtype),('art2',vlen_dtype),('c','f8')])
ds[...] = corr
h5f.close()
log.write('Saved sample artist correlation matrix: [corr] shape->%s\tdtype->%s'%(corr.shape,corr.dtype),add_line=1)

#-- save the records in the database as well
dbs = sqlite3.connect('data/lastfm.sql3', detect_types=sqlite3.PARSE_DECLTYPES)
cur = dbs.cursor()
cur.execute("DELETE FROM artist_correlation")
cur.executemany("INSERT INTO artist_correlation VALUES (?,?,?)",(r for r in corr))
log.write('Loaded %s records in the database.'%fmt('%6d',cur.rowcount,True))
dbs.commit()
cur.close()
dbs.close()

log.write(''.ljust(150,'*'), add_line=1)
log.close()

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#
