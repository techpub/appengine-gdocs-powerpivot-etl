#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2, urllib, jinja2, os, os.path
from google.appengine.api import urlfetch
from collections import OrderedDict, defaultdict
import logging; logging.getLogger().setLevel(logging.DEBUG)

japp = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))
japp.filters['header'] = lambda s, lowercase=True: (s.lower().replace(" ", "") if lowercase else s.replace(" ", ""))
japp.filters['annotate'] = lambda k, annotations: " ".join('%s="%s"' % (h, d[k]) for h, d in annotations.items() if k in d)
    
def parse_txt(lines):
    header = lines[0].split("\t")
    return (OrderedDict([(k, v) for k, v in zip(header, line.split("\t"))]) for line in lines[1:])
    
def unpivot(rows, colix):
    for row in rows:
        items = row.items()
        for col, val in items[colix:]:
            yield OrderedDict(items[:colix], col=col, value=val)
    
class MainHandler(webapp2.RequestHandler):
    def get(self):
        data = {    'output' : 'txt',
                    'gid' : self.request.GET.get('gid', '0'),
                    'key' : self.request.GET['key'],
        }
        resp = urlfetch.fetch("https://docs.google.com/spreadsheet/pub?" + urllib.urlencode(data))
        rows = list(parse_txt(resp.content.decode("utf-8").splitlines()))
        
        if 'ignore_rows' in self.request.GET: rows = rows[int(self.request.GET['ignore_rows']):]
        if 'unpivot' in self.request.GET: rows = unpivot(rows, int(self.request.GET['unpivot']))
            
        annotations = defaultdict(dict)
        for key, value in self.request.GET.items():
            if key.startswith("type_"): 
                annotations['m:type'][key.replace("type_", "")] = value
        
        template = japp.get_template("feed.xml")
        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(template.render({
            "rows" : rows, 
            "annotations" : annotations, 
            "lowercase" : self.request.GET.get('lowercase', '1') != '0'
        }))

app = webapp2.WSGIApplication([('/gdetl', MainHandler)], debug=True)