#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib 
import getpass

EXCP_BEGIN = '''    
    #
    #add catch command to catch exception to avoid interrupt of buddy running
    #
    if {[catch {

'''

EXCP_END = r'''    
    
    } msg details]} {
        buddy::FAIL "Got exception: \n$msg\nDetails:\n$details"
    } 
    #end of catch

'''



def email(pathname):

    def send (exception, trace):
        content = '''
Exception: %s
_________
Details: %s
_________
Pathname: %s
_________
%s
''' % (exception, trace, pathname, file(pathname).read())
        author = 'wuli2@cisco.com'
        
        top = MIMEText(content)
        top['from'] = getpass.getuser()
        top['to'] = author
        top['subject'] = 'addexcpthandle.py parsing file failed'
        
        smtp = smtplib.SMTP('outbound.cisco.com')
        smtp.sendmail(getpass.getuser(), author, top.as_string())

    return send

class Finder:
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)
        self.count = 0
        self.scaning = False

    def count_chr_in_str(self, s, char):
        count = 0
        pos   = 0

        while True:
            index = s.find(char, pos)
            if index == -1:
                break
            
            count += 1
            pos = index + 1

        return count

    def count_left_brace(self, s):
        return self.count_chr_in_str(s, '{')

    def count_right_brace(self, s):
        return self.count_chr_in_str(s, '}')

    
    def find_proc_begin(self, line):
        if self.scaning:       #already begin scaning the end of proc, skip
            return False

        if self.pattern.match(line):
            self.count = 1
            self.scaning = True
            return True

        return False
        
    def find_proc_end(self, line):
        if self.scaning:
            self.count += self.count_left_brace(line)
            self.count -= self.count_right_brace(line)

            if self.count == 0:   #all { } matched, end of proc
                self.scaning = False
                return True

        return False



def subst_file_content(pathname):

    finder = Finder(r"\s*proc\s+:*\w+.*{\s*")

    content = ''
    with open(pathname) as inf:
        for line in inf:
            if finder.find_proc_begin(line):
                content += (line + EXCP_BEGIN)
                continue


            if finder.find_proc_end(line):
                content += EXCP_END

            content += line

                
    with open(pathname + ".new", "w") as outf:
        outf.write(content)
                
            
        
def excepthook(type, value, tb):
    import traceback
    msg = str(value)
    details = ''
    for line in traceback.format_tb(tb):
        details += line
    send_email(msg, details)
    print "Parsing file countered a exception: %s" % msg
    print details


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: addexcpthandle.py  your_script.py"
        sys.exit(1)

    send_email = email(sys.argv[1])
    sys.excepthook = excepthook

    subst_file_content(sys.argv[1])
        
    
