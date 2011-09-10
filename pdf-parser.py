#!/usr/bin/env python
"""

pdf-parser, use it to parse a PDF document

Source code put in public domain by Didier Stevens, no Copyright
https://DidierStevens.com
Use at your own risk

History:
  2008/05/02: continue
  2008/05/03: continue
  2008/06/02: streams
  2008/10/19: refactor, grep & extract functionality
  2008/10/20: reference
  2008/10/21: cleanup
  2008/11/12: V0.3 dictionary parser
  2008/11/13: option elements
  2008/11/14: continue
  2009/05/05: added /ASCIIHexDecode support (thanks Justin Prosco)
  2009/05/11: V0.3.1 updated usage, added --verbose and --extract
  2009/07/16: V0.3.2 Added Canonicalize (thanks Justin Prosco)
  2009/07/18: bugfix EqualCanonical
  2009/07/24: V0.3.3 Added --hash option
  2009/07/25: EqualCanonical for option --type, added option --nocanonicalizedoutput
  2009/07/28: V0.3.4 Added ASCII85Decode support
  2009/08/01: V0.3.5 Updated ASCIIHexDecode to support whitespace obfuscation
  
Todo:
  - handle printf todo

"""

__author__ = 'Didier Stevens'
__version__ = '0.3.5'
__date__ = '2009/08/01'

import re
import optparse
import zlib
import binascii
import hashlib

CHAR_WHITESPACE = 1
CHAR_DELIMITER = 2
CHAR_REGULAR = 3

CONTEXT_NONE = 1
CONTEXT_OBJ = 2
CONTEXT_XREF = 3
CONTEXT_TRAILER = 4

PDF_ELEMENT_COMMENT = 1
PDF_ELEMENT_INDIRECT_OBJECT = 2
PDF_ELEMENT_XREF = 3
PDF_ELEMENT_TRAILER = 4
PDF_ELEMENT_STARTXREF = 5
PDF_ELEMENT_MALFORMED = 6

def CopyWithoutWhiteSpace(content):
    result = []
    for token in content:
        if token[0] != CHAR_WHITESPACE:
            result.append(token)
    return result

def Obj2Str(content):
    return ''.join(map(lambda x: repr(x[1])[1:-1], CopyWithoutWhiteSpace(content)))
    
class cPDFDocument:
    def __init__(self, file):
        self.file = file
        self.infile = open(file, 'rb')
        self.ungetted = []
        self.position = -1

    def byte(self):
        if len(self.ungetted) != 0:
            self.position += 1
            return self.ungetted.pop()
        inbyte = self.infile.read(1)
        if not inbyte:
            self.infile.close()
            return None
        self.position += 1
        return ord(inbyte)

    def unget(self, byte):
        self.position -= 1
        self.ungetted.append(byte)

def CharacterClass(byte):
    if byte == 0 or byte == 9 or byte == 10 or byte == 12 or byte == 13 or byte == 32:
        return CHAR_WHITESPACE
    if byte == 0x28 or byte == 0x29 or byte == 0x3C or byte == 0x3E or byte == 0x5B or byte == 0x5D or byte == 0x7B or byte == 0x7D or byte == 0x2F or byte == 0x25:
        return CHAR_DELIMITER
    return CHAR_REGULAR

def IsNumeric(str):
    return re.match('^[0-9]+', str)
    
