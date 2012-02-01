import datetime
import time
import os

def parse_date(date):
    if isinstance(date, basestring):
        date = int(date)
    gmtime = time.gmtime(date)
    return datetime.date(gmtime.tm_year, gmtime.tm_mon, gmtime.tm_mday)


class NZBSegment(object):
    def __init__(self, bytes, number, message_id=None):
        self.bytes = int(bytes)
        self.number = int(number)
        if message_id:
            self.message_id = message_id
    
    
    def set_message_id(self, message_id):
        self.message_id = message_id



class NZBFile(object):
    def __init__(self, poster, date, subject, groups=None, segments=None):
        self.poster = poster
        self.date = parse_date(date)
        self.subject = subject
        self.groups = groups or []
        self.segments = segments or []
    
    
    def add_group(self, group):
        self.groups.append(group)
    
    
    def add_segment(self, segment):
        self.segments.append(segment)



class BaseNZBParser(object):
    def parse(self, xml):
        raise NotImplementedError



class BaseETreeNZBParser(BaseNZBParser):
    def get_etree_iter(self, xml, et=None):
        raise NotImplementedError
    
    def get_etree_module(self, et=None):
        raise NotImplementedError
    
    def parse(self, xml):
        context = self.get_etree_iter(xml)
        files, current_file, current_segment = [], None, None
        
        for event, elem in context:
            if event == "start":
                # If it's an NZBFile, create an object so that we can add the
                # appropriate stuff to it.
                if elem.tag == "{http://www.newzbin.com/DTD/2003/nzb}file":
                    current_file = NZBFile(
                        poster = elem.attrib['poster'],
                        date = elem.attrib['date'],
                        subject = elem.attrib['subject']
                    )
            
            elif event == "end":
                if elem.tag == "{http://www.newzbin.com/DTD/2003/nzb}file":
                    files.append(current_file)
                
                elif elem.tag == "{http://www.newzbin.com/DTD/2003/nzb}group":
                    current_file.add_group(elem.text)
                
                elif elem.tag == "{http://www.newzbin.com/DTD/2003/nzb}segment":
                    current_file.add_segment(
                        NZBSegment(
                            bytes = elem.attrib['bytes'],
                            number = elem.attrib['number'],
                            message_id = elem.text
                        )
                    )
                # Clear the element, we don't need it any more.
                elem.clear()
        return files
        
    def NZBtoXMLElement(self, files):
                
        etree = self.get_etree_module()
        
        nzbnode = etree.Element('nzb')
        nzbnode.attrib['xmlns'] = 'http://www.newzbin.com/DTD/2003/nzb'
        
        #Create files
        for file in files:
            #Create file
            filenode = etree.Element('file')
            filenode.attrib['poster'] = file.poster
            timeformat = '%Y-%m-%d'
            filenode.attrib['date'] = str(int(time.mktime(time.strptime(str(file.date), timeformat))))
            filenode.attrib['subject'] = file.subject
            
            #Create groups
            groupsnode = etree.Element('groups')
            for group in file.groups:
                groupnode = etree.Element('group')
                groupnode.text = group
                groupsnode.append(groupnode)
            
            filenode.append(groupsnode)
            
            #Create segments
            segmentsnode = etree.Element('segments')
            for segment in file.segments:
                segmentnode = etree.Element('segment')
                segmentnode.attrib['bytes'] = str(segment.bytes)
                segmentnode.attrib['number'] = str(segment.number)
                segmentnode.text = segment.message_id
                segmentsnode.append(segmentnode)
            filenode.append(segmentsnode)
            
            nzbnode.append(filenode)
        
        def indent(elem, level=0):
            i = "\n" + level*"  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    indent(elem, level+1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i
        
        indent(nzbnode)
        return nzbnode

    def writetostring(self, files):
        etree = self.get_etree_module()
        return etree.tostring(self.NZBtoXMLElement(files), 'iso-8859-1')
        
    def writetofile(self, files, path):
        if os.access(os.path.dirname(os.path.abspath(path)), os.W_OK):
            nzbelem = self.writetostring(files)
            try:
                outfile = open(path, 'w')
                outfile.write(nzbelem)
                outfile.close()
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
        else:
            print 'Path (' + path + ') does not exist!'
        
            
            