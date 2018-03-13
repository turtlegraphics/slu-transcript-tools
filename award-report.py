"""usage: award-report <chrome server>

Produce a summary of students, given their IDs on stdin.

Creates two files:
   reportfile.txt with the report
   transcripts.txt with their transcript data
"""

import sys
import logging
import banner
import transcript

def report(t,id):
    out = ''
    out += t.studentname() + ' ' + id
    out += '\n'
    out += 'SLU GPA: %1.2f' % t.gpa()
    out += '\tMATH GPA: %1.2f' % t.gpa(['MATH'])
    out += '\tCSCI GPA: %1.2f' % t.gpa(['CSCI'])
    out += '\n'

    out += 'Major, Dept:'
    for m in t.majors():
        out += ' (' + m +')'
    out += '\n'

    if t.minors():
        out += 'Minors:'
        for m in t.minors():
            out += ' (' + m + ')'
        out += '\n'

    for dept in ['MATH','CSCI']:
        out += dept+' Courses:'
        for c in t.courses:
            if c.dept() == dept and c.number() != '495':
                out += ' [%s %s]' % (c.number(),c.grade)
        out += '\n'

    return out

if len(sys.argv) == 2:
    server = sys.argv[1]
else:
    print __doc__
    sys.exit(1)

logging.basicConfig(level=logging.INFO);

b = banner.Banner(server,user,password)
b.setTerm()

reportfile = open('reportfile.txt','w')

try:
    while True:
        id = raw_input()
        logging.info('Working student '+ id);
        b.setStudentID(id)
        raw_transcript = b.transcriptSource()

        # Debug test - saves current student data file for crash recovery
        tempfile = open("temp"+str(id)+".txt","w")
        tempfile.write(raw_transcript.encode("UTF-8"))

        logging.info(' Read ' + str(len(raw_transcript)) + ' bytes');

        t = transcript.Transcript(raw_transcript)

        reportfile.write( '-'*50+'\n')
        reportfile.write( report(t,id) )
        reportfile.flush()

        for c in t.courses:
            print id + '\t' + str(c)

except (EOFError):
    pass

reportfile.close()