class cPDFTokenizer:
    def __init__(self, file):
        self.oPDF = cPDFDocument(file)
        self.ungetted = []
        
    def Token(self):
        if len(self.ungetted) != 0:
            return self.ungetted.pop()
        if self.oPDF == None:
            return None
        self.byte = self.oPDF.byte()
        if self.byte == None:
            self.oPDF = None
            return None
        elif CharacterClass(self.byte) == CHAR_WHITESPACE:
            self.token = ''
            while self.byte != None and CharacterClass(self.byte) == CHAR_WHITESPACE:
                self.token = self.token + chr(self.byte)
                self.byte = self.oPDF.byte()
            if self.byte != None:
                self.oPDF.unget(self.byte)
            else:
                self.oPDF = None
            return (CHAR_WHITESPACE, self.token)
        elif CharacterClass(self.byte) == CHAR_REGULAR:
            self.token = ''
            while self.byte != None and CharacterClass(self.byte) == CHAR_REGULAR:
                self.token = self.token + chr(self.byte)
                self.byte = self.oPDF.byte()
            if self.byte != None:
                self.oPDF.unget(self.byte)
            else:
                self.oPDF = None
            return (CHAR_REGULAR, self.token)
        else:
            if self.byte == 0x3C:
                self.byte = self.oPDF.byte()
                if self.byte == 0x3C:
                    return (CHAR_DELIMITER, '<<')
                else:
                    self.oPDF.unget(self.byte)
                    return (CHAR_DELIMITER, '<')
            elif self.byte == 0x3E:
                self.byte = self.oPDF.byte()
                if self.byte == 0x3E:
                    return (CHAR_DELIMITER, '>>')
                else:
                    self.oPDF.unget(self.byte)
                    return (CHAR_DELIMITER, '>')
            elif self.byte == 0x25:
                self.token = ''
                while self.byte != None:
                    self.token = self.token + chr(self.byte)
                    if self.byte == 10 or self.byte == 13:
                        self.byte = self.oPDF.byte()
                        break
                    self.byte = self.oPDF.byte()
                if self.byte != None:
                    if self.byte == 10:
                        self.token = self.token + chr(self.byte)
                    else:
                        self.oPDF.unget(self.byte)
                else:
                    self.oPDF = None
                return (CHAR_DELIMITER, self.token)
            return (CHAR_DELIMITER, chr(self.byte))

    def TokenIgnoreWhiteSpace(self):
        token = self.Token()
        while token != None and token[0] == CHAR_WHITESPACE:
            token = self.Token()
        return token

    def unget(self, byte):
        self.ungetted.append(byte)

