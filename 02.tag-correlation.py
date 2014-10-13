#!/usr/bin/env python

''' Calculate the correlation between the tags. Intermediate datasets are
    saved in the HDF5 file and the final dataset is saved in the database as
    well. Also, the Top-25 matching tag pairs are expanded into the matrix and
    plotted on the Heatmap chart.
    Load the "tag-correlation-heatmap.htm" to view the chart.

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
import os, sys, sqlite3, time, locale

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
h5f = h5py.File('data/tag-correlation-datasets.h5','w')
vlen_dtype = h5py.special_dtype(vlen=str)

#==============================================================================#
#------------------------- Load and process data ------------------------------#
#==============================================================================#

#--------------------------------------#
#-- load data and apply basic filter   #
#--------------------------------------#
''' Load the records from the artist/tag table. Apply basic filter to clean the
    marginal and outlier tags, which is also convenient to do with SQL. This
    provides more generalized values for the tags.
    The rules are:
    1. Filter out all tags with ranking (i.e count) less then 50.
    2. Filter out all tags which does not occur at least 5 times in the dataset,
       i.e. the tag must be given to at least 5 artists.
    3. Filter out all tags having the same name as the artist.
'''
log.write('Load data and apply basic filter.')
dbs = sqlite3.connect('data/lastfm.sql3', detect_types=sqlite3.PARSE_DECLTYPES)
cur = dbs.cursor()
cur.execute("""
    SELECT t.artist_name, t.tag, t.count FROM top_artist_tags t
    JOIN (SELECT t1.tag FROM top_artist_tags t1
          WHERE t1.count >= 50 GROUP BY 1 HAVING count(*) >= 5) AS jt1
    ON t.tag = jt1.tag
    WHERE t.count >= 50 AND t.artist_name <> t.tag;
    """)
recs = numpy.array([r for r in cur],dtype=[('art','O'),('tag','O'),('count','i4')])
cur.close()
dbs.close()
log.write('Loaded %s records.'%fmt('%12d',recs.shape[0],True).strip())

ds = h5f.create_dataset('recs', recs.shape, dtype=[('art',vlen_dtype),('tag',vlen_dtype),('count','i4')])
ds[...] = recs
h5f.flush()
log.write('Saved [recs] dataset.',add_line=1)

#--------------------------------------#
#-- prepare data for correlation calc  #
#--------------------------------------#

log.write('Prepare data for the correlation calc.')

#-- Get unique list of artists and tags.
unique_art  = numpy.unique( recs['art'] )
unique_tags = numpy.unique( recs['tag'] )

''' Create 2d array to hold the vector for each tag. The vector size is 2x
    the length of the list of the unique artists. First part will have the
    value 0/1, depending if the given tag is associated with the given artist.
    The second part will have the tag ranking (count) value, at the same
    position for the given artist.

    Assuming the following tuples in the basic dataset [recs]:
    (art1,tag1,90), (art1,tag2,80), (art1,tag3,60), (art1,tag4,50),
    (art2,tag1,80),                 (art2,tag3,90), (art2,tag4,70),
                    (art3,tag2,90), (art3,tag3,80), (art3,tag4,60),
    (art4,tag1,50), (art4,tag2,70), (art4,tag3,70)

    The "unique_art"  list is:  [art1,art2,art3,art4]
    The "unique_tags" list is:  [tag1,tag2,tag3,tag4]
    offset = 4
    Single tag vector is [0,0,0,0,0,0,0,0], with logical mask as
    [art1,art2,art3,art4,rank1,rank2,rank3,rank4].

    Based on the above described data, the complete matrix "tags_mx"
    will have 4 vectors with following values:
    [[1,1,0,1,90,80, 0,50],
     [1,0,1,1,80, 0,90,70],
     [1,1,1,1,60,90,80,70],
     [1,1,1,0,50,70,60, 0]]

    The sample data (tags for 1000 artists) is very small and this executes
    fast, otherwise this loop would be a strong candidate for parallel
    execution.
