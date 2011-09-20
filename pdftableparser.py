#!/usr/bin/python

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator, HTMLConverter
from pdfminer.layout import LAParams, LTText
from pdfminer.utils import fsplit
from pdfminer.pdfdevice import PDFTextDevice
from pprint import pprint
import sys
import csv

def open_pdf(filename, password=''):
  fp = open(filename, 'rb')
  parser = PDFParser(fp)
  doc = PDFDocument(caching=True)
  parser.set_document(doc)
  doc.set_parser(parser)
  doc.initialize(password)
  return doc

def page_count(doc):
  return doc.getobj(doc.catalog['Pages'].objid)['Count']

class BufferedWriter:
  def __init__(self, *params, **kwds):
    self._writer = csv.writer(*params, **kwds)
    self._buffer = None

  def __del__(self):
    if self._buffer:
      self._writer.writerow(self._buffer)

  def writerow(self, row):
    if self._buffer == None:
      self._buffer = row
    elif row[0] == None:
      while row[0] == None:
        del row[0]
      self._buffer += row
    else:
      while self._buffer[-1] == None:
        del self._buffer[-1]
      self._writer.writerow(self._buffer)
      self._buffer = row

  def writerows(self, rows):
    for row in rows:
      self.writerow(row)

if __name__ == "__main__":
  doc = open_pdf(sys.argv[1])
  
  Point = Route = False
  pages = page_count(doc)
  if pages == 68:
    Point = True
  elif pages == 1143:
    Route = True
  else:
    sys.stderr.write("PDF file not of recognised (NRG) format\n")
    sys.exit(1)
  
  rsrcmgr = PDFResourceManager()
  laparams = LAParams()
  laparams.line_margin = 0    # Forces every line to be absolutely positioned
  laparams.word_margin = 0.2  # Prevents space before narrow characters
  #device = PDFPageAggregator(rsrcmgr, laparams=laparams)
  device = PDFTextDevice(rsrcmgr)
  interpreter = PDFPageInterpreter(rsrcmgr, device)

  writer = BufferedWriter(sys.stdout)

  for (pageno, page) in enumerate(doc.get_pages()):
    interpreter.process_page(page)
    layout = device.get_result()  # returns LTPage

    (text, other) = fsplit(lambda obj: isinstance(obj, LTText), layout)

    header_y = 0
    if Point:
      # Locates bottom of header separator (lowest non-text < 10px height)
      header_y = reduce(lambda x, o: min(x, o.y0),
                        filter(lambda o: o.height < 10, other), float("inf"))
    elif Route:
      header_y = reduce(lambda x, o: max(x, o.y0), other, 0)

    if header_y:
      # Strip off header text
      text = filter(lambda obj: obj.y1 < header_y, text)

    tabs = sorted(set(map(lambda obj: obj.x0, text)))

    text.sort(None, lambda obj: obj.x0)
    text.sort(None, lambda obj: obj.y1, True)

    current = []
    i = iter(tabs)

    for item in text:
      while True:
        try:
          if i.next() != item.x0:
            current.append(None)
          else:
            current.append(item.get_text().strip())
            break
        except StopIteration:
          i = iter(tabs)
          writer.writerow(current)
          current = []

    writer.writerow(current)