class cPDFParser:
    def __init__(self, file, verbose=False, extract=None):
        self.context = CONTEXT_NONE
        self.content = []
        self.oPDFTokenizer = cPDFTokenizer(file)
        self.verbose = verbose
        self.extract = extract
        
    def GetObject(self):
        while True:
            if self.context == CONTEXT_OBJ:
                self.token = self.oPDFTokenizer.Token()
            else:
                self.token = self.oPDFTokenizer.TokenIgnoreWhiteSpace()
            if self.token:
                if self.token[0] == CHAR_DELIMITER:
                    if self.token[1][0] == '%':
                        if self.context == CONTEXT_OBJ:
                            self.content.append(self.token)
                        else:
                            return cPDFElementComment(self.token[1])
                    elif self.token[1] == '/':
                        self.token2 = self.oPDFTokenizer.Token()
                        if self.token2[0] == CHAR_REGULAR:
                            if self.context != CONTEXT_NONE:
                                self.content.append((CHAR_DELIMITER, self.token[1] + self.token2[1]))
                            elif self.verbose:
                                print 'todo 1: %s' % (self.token[1] + self.token2[1])
                        else:
                            self.oPDFTokenizer.unget(self.token2)
                            if self.context != CONTEXT_NONE:
                                self.content.append(self.token)
                            elif self.verbose:
                                print 'todo 2: %d %s' % (self.token[0], repr(self.token[1]))
                    elif self.context != CONTEXT_NONE:
                        self.content.append(self.token)
                    elif self.verbose:
                        print 'todo 3: %d %s' % (self.token[0], repr(self.token[1]))
                elif self.token[0] == CHAR_WHITESPACE:
                    if self.context != CONTEXT_NONE:
                        self.content.append(self.token)
                    elif self.verbose:
                        print 'todo 4: %d %s' % (self.token[0], repr(self.token[1]))
                else:
                    if self.context == CONTEXT_OBJ:
                        if self.token[1] == 'endobj':
                            self.oPDFElementIndirectObject = cPDFElementIndirectObject(self.objectId, self.objectVersion, self.content)
                            self.context = CONTEXT_NONE
                            self.content = []
                            return self.oPDFElementIndirectObject
                        else:
                            self.content.append(self.token)
                    elif self.context == CONTEXT_TRAILER:
                        if self.token[1] == 'startxref' or self.token[1] == 'xref':
                            self.oPDFElementTrailer = cPDFElementTrailer(self.content)
                            self.oPDFTokenizer.unget(self.token)
                            self.context = CONTEXT_NONE
                            self.content = []
                            return self.oPDFElementTrailer
                        else:
                            self.content.append(self.token)
                    elif self.context == CONTEXT_XREF:
                        if self.token[1] == 'trailer' or self.token[1] == 'xref':
                            self.oPDFElementXref = cPDFElementXref(self.content)
                            self.oPDFTokenizer.unget(self.token)
                            self.context = CONTEXT_NONE
                            self.content = []
                            return self.oPDFElementXref
                        else:
                            self.content.append(self.token)
                    else:
                        if IsNumeric(self.token[1]):
                            self.token2 = self.oPDFTokenizer.TokenIgnoreWhiteSpace()
                            if IsNumeric(self.token2[1]):
                                self.token3 = self.oPDFTokenizer.TokenIgnoreWhiteSpace()
                                if self.token3[1] == 'obj':
                                    self.objectId = eval(self.token[1])
                                    self.objectVersion = eval(self.token2[1])
                                    self.context = CONTEXT_OBJ
                                else:
                                    self.oPDFTokenizer.unget(self.token3)
                                    self.oPDFTokenizer.unget(self.token2)
                                    if self.verbose:
                                        print 'todo 6: %d %s' % (self.token[0], repr(self.token[1]))
                            else:
                                self.oPDFTokenizer.unget(self.token2)
                                if self.verbose:
                                    print 'todo 7: %d %s' % (self.token[0], repr(self.token[1]))
                        elif self.token[1] == 'trailer':
                            self.context = CONTEXT_TRAILER
                            self.content = [self.token]
                        elif self.token[1] == 'xref':
                            self.context = CONTEXT_XREF
                            self.content = [self.token]
                        elif self.token[1] == 'startxref':
                            self.token2 = self.oPDFTokenizer.TokenIgnoreWhiteSpace()
                            if IsNumeric(self.token2[1]):
                                return cPDFElementStartxref(eval(self.token2[1]))
                            else:
                                self.oPDFTokenizer.unget(self.token2)
                                if self.verbose:
                                    print 'todo 9: %d %s' % (self.token[0], repr(self.token[1]))
                        elif self.extract:
                            self.bytes = ''
                            while self.token:
                                self.bytes += self.token[1]
                                self.token = self.oPDFTokenizer.Token()
                            return cPDFElementMalformed(self.bytes)
                        elif self.verbose:
                            print 'todo 10: %d %s' % (self.token[0], repr(self.token[1]))
            else:
                break

class cPDFElementComment:
    def __init__(self, comment):
        self.type = PDF_ELEMENT_COMMENT
        self.comment = comment
#                        if re.match('^%PDF-[0-9]\.[0-9]', self.token[1]):
#                            print repr(self.token[1])
#                        elif re.match('^%%EOF', self.token[1]):
#                            print repr(self.token[1])

class cPDFElementXref:
    def __init__(self, content):
        self.type = PDF_ELEMENT_XREF
        self.content = content

class cPDFElementTrailer:
    def __init__(self, content):
        self.type = PDF_ELEMENT_TRAILER
        self.content = content