'''
offset  = unique_art.shape[0]
tags_mx = numpy.zeros((unique_tags.shape[0],offset*2),'i4')

for i in xrange(unique_tags.shape[0]):
    #-- find indicies for all records in the basic dataset for given tag
    idx = numpy.where( recs['tag']==unique_tags[i] )[0]
    #-- get all artists and counts for the given tag
    tag_arts  = recs['art'].take(idx)
    tag_count = recs['count'].take(idx)
    #-- find the index positions in the artist unique list, for all tag artists
    idx = unique_art.searchsorted(tag_arts)
    #-- fill in the first part of the tag vector with 1, for each artist found
    numpy.put( tags_mx[i], idx, 1 )
    #-- fill in the tag count (rank) in the second part of the tag vector
    numpy.put( tags_mx[i], idx+offset, tag_count )

ds = h5f.create_dataset('unique_art', unique_art.shape, dtype=vlen_dtype)
ds[...] = unique_art
ds = h5f.create_dataset('unique_tags', unique_tags.shape, dtype=vlen_dtype)
ds[...] = unique_tags
ds = h5f.create_dataset('tags_mx', tags_mx.shape, dtype=tags_mx.dtype)
ds[...] = tags_mx
h5f.flush()
log.write('Saved following datasets:')
log.write('unique_art:  shape->%s\tdtype->%s'%(unique_art.shape, unique_art.dtype))
log.write('unique_tags: shape->%s\tdtype->%s'%(unique_tags.shape,unique_tags.dtype))
log.write('tags_mx:     shape->%s\tdtype->%s'%(tags_mx.shape,    tags_mx.dtype), add_line=1)

#--------------------------------------#
#-- calculate tag correlation          #
#--------------------------------------#

log.write('Calculate tag correlation.')

#-- allocate full size tag matrix
corr = numpy.empty( unique_tags.shape[0]**2, dtype=[('tag1','O'),('tag2','O'),('c','f8')] )

''' Calculate correlation for each distinct pair of tag vectors. Again, in case
    of high data volume, this could be executed in parallel using the pool of
    worker processes.
'''
r = 0
for i in xrange(unique_tags.shape[0]):
    for j in xrange(i+1,unique_tags.shape[0]):
        c = numpy.corrcoef( tags_mx[i], tags_mx[j] )[0,1]
        corr[r] = (unique_tags[i],unique_tags[j],c)
        r += 1

#-- cut the array to the actual size
corr = corr[:r]

ds = h5f.create_dataset('corr', corr.shape, dtype=[('tag1',vlen_dtype),('tag2',vlen_dtype),('c','f8')])
ds[...] = corr
h5f.flush()
log.write('Saved full tag correlation matrix: [corr] shape->%s\tdtype->%s'%(corr.shape,corr.dtype))

#-- save the records in the database as well
dbs = sqlite3.connect('data/lastfm.sql3', detect_types=sqlite3.PARSE_DECLTYPES)
cur = dbs.cursor()
cur.execute("DELETE FROM tag_correlation")
cur.executemany("INSERT INTO tag_correlation VALUES (?,?,?)",(r for r in corr))
log.write('Loaded %s records in the database.'%fmt('%6d',cur.rowcount,True), add_line=1)
dbs.commit()
cur.close()
dbs.close()

#--------------------------------------#
#-- get Top25x25 tags                  #
#--------------------------------------#
''' Based on the top 25 tag pairs, use that list and expand to the full size
    25x25 matrix so we can prepare the data for the heatmap chart.
