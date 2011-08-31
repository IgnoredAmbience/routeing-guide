#!/usr/bin/python

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator, HTMLConverter
from pdfminer.layout import LAParams, LTText
from pdfminer.utils import fsplit
from pprint import pprint
import sys

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

if __name__ == "__main__":
  #doc = open_pdf('/home/thomas/Rail/RouteingGuide-B-PointLookup.pdf')
  doc = open_pdf('/home/thomas/Rail/RouteingGuide-C-RouteLookup.pdf')
  
  Point = Route = False
  pages = page_count(doc)
  if pages < 100:
    Point = True
  elif pages > 1000:
    Route = True
  
  rsrcmgr = PDFResourceManager()
  laparams = LAParams()
  laparams.line_margin = 0    # Forces every line to be absolutely positioned
  laparams.word_margin = 0.2  # Prevents space before narrow characters
  device = PDFPageAggregator(rsrcmgr, laparams=laparams)
  interpreter = PDFPageInterpreter(rsrcmgr, device)


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
      text = filter(lambda obj: obj.y1 < header_y, text)

    html = HTMLConverter(rsrcmgr, sys.stdout)
    layout._objs = text   # hack
    html.receive_layout(layout)

    break