class cPDFElementIndirectObject:
    def __init__(self, id, version, content):
        self.type = PDF_ELEMENT_INDIRECT_OBJECT
        self.id = id
        self.version = version
        self.content = content

    def GetType(self):
        content = CopyWithoutWhiteSpace(self.content)
        dictionary = 0
        for i in range(0, len(content)):
            if content[i][0] == CHAR_DELIMITER and content[i][1] == '<<':
                dictionary += 1
            if content[i][0] == CHAR_DELIMITER and content[i][1] == '>>':
                dictionary -= 1
            if dictionary == 1 and content[i][0] == CHAR_DELIMITER and EqualCanonical(content[i][1], '/Type') and i < len(content) - 1:
                return content[i+1][1]
        return ''

    def GetReferences(self):
        content = CopyWithoutWhiteSpace(self.content)
        references = []
        for i in range(0, len(content)):
            if i > 1 and content[i][0] == CHAR_REGULAR and content[i][1] == 'R' and content[i-2][0] == CHAR_REGULAR and IsNumeric(content[i-2][1]) and content[i-1][0] == CHAR_REGULAR and IsNumeric(content[i-1][1]):
                references.append((content[i-2][1], content[i-1][1], content[i][1]))
        return references

    def References(self, index):
        for ref in self.GetReferences():
            if ref[0] == index:
                return True
        return False
        
    def ContainsStream(self):
        for i in range(0, len(self.content)):
            if self.content[i][0] == CHAR_REGULAR and self.content[i][1] == 'stream':
                return self.content[0:i]
        return False

    def Contains(self, keyword):
        data = ''
        for i in range(0, len(self.content)):
            if self.content[i][1] == 'stream':
                break
            else:
                data += Canonicalize(self.content[i][1])
        return data.upper().find(keyword.upper()) != -1

    def FilterStream(self):
        state = 'start'
        countDirectories = 0
        data = ''
        filters = []
        for i in range(0, len(self.content)):
            if state == 'start':
                if self.content[i][0] == CHAR_DELIMITER and self.content[i][1] == '<<':
                    countDirectories += 1
                if self.content[i][0] == CHAR_DELIMITER and self.content[i][1] == '>>':
                    countDirectories -= 1
                if countDirectories == 1 and self.content[i][0] == CHAR_DELIMITER and EqualCanonical(self.content[i][1], '/Filter'):
                    state = 'filter'
            elif state == 'filter':
                if self.content[i][0] == CHAR_DELIMITER and self.content[i][1][0] == '/':
                    filters = [self.content[i][1]]
                    state = 'search-stream'
                elif self.content[i][0] == CHAR_DELIMITER and self.content[i][1] == '[':
                    state = 'filter-list'
            elif state == 'filter-list':
                if self.content[i][0] == CHAR_DELIMITER and self.content[i][1][0] == '/':
                    filters.append(self.content[i][1])
                elif self.content[i][0] == CHAR_DELIMITER and self.content[i][1] == ']':
                    state = 'search-stream'
            elif state == 'search-stream':
                if self.content[i][0] == CHAR_REGULAR and self.content[i][1] == 'stream':
                    state = 'stream-whitespace'
            elif state == 'stream-whitespace':
                if self.content[i][0] != CHAR_WHITESPACE:
                    data += self.content[i][1]
                state = 'stream-concat'
            elif state == 'stream-concat':
                if self.content[i][0] == CHAR_REGULAR and self.content[i][1] == 'endstream':
                    return self.Decompress(data, filters)
                else:
                    data += self.content[i][1]
            else:
                return 'Unexpected filter state'
        return filters

    def Decompress(self, data, filters):
        for filter in filters:
            if EqualCanonical(filter, '/FlateDecode') or EqualCanonical(filter, '/Fl'):
                try:
                    data = FlateDecode(data)
                except:
                    return 'FlateDecode decompress failed'
            elif EqualCanonical(filter, '/ASCIIHexDecode') or EqualCanonical(filter, '/AHx'):
                try:
                    data = ASCIIHexDecode(data)
                except:
                    return 'ASCIIHexDecode decompress failed'
            elif EqualCanonical(filter, '/ASCII85Decode') or EqualCanonical(filter, '/A85'):
                try:
                    data = ASCII85Decode(data.rstrip('>'))
                except:
                    return 'ASCII85Decode decompress failed'
