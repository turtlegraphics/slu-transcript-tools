from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import pdb
import time

class Banner:
  def __init__(self, server, username="", password=""):
    """username and password are unused, since login must be done manually"""
    self._browser = webdriver.Chrome() 

    # Login
#    self._browser.get('https://ssoprd.slu.edu/ssomanager/c/SSB')

#    self._browser.find_element_by_name('ContentPlaceHolder1_MFALoginControl1_UserIDView_txtUserid_UiInput').send_keys(username)
#    self._browser.find_element_by_name('ContentPlaceHolder1_MFALoginControl1_UserIDView_tbxPassword_UiInput').send_keys(password)
#    self._browser.find_element_by_name('Submit').submit()

    self._browser.get('http://banner.slu.edu')
    WebDriverWait(self._browser, 120).until(EC.title_is('Main Menu'))

  def close(self):
    self._browser.close()

  def setTerm(self, term=None):
    """Set term to given string (i.e. 'Fall 2014') or current term
       if term is None."""
    if not term:  # Guess the selected term
      t = time.localtime()
      if t[1] <= 5:
        term = 'Spring %d' % (t[0])
      elif t[1] <= 7:
        term = 'Summer %d' % t[0]
      else:
        term = 'Fall %d' % (t[0])

    self._browser.find_element_by_link_text('Faculty Services').click()
    self._browser.find_element_by_link_text('Term Selection').click()

    found = False
    for option in self._browser.find_elements_by_tag_name('option'):
      if option.text.startswith(term):
        option.click()
        option.submit()
        found = True
        break
      
    if not found:
      print 'Invalid term'
      exit(0)

  def setStudentID(self, id):
    """Assumes term was previously set."""
    # navigate
    self._browser.find_element_by_link_text('Faculty Services').click()
    self._browser.find_element_by_link_text('Student Information Menu').click()
    self._browser.find_element_by_link_text('ID Selection').click()
    # enter info
    self._browser.find_element_by_id('Stu_ID').send_keys(str(id))
    self._browser.find_element_by_id('Stu_ID').submit()
    # confirm
    time.sleep(2)
    self._browser.find_element_by_xpath("//input[@type='submit'][@value='Submit']").click()
    time.sleep(2)

  def transcriptSource(self):
    """
    Return HTML source of transcript page of currently selected student
    """
    self._browser.find_element_by_link_text('Faculty Services').click()
    self._browser.find_element_by_link_text('Student Information Menu').click()
    self._browser.find_element_by_link_text('Academic Transcript').click()
    # want the default transcript
    self._browser.find_element_by_id('tprt_id').submit()
    # wait for page to load
    self._browser.find_element_by_link_text('Institution Credit')
    return self._browser.find_element_by_xpath("//*").get_attribute("outerHTML")

  def info(self):
    """Return information on student (name, email, year, degree, major, 2nd major, minor, 2nd minor)"""
    if idNum:
      try:
        return self._info[idNum]
      except:
        pass
      self.selectStudent(idNum)
    try:
      return self._info[self._idNum]
    except:
      pass

    self._click("//a[text()='Faculty Services']")
    self._click("//a[text()='Student Information Menu']")
    self._click("//a[text()='Student Information']")
    self._waitForElement("//a[text()='Student E-mail Addresses']")

    source = self._source()

    name = source.split('Information for')[1].split('return true">')[1].split('</a>')[0]
    name = name.split()[-1] + ', ' + ' '.join(name.split()[:-1])
    program = source.split('Program:')[1].split('dddefault">')[1].split('</td>')[0]
    major = source.split('Major and Department:')[1].split('dddefault">')[1].split('</td>')[0].split(',')[0]
    year = source.split('Class:')[1].split('dddefault">')[1].split('</td>')[0]
    if source.count('Major and Department:') > 1:
      secondMajor = source.split('Major and Department:')[2].split('</td>')[0].split('dddefault">')[1].split(',')[0]
    else:
      secondMajor = ''
    if len(source.split('Minor')) > 1:
      minor = source.split('Minor')[1].split('dddefault">')[1].split('</td>')[0]
    else:
      minor = ''
    if len(source.split('Minor')) > 2:
      secondMinor = source.split('Minor')[2].split('dddefault">')[1].split('</td>')[0]
    else:
      secondMinor = ''

    try:
      email = self._email[self._idNum]
    except:
      self._click("//a[text()='Student E-mail Addresses']")
      self._waitForElement("//a[text()='Student Address and Phones']")

      source = self._source()
      email = source.split('SLU Email Address')[1].split('dddefault">')[1].split('\n')[0].lower()
      self._email[self._idNum] = email

    self._info[self._idNum] = (name, email, year, program, major, secondMajor, minor, secondMinor)
    return (name, email, year, program, major, secondMajor, minor, secondMinor)

  def classList(self, crn):
    self._browser.find_element_by_link_text('Faculty Services').click()
    self._browser.find_element_by_link_text('CRN Selection').click()
    self._browser.find_element_by_link_text('Enter CRN Directly').click()
    self._browser.find_element_by_id('crn_input_id').send_keys(str(crn))
    self._browser.find_element_by_id('crn_input_id').submit()
    self._browser.find_element_by_link_text('Class List: Summary').click()
    
    lines = str(self._browser.find_element_by_class_name('datadisplaytable').text).split('\n')
    title = ' - '.join(lines[1].split(' - ')[:-1])
    prefix = lines[1].split()[-3]
    number = int(lines[1].split()[-2])
    section = int(lines[1].split()[-1])
    
    students = []
    
    table = self._browser.find_elements_by_class_name('datadisplaytable')[2]
    tableEntries = table.find_elements_by_class_name('dddefault')
    for i in range(0,len(tableEntries),12):
      try:
        print i, len(tableEntries)
        name = tableEntries[i+2].text
        sid = tableEntries[i+3].text
        major = tableEntries[i+5].text
        
        email = tableEntries[i+11].find_element_by_partial_link_text('').get_attribute('href').split('mailto:')[1]
        
        students.append((name,sid,email,major))
      except:
        print 'Error getting student info'
      
    l = self._browser.find_elements_by_partial_link_text('')
    for t in l:
      if prefix.lower() in t.text.lower():
        t.click()
        break
    
    info = [prefix, number, section, title]

    self._browser.find_element_by_partial_link_text('Return').click()
    
    return students, info
  
  def classSchedule(self, area, term):
    self._browser.find_element_by_link_text('Faculty Services').click()
    self._browser.find_element_by_link_text('Search Schedule Of Classes').click()
    
    for option in self._browser.find_elements_by_tag_name('option'):
      if option.text.startswith(term):
        option.click()
        option.submit()
        break
    
    for option in self._browser.find_elements_by_tag_name('option'):
      print 'Area', option.text
      if option.text.startswith(area):
        option.click()
        option.submit()
        break
    
    courses = []
    table = self._browser.find_element_by_class_name('datadisplaytable')  
    rows = table.find_elements_by_xpath('//tr')[1:]
    
    count = 0
    for r in rows:
      count += 1
      e = r.find_elements_by_class_name('dddefault')
      if len(e) > 3:
        crn = e[0].text
        prefix = e[1].text
        number = e[2].text
        section = e[3].text
        
        try:
          courses.append( [int(crn),prefix,int(number),int(section)] )
          print 'Found', prefix, number, section, count, len(rows)
        except:
          print 'Row invalid', count, len(rows)
      else:
        print 'Too short', count, len(rows)
    
    for i in range(len(courses)):
     if courses[i][2] in [145,150,146,180,290,305,306,314,324,362,371,408,493,140,145,150,180,224,290,293,334,344,390,408]:
#     if courses[i][2] in [141,142,143,244,132,135,405]:
      (crn, prefix, number, section) = courses[i][:4]
      page = self._browser.find_element_by_link_text(str(crn)).get_attribute('href')      
      mainHandle = self._browser.window_handles[0]
      
      self._browser.find_element_by_link_text(str(crn)).send_keys(Keys.CONTROL + 'n')
      
      for h in self._browser.window_handles:
        if h != mainHandle:
          self._browser.switch_to_window(h)
      self._browser.get(page)
      
      table = self._browser.find_elements_by_class_name('datadisplaytable')[1]
      e = table.find_elements_by_class_name('dddefault')
      
      instructor = e[6].text.split('(')[0].strip()
      try:
        instructorEmail = e[6].find_elements_by_partial_link_text('')[0].get_attribute('href').split('mailto:')[1]
      except:
        instructorEmail = 'noreply@slu.edu'
        
      print crn, prefix, number, section, instructor, instructorEmail
      courses[i].extend([instructor, instructorEmail])
      
      self._browser.close()
      self._browser.switch_to_window(mainHandle)
    
    return courses