'''
log.write('Get Top-25 list.')

corr.sort(order='c')
top25 = corr[::-1][:25]

#-- get the full 25x25 matrix
top_tags = numpy.array( [(t1,t2) for t1 in top25['tag1'] for t2 in top25['tag2']],
                        dtype=[('tag1','O'),('tag2','O')])

#-- create the view for the first 2 columns (tags) on the original corr array
corr_v = numpy.ndarray( corr.shape, numpy.dtype([('tag1','O'),('tag2','O')]), corr, 0, corr.strides)

#-- get correlation records for the top tags
mask_a  = numpy.in1d( corr_v, top_tags )
top25mx = corr[mask_a]

ds = h5f.create_dataset('top25', top25.shape, dtype=[('tag1',vlen_dtype),('tag2',vlen_dtype),('c','f8')])
ds[...] = top25
ds = h5f.create_dataset('top_tags', top_tags.shape, dtype=[('tag1',vlen_dtype),('tag2',vlen_dtype)])
ds[...] = top_tags
ds = h5f.create_dataset('corr_v', corr_v.shape, dtype=[('tag1',vlen_dtype),('tag2',vlen_dtype)])
ds[...] = corr_v
ds = h5f.create_dataset('mask_a', mask_a.shape, dtype=mask_a.dtype)
ds[...] = mask_a
ds = h5f.create_dataset('top25mx', top25mx.shape, dtype=[('tag1',vlen_dtype),('tag2',vlen_dtype),('c','f8')])
ds[...] = top25mx
h5f.close()
log.write('Saved following datasets:')
log.write('top25:    shape->%s\tdtype->%s'%(top25.shape,    top25.dtype))
log.write('top_tags: shape->%s\tdtype->%s'%(top_tags.shape, top_tags.dtype))
log.write('corr_v:   shape->%s\tdtype->%s'%(corr_v.shape,   corr_v.dtype))
log.write('mask_a:   shape->%s\tdtype->%s'%(mask_a.shape,   mask_a.dtype))
log.write('top25mx:  shape->%s\tdtype->%s'%(top25mx.shape,  top25mx.dtype))
log.write(''.ljust(150,'*'), add_line=1)

#==============================================================================#
#--------------------- Prepare data for the HeatMap chart ---------------------#
#==============================================================================#

log.write('Preparing data for the HeatMap chart.',add_line=1)

#-- print all tag pairs in descending order of the correlation coef
top25mx.sort(order='c')
for r in top25mx[::-1]:
    log.write('\t%s\t%s\t%s'%(r[0].ljust(25), r[1].ljust(25), fmt('%15.12f',r[2],True)))

#-- find the longer list of tags and make it X-axis
if numpy.unique(top25mx['tag1']).shape[0] >= numpy.unique(top25mx['tag2']).shape[0]:
    x_tag = 'tag1'
    y_tag = 'tag2'
else:
    x_tag = 'tag2'
    y_tag = 'tag1'

''' Generate values for the heatmap chart:
    x_cat  = labels (tags) for the X-axis
    y_cat  = labels (tags) for the Y-axis
    values = actual correlation coefficient values
    The "values" is a list of 3-element lists, each representing the
    [X-coordinate, Y-coordinate, value].
'''
x_cat  = [str(e) for e in numpy.unique(top25mx[x_tag])]
y_cat  = [str(e) for e in numpy.unique(top25mx[y_tag])]
values = []
for x in xrange(len(x_cat)):
    for y in xrange(len(y_cat)):
        #-- find the index of the specific tag pair
        i = numpy.where( (top25mx[x_tag]==x_cat[x])&(top25mx[y_tag]==y_cat[y]) )[0]

        ''' Not all possible combinations are represented on the Heatmap
            matrix, so if found, get the actual correlation coeficient value,
            otherwise 0. For display, cut the value to 4 decimal places.
        '''
        if i.shape[0]==0:   z = 0.0
        else:               z = top25mx['c'][i[0]]
        values.append( [x,y,float('%7.4f'%z)] )

''' Read the prepared html template file and substitue the values for the
    X,Y labels and the actual data list. Save the new version, so it can
    be viewed in the browser.
'''
with open('tag-correlation-heatmap.template','r') as f:
    page = f.read()
with open('tag-correlation-heatmap.htm','w') as f:
    f.write( page%(x_cat, y_cat, values) )

log.write('Load "tag-correlation-heatmap.htm" to view the chart!',skip_line=1)
log.write(''.ljust(150,'*'), add_line=1)
log.close()

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#