#            elif i.startswith('/LZW')                       # LZWDecode
#            elif i.startswith('/R')                         # RunLevelDecode
#            elif i.startswith('/CC')                        # CCITTFaxDecode
#            elif i.startswith('/DCT')                       # DCTDecode
            else:
                return 'Unsupported filter: %s' % repr(filters)
        if len(filters) == 0:
            return 'No filters'
        else:
            return data

class cPDFElementStartxref:
    def __init__(self, index):
        self.type = PDF_ELEMENT_STARTXREF
        self.index = index

class cPDFElementMalformed:
    def __init__(self, content):
        self.type = PDF_ELEMENT_MALFORMED
        self.content = content

def TrimLWhiteSpace(data):
    while data[0][0] == CHAR_WHITESPACE:
        data = data[1:]
    return data
    
def TrimRWhiteSpace(data):
    while data[-1][0] == CHAR_WHITESPACE:
        data = data[:-1]
    return data
    
class cPDFParseDictionary:
    def __init__(self, content, nocanonicalizedoutput):
        self.content = content
        self.nocanonicalizedoutput = nocanonicalizedoutput
        dataTrimmed = TrimLWhiteSpace(TrimRWhiteSpace(self.content))
        if self.isOpenDictionary(dataTrimmed[0]) and self.isCloseDictionary(dataTrimmed[-1]):
            self.parsed = self.ParseDictionary(dataTrimmed)
        else:
            self.parsed = None

    def isOpenDictionary(self, token):
        return token[0] == CHAR_DELIMITER and token[1] == '<<'
        
    def isCloseDictionary(self, token):
        return token[0] == CHAR_DELIMITER and token[1] == '>>'
        
    def ParseDictionary(self, tokens):
        state = 0 # start
        dictionary = []
        while tokens != []:
            if state == 0:
                if self.isOpenDictionary(tokens[0]):
                    state = 1
                else:
                    return None
            elif state == 1:
                if self.isOpenDictionary(tokens[0]):
                    pass
                elif self.isCloseDictionary(tokens[0]):
                    return dictionary
                elif tokens[0][0] != CHAR_WHITESPACE:
                    key = ConditionalCanonicalize(tokens[0][1], self.nocanonicalizedoutput)
                    value = []
                    state = 2
            elif state == 2:
                if self.isOpenDictionary(tokens[0]):
                    pass
                elif self.isCloseDictionary(tokens[0]):
                    dictionary.append((key, value))
                    return dictionary
                elif value == [] and tokens[0][0] == CHAR_WHITESPACE:
                    pass
                elif value != [] and tokens[0][1][0] == '/':
                    dictionary.append((key, value))
                    key = ConditionalCanonicalize(tokens[0][1], self.nocanonicalizedoutput)
                    value = []
                    state = 2
                else:
                    value.append(ConditionalCanonicalize(tokens[0][1], self.nocanonicalizedoutput))
            tokens = tokens[1:]

    def retrieve(self):
        return self.parsed

    def PrettyPrint(self, prefix):
        if self.parsed != None:
            print '%s<<' % prefix
            for e in self.parsed:
                print '%s  %s %s' % (prefix, e[0], ''.join(e[1]))
            print '%s>>' % prefix

def FormatOutput(data, raw):
    if raw:
        if type(data) == type([]):
            return ''.join(map(lambda x: x[1], data))
        else:        
            return data
    else:
        return repr(data)
        
def PrintObject(object, options):
    print 'obj %d %d' % (object.id, object.version)
    print ' Type: %s' % ConditionalCanonicalize(object.GetType(), options.nocanonicalizedoutput)
    print ' Referencing: %s' % ', '.join(map(lambda x: '%s %s %s' % x, object.GetReferences()))
    stream = object.ContainsStream()
    oPDFParseDictionary = None
    if stream:
        print ' Contains stream'
        print ' %s' % FormatOutput(stream, options.raw)
        oPDFParseDictionary = cPDFParseDictionary(stream, options.nocanonicalizedoutput)
    else:
        print ' %s' % FormatOutput(object.content, options.raw)
        oPDFParseDictionary = cPDFParseDictionary(object.content, options.nocanonicalizedoutput)
    print
    oPDFParseDictionary.PrettyPrint(' ')
    print
    if options.filter:
        filtered = object.FilterStream()
        if filtered == []:
            print ' %s' % FormatOutput(object.content, options.raw)
        else:
            print ' %s' % FormatOutput(filtered, options.raw)
    print
    return

