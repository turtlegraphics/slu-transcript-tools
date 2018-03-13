# transcript.py
#
# Class for parsing transcript info
# 
import re
import logging

"""Class that stores transcript information, built from the source of
   the banner transcript display page.
   This allows for manual or automatic use."""

class Course:
  def __init__(self,name,title,term,grade,hours,qp):
    self.name = name if name else ''
    self.title = title if title else ''
    self.term = term if term else ''
    self.grade = grade if grade else ''
    self.hours = hours if hours else 0
    self.qp = qp if qp else 0

  def __str__(self):
    return '\t'.join([self.name,self.title,self.term,self.grade,str(self.hours),str(self.qp)])

  def dept(self):
    """Return department name (CSCI, MATH, ART, ..)"""
    return self.name.split(' ')[0]

  def number(self):
    """Return course number (110, 140,...) as a string."""
    return self.name.split(' ')[1]

  def section(self):
    """Return course section (01,.) as a string."""
    return self.name.split(' ')[3]

class Transcript:
  def __init__(self,source):
    """
    Create a new transcript object from HTML source of transcript page.
    (course, course title, term, grade, hours, quality points )
    If transfer/in progress the grade will be 'Transfer'/'Current'.
    """
    source = source.encode('ascii','replace')
    self.source = source.replace('&amp;','&').upper()
    
    self._parse()

  def __str__(self):
    return '\n'.join([str(course) for course in self.courses])

  def gpa(self,departments=None):
    """Return gpa total for given list of departments, or overall GPA if departments is None"""
    if departments is None:
      return self._gpa

    qp = 0
    hours = 0
    for c in self.courses:
      if c.dept() in departments:
        if c.grade not in ['Transfer','Current','AU']:
          if c.qp != None:
            qp += c.qp
          if c.hours != None:
            hours += c.hours

    if hours > 0:
      return qp/float(hours)
    else:
      return 0

  def majors(self):
    """Return a list of the student's majors"""
    return [p for (deg,p) in self._programs if deg == 'major']

  def minors(self):
    """Return a list of the student's minors"""
    return [p for (deg,p) in self._programs if deg == 'minor']

  def studentname(self):
    """Return the student's name."""
    return self._studentname

  def _parseCourse(self,l):
    """Take a line, and if it seems to be a course, split it
       into the data fields for that course.  Returns the list
       of field strings."""
    if not l.startswith('<TD CLASS="DDDEFAULT">'):
      return None

    fields = []
    # first split on TD rows, cleaning off the first tag
    for f in l.split('DDDEFAULT">')[1:]:
      s = f.split('</TD>')[0]  # strip off tail tag
      if s.startswith('<P'):
        # numeric values get wrapped in another <p> tag, this strips it
        s = f.split('ALIGNTEXT">')[1].split('</P>')[0]
      fields.append(s)

    # logging.debug('Got fields:\n' + str(fields))
    return fields

  def _getSection(self,which):
    """Cut a section of HTML out of the source and split into table rows.
    Sections are numbered as in the self.section array defined in parse.
    Returns an array of strings, one per table row.  Returns the empty list
    if the section is not found."""
    lines = []
    if self.sechtml[which] in self.source:
      try:
        raw = self.source.split(self.sechtml[which+1])[0].split(self.sechtml[which])[1]
      except IndexError:
        raw = '\n'.join(self.source.split(self.sechtml[which])[1:])

      logging.info(' PARSING SECTION ' + self.sections[which])
      lines = raw.split('<TR>')
      lines = [l.strip() for l in lines]

    return lines

  def _checkTerm(self,l):
    """Take a line and if it appears to define a Term, set self.term"""
    target = '<SPAN CLASS="FIELDORANGETEXTBOLD">'
    if target in l:
      rawterm = l.split(target)[1].split('</SPAN>')[0]
      rawterm = rawterm.strip('TERM:')
      rawterm = rawterm.replace(',','')
      self.term = rawterm.strip()
      logging.info('  Switching to term: '+self.term)
      return self.term
    else:
      return None

  def _parse(self):
    """
    Parse transcript information from Banner's disgusting HTML,
    which should be stored in self.source
    """
    logging.debug(self.source)

    # titles of key sections in the transcript, in order of appearance
    self.sections = [
      'student information',
      'degrees',
      'transfer credit accepted by institution',
      'institution credit',
      'transcript totals',
      'courses in progress'
      ]
    # put section titles into correct form to find in the html
    self.sechtml = [('scope="colgroup">'+s).upper() for s in self.sections]

    # Student name
    nameline = re.search('ADDRESS.*</A>',self.source,re.IGNORECASE).group()
    self._studentname = re.search('>.*<',nameline).group()[1:-1]
    logging.info(' STARTING TO PARSE STUDENT '+self._studentname)

    # Courses
    self.courses = []
    self.term = None
    for block in [2,3,5]:
      # transfer, institution, in progress
      lines = self._getSection(block)
      for l in lines:
        self._checkTerm(l)
        fields = self._parseCourse(l)
        if fields:
          course = fields[0] + ' ' + fields[1]
          title = fields[3]
          qp = None
          if block == 2:  # transfer
            title = fields[2]
            hours = float(fields[4])
            grade = 'Transfer'
          elif block == 3:  # institution
            grade = fields[4]
            hours = float(fields[5])
            qp = float(fields[6])
          elif block == 5:  # in progress
            hours = float(fields[4])
            grade = 'Current'

          logging.info('   Adding course: ' + course)
          self.courses.append(Course(course, title, self.term, grade, hours, qp))

    # Overall GPA
    lines = self._getSection(4)  # transcript totals
    oline = [l for l in lines if l.find('OVERALL')>0][0]
    gpaline = oline.split('<TD')[-1]
    self._gpa = float(re.search('\d\.\d\d',gpaline).group())
    logging.info('   Got GPA = ' + str(self._gpa))

    # Majors, minors
    lines = self._getSection(0) # student information

    self._programs = []
    for program in ['major','minor']:
      lines = [l for l in lines if l.find(program.upper())>0]
      for m in lines:
        p = re.search('DDDEFAULT">.*</TD>',m).group()[11:-5]
        self._programs.append((program,p))
        logging.info('   Adding ' + program + ': ' + p);

if __name__=="__main__":
  import sys

  logging.basicConfig(level=logging.INFO);
  try:
    raw = open(sys.argv[1]).read()
  except IndexError:
    print 'Usage: transcript.py <raw transcript html file>'
    sys.exit()
    
  t = Transcript(raw)
  print
  print 'Student:',t.studentname()
  print 'SLU GPA:',t.gpa()
  print 'Math GPA:',t.gpa(['MATH'])
  print 'CS GPA:',t.gpa(['CSCI'])
  print 'Major GPA:',t.gpa(['MATH','CSCI'])
  for m in t.majors():
    print 'Major:',m
  for m in t.minors():
    print 'Minor:',m
  print t
