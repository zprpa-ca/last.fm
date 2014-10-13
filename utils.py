''' Utility classes and functions.

    ============================================================================
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
    ============================================================================
'''

import os, sys, urllib, json
from datetime import datetime

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#

def api_request( root_url, params ):

    req = '?'.join( (root_url,'&'.join('='.join((k,params[k])) for k in params.iterkeys())) )
    f   = urllib.urlopen( req )
    rsp = json.load(f)
    f.close()

    return rsp

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#

class ZpLog:
    ''' simple logging with options to write to file, screen or both '''

    def __init__( self, fname, mode='w' ):
        if mode=='w':
            if os.path.exists(fname): os.rename( fname, fname + '--' + datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f') + '.old.txt')
            self.logfile = open(fname,'w')
        elif mode=='a':
            self.logfile = open(fname,'a')
        self.opened = True

    def write( self, text, skip_line=None, add_line=None ):
        ''' write text as new line to both file and screen '''
        dt   = str(datetime.now())
        txt1 = ''.join(('\n',dt,'-> '))
        txt2 = ''.join((txt1,text))
        if skip_line:
            sys.stdout.write(  ''.join([txt1 for x in range(skip_line)]))
            self.logfile.write(''.join([txt1 for x in range(skip_line)]))
        sys.stdout.write(   txt2 )
        self.logfile.write( txt2 )
        if add_line:
            sys.stdout.write(  ''.join([txt1 for x in range(add_line)]))
            self.logfile.write(''.join([txt1 for x in range(add_line)]))
        sys.stdout.flush()
        self.logfile.flush()

    def write_add( self, text ):
        ''' add text at the last line, both file and screen '''
        sys.stdout.write('\033[K')
        sys.stdout.write(text)
        sys.stdout.flush()
        self.logfile.write(text)
        self.logfile.flush()

    def fwrite( self, text, skip_line=None, add_line=None ):
        ''' write text as new line to file '''
        dt   = str(datetime.now())
        txt1 = ''.join(('\n',dt,'-> '))
        txt2 = ''.join((txt1,text))
        if skip_line:
            self.logfile.write(''.join([txt1 for x in range(skip_line)]))
        self.logfile.write( txt2 )
        if add_line:
            self.logfile.write(''.join([txt1 for x in range(add_line)]))
        self.logfile.flush()

    def fwrite_add( self, text ):
        ''' add text at the last line in file '''
        self.logfile.write(text)
        self.logfile.flush()

    def write_split( self, screen_text, file_text ):
        ''' split writing text on screen and file '''
        dt = str(datetime.now())
        sys.stdout.write(''.join(('\n',dt,'-> ',screen_text)))
        sys.stdout.flush()
        self.logfile.write(''.join(('\n',dt,'-> ',screen_text,'\t',file_text)))
        self.logfile.flush()

    def write_static( self, txt, restore=True ):
        ''' write static text on the screen, without advancing the cursor. usefull for progress display.
            restore=True:   restore the cursor position back to the beggining of text [default]
        '''
        sys.stdout.write('\033[K')
        sys.stdout.write('\033[s')
        sys.stdout.write(txt)
        if restore: sys.stdout.write('\033[u')
        sys.stdout.flush()

    def tty_write( self, txt ):
        ''' write text on the screen '''
        sys.stdout.write('\033[K')
        sys.stdout.write(txt)
        sys.stdout.flush()

    def _print( self, a, skip_line=None, add_line=None ):
        ''' print array elements, tab delimited, to screen and file as new line '''
        if skip_line:
            sys.stdout.write(   ''.join(['\n' for x in range(skip_line)]) )
            self.logfile.write( ''.join(['\n' for x in range(skip_line)]) )
        sys.stdout.write(  '\n' + ''.join([str(x)+'\t' for x in a]) )
        self.logfile.write('\n' + ''.join([str(x)+'\t' for x in a]) )
        if add_line:
            sys.stdout.write(   ''.join(['\n' for x in range(add_line)]) )
            self.logfile.write( ''.join(['\n' for x in range(add_line)]) )
        sys.stdout.flush()
        self.logfile.flush()

    def write_timing( self, txt, t1, t2, out_type='FILE' ):
        ''' write formatted timing, t1 and t2 must be system time '''
        hh = '%02d'%(int((t2-t1)/3600))
        mi = '%02d'%((int((t2-t1)/60))%60)
        ss = '%06.3f'%((t2-t1)%60)
        timing = ''.join([txt,hh,':',mi,':',ss])
        if   out_type == 'ADD':     self.write_add( timing )
        elif out_type == 'FADD':    self.fwrite_add( timing )
        elif out_type == 'STATIC':  self.write_static( timing )
        elif out_type == 'FILE':    self.fwrite( timing )
        elif out_type == 'TTY':     self.write( timing )

    def write_timing1( self, cnt, total_cnt, t1, t2, out_type='FILE' ):
        ''' write formatted timing, t1 and t2 must be system time
            shows current rec counter, total rec counter and calc the estimated time to end
        '''
        tdiff = t2-t1
        hh = '%02d'%(int(tdiff/3600))
        mi = '%02d'%((int(tdiff/60))%60)
        ss = '%06.3f'%(tdiff%60)
        if cnt==0: cnt=1
        est_time = (total_cnt-cnt) * (tdiff/cnt)
        hh1 = '%02d'%(int(est_time/3600))
        mi1 = '%02d'%((int(est_time/60))%60)
        ss1 = '%06.3f'%(est_time%60)
        txt = ''.join([' rec# ',str(cnt),'/',str(total_cnt),'  elapsed: ',hh,':',mi,':',ss,'/',hh1,':',mi1,':',ss1])
        if   out_type == 'FILE':    self.fwrite( txt )
        elif out_type == 'TTY':     self.write_static( txt )

    def close( self ):
        ''' close and flush log file '''
        sys.stdout.write('\n')
        sys.stdout.flush()
        self.logfile.write('\n')
        self.logfile.close()
        self.opened = False

    def __del__( self ):
        if self.opened: self.close()
#------------------------------------------------------------------------------#

class ZpErrLog:
    ''' swap stderr and capture any error printout '''

    def __init__( self, fname, mode='w' ):
        if mode=='w':
            if os.path.exists(fname): os.rename( fname, fname + '--' + datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f') + '.old.txt')
            self.logfile = open(fname,'w')
        elif mode=='a':
            self.logfile = open(fname,'a')
        self.stderr = sys.stderr
        sys.stderr  = self

    def __del__( self ):
        self.logfile.write('\n')
        sys.stderr = self.stderr
        self.logfile.close()

    def write( self, data ):
        self.logfile.write(data)
        self.stderr.write(data)

    def flush( self ):
        self.logfile.flush()
        self.stderr.flush()

#==============================================================================#
#------------------------------------------------------------------------------#
#==============================================================================#