def Canonicalize(sIn):
    if sIn == "":
        return sIn
    elif sIn[0] != '/':
        return sIn
    elif sIn.find('#') == -1:
        return sIn
    else:
        i = 0
        iLen = len(sIn)
        sCanonical = ''
        while i < iLen:
            if sIn[i] == '#' and i < iLen - 2:
                try:
                    sCanonical += chr(int(sIn[i+1:i+3], 16))
                    i += 2
                except:
                    sCanonical += sIn[i]
            else:
                sCanonical += sIn[i]
            i += 1
        return sCanonical
        
def EqualCanonical(s1, s2):
    return Canonicalize(s1) == s2

def ConditionalCanonicalize(sIn, nocanonicalizedoutput):
    if nocanonicalizedoutput:
        return sIn
    else:
        return Canonicalize(sIn)

# http://code.google.com/p/pdfminerr/source/browse/trunk/pdfminer/pdfminer/ascii85.py
def ASCII85Decode(data):
  import struct
  n = b = 0
  out = ''
  for c in data:
    if '!' <= c and c <= 'u':
      n += 1
      b = b*85+(ord(c)-33)
      if n == 5:
        out += struct.pack('>L',b)
        n = b = 0
    elif c == 'z':
      assert n == 0
      out += '\0\0\0\0'
    elif c == '~':
      if n:
        for _ in range(5-n):
          b = b*85+84
        out += struct.pack('>L',b)[:n-1]
      break
  return out

def ASCIIHexDecode(data):
    return binascii.unhexlify(''.join([c for c in data if c not in ' \t\n\r']).rstrip('>'))

def FlateDecode(data):
    return zlib.decompress(data)

def Main():
    """pdf-parser, use it to parse a PDF document
    """

    oParser = optparse.OptionParser(usage='usage: %prog [options] pdf-file', version='%prog ' + __version__)
    oParser.add_option('-s', '--search', help='string to search in indirect objects (except streams)')
    oParser.add_option('-f', '--filter', action='store_true', default=False, help='pass stream object through filters (FlateDecode, ASCIIHexDecode and ASCII85Decode only)')
    oParser.add_option('-o', '--object', help='id of indirect object to select (version independent)')
    oParser.add_option('-r', '--reference', help='id of indirect object being referenced (version independent)')
    oParser.add_option('-e', '--elements', help='type of elements to select (cxtsi)')
    oParser.add_option('-w', '--raw', action='store_true', default=False, help='raw output for data and filters')
    oParser.add_option('-a', '--stats', action='store_true', default=False, help='display stats for pdf document')
    oParser.add_option('-t', '--type', help='type of indirect object to select')
    oParser.add_option('-v', '--verbose', action='store_true', default=False, help='display malformed PDF elements')
    oParser.add_option('-x', '--extract', help='filename to extract to')
    oParser.add_option('-H', '--hash', action='store_true', default=False, help='display hash of objects')
    oParser.add_option('-n', '--nocanonicalizedoutput', action='store_true', default=False, help='do not canonicalize the output')
    (options, args) = oParser.parse_args()

    if len(args) != 1:
        oParser.print_help()
        print ''
        print '  pdf-parser, use it to parse a PDF document'
        print '  Source code put in the public domain by Didier Stevens, no Copyright'
        print '  Use at your own risk'
        print '  https://DidierStevens.com'
    
    else:
        oPDFParser = cPDFParser(args[0], options.verbose, options.extract)
        cntComment = 0
        cntXref = 0
        cntTrailer = 0
        cntStartXref = 0
        cntIndirectObject = 0
        dicObjectTypes = {}

        selectComment = False
        selectXref = False
        selectTrailer = False
        selectStartXref = False
        selectIndirectObject = False
        if options.elements:
            for c in options.elements:
                if c == 'c':
                    selectComment = True
                elif c == 'x':
                    selectXref = True
                elif c == 't':
                    selectTrailer = True
                elif c == 's':
                    selectStartXref = True
                elif c == 'i':
                    selectIndirectObject = True
                else:
                    print 'Error: unknown --elements value %s' % c
                    return
        else:
            selectIndirectObject = True
            if not options.search and not options.object and not options.reference and not options.type:
                selectComment = True
                selectXref = True
                selectTrailer = True
                selectStartXref = True

        if options.type == '-':
            optionsType = ''
        else:
            optionsType = options.type

        while True:
            object = oPDFParser.GetObject()
            if object != None:
                if options.stats:
                    if object.type == PDF_ELEMENT_COMMENT:
                        cntComment += 1
                    elif object.type == PDF_ELEMENT_XREF:
                        cntXref += 1
                    elif object.type == PDF_ELEMENT_TRAILER:
                        cntTrailer += 1
                    elif object.type == PDF_ELEMENT_STARTXREF:
                        cntStartXref += 1
                    elif object.type == PDF_ELEMENT_INDIRECT_OBJECT:
                        cntIndirectObject += 1
                        type = object.GetType()
                        if not type in dicObjectTypes:
                            dicObjectTypes[type] = [object.id]
                        else:
                            dicObjectTypes[type].append(object.id)
                else:
                    if object.type == PDF_ELEMENT_COMMENT and selectComment:
                        print 'PDF Comment %s' % FormatOutput(object.comment, options.raw)
                        print
                    elif object.type == PDF_ELEMENT_XREF and selectXref:
                        print 'xref %s' % FormatOutput(object.content, options.raw)
                        print
                    elif object.type == PDF_ELEMENT_TRAILER and selectTrailer:
                        oPDFParseDictionary = cPDFParseDictionary(object.content[1:], options.nocanonicalizedoutput)
                        if oPDFParseDictionary == None:
                            print 'trailer %s' % FormatOutput(object.content, options.raw)
                        else:
                            print 'trailer'
                            oPDFParseDictionary.PrettyPrint(' ')
                        print
                    elif object.type == PDF_ELEMENT_STARTXREF and selectStartXref:
                        print 'startxref %d' % object.index
                        print
                    elif object.type == PDF_ELEMENT_INDIRECT_OBJECT and selectIndirectObject:
                        if options.search:
                            if object.Contains(options.search):
                                PrintObject(object, options)
                        elif options.object:
                            if object.id == eval(options.object):
                                PrintObject(object, options)
                        elif options.reference:
                            if object.References(options.reference):
                                PrintObject(object, options)
                        elif options.type:
                            if EqualCanonical(object.GetType(), optionsType):
                                PrintObject(object, options)
                        elif options.hash:
                            print 'obj %d %d' % (object.id, object.version)
                            rawContent = FormatOutput(object.content, True)
                            print ' len: %d md5: %s' % (len(rawContent), hashlib.md5(rawContent).hexdigest())
                            print
                        else:
                            PrintObject(object, options)
                    elif object.type == PDF_ELEMENT_MALFORMED:
                        try:
                            fExtract = open(options.extract, 'wb')
                            try:
                                fExtract.write(object.content)
                            except:
                                print 'Error writing file %s' % options.extract
                            fExtract.close()
                        except:
                            print 'Error writing file %s' % options.extract
            else:
                break

        if options.stats:
            print 'Comment: %s' % cntComment
            print 'XREF: %s' % cntXref
            print 'Trailer: %s' % cntTrailer
            print 'StartXref: %s' % cntStartXref
            print 'Indirect object: %s' % cntIndirectObject
            names = dicObjectTypes.keys()
            names.sort()
            for key in names:
                print ' %s %d: %s' % (key, len(dicObjectTypes[key]), ', '.join(map(lambda x: '%d' % x, dicObjectTypes[key])))
        
if __name__ == '__main__':
    Main()
