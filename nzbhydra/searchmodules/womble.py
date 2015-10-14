import logging
import re
import arrow
from furl import furl
import xml.etree.ElementTree as ET
from nzbhydra.config import GenerateQueriesSelection
from nzbhydra.exceptions import ProviderResultParsingException
from nzbhydra.nzb_search_result import NzbSearchResult

from nzbhydra.search_module import SearchModule, ProviderProcessingResult

logger = logging.getLogger('root')


# Probably only as RSS supply, not for searching. Will need to do a (config) setting defining that. When searches without specifier are done we can include indexers like that
class Womble(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, provider):
        super(Womble, self).__init__(provider)
        self.module = "womble"
        
        self.settings.generate_queries = GenerateQueriesSelection.never #Doesn't matter because supports_queries is False
        self.needs_queries = False
        self.category_search = True
        self.supports_queries = False  # Only as support for general tv search

    def build_base_url(self):
        url = furl(self.provider.settings.get("query_url")).add({"fr": "false"})
        return url

    def get_search_urls(self, args):
        logger.error("This provider does not support queries")
        return []

    def get_showsearch_urls(self, args):
        urls = []
        if args["query"] or args["imdbid"] or args["rid"] or args["tvdbid"] or args["season"] or args["episode"]:
            logger.error("This provider does not support specific searches")
            return []
        if args["category"]:
            if args["category"] == "TV SD" or args["category"] == "TV":
                urls.append(self.build_base_url().add({"sec": "tv-dvd"}).tostr())
                urls.append(self.build_base_url().add({"sec": "tv-sd"}).tostr())
            if args["category"] == "TV HD" or args["category"] == "TV":
                urls.append(self.build_base_url().add({"sec": "tv-x264"}).tostr())
                urls.append(self.build_base_url().add({"sec": "tv-hd"}).tostr())
        else:
            urls.append(self.build_base_url().tostr())
        return urls

    def get_moviesearch_urls(self, args):
        logger.error("This provider does not support movie search")
        return []

    def process_query_result(self, xml, query) -> ProviderProcessingResult:
        entries = []
        try:
            tree = ET.fromstring(xml)
        except Exception:
            logger.exception("Error parsing XML: %s..." % xml[:500])
            logger.debug(xml)
            raise ProviderResultParsingException("Error parsing XML", self)
        for elem in tree.iter('item'):
            title = elem.find("title")
            url = elem.find("enclosure")
            pubdate = elem.find("pubDate")
            if title is None or url is None or pubdate is None:
                continue
            
            entry = NzbSearchResult()
            entry.title = title.text
            entry.link = url.attrib["url"]
            
            p = re.compile("(.*)\(Size:(\d*)")
            m = p.search(elem.find("description").text)
            if m:
                entry.description = m.group(1)
                entry.size = int(m.group(2)) * 1024 * 1024 #megabyte to byte
            if elem.find("category").text.lower() == "tv-dvdrip" or elem.find("category").text.lower() == "tv-sd":
                entry.category = "TV SD"
            elif elem.find("category").text.lower() == "tv-x264" or elem.find("category").text.lower == "tv-hd":
                entry.category = "TV HD"
            else:
                entry.category = "N/A" #undefined
                
            
            entry.guid = elem.find("guid").text[30:] #39a/The.Almighty.Johnsons.S03E06.720p.BluRay.x264-YELLOWBiRD.nzb is the GUID, only the 39a doesn't work
            
            pubdate = arrow.get(pubdate.text, 'M/D/YYYY h:mm:ss A')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
             
            entries.append(entry)
            
        return ProviderProcessingResult(entries=entries, queries=[])
    
    def get_nzb_link(self, guid, title):
        f = furl(self.base_url)
        f.path.add("nzb")
        f.path.add(guid)
        return f.tostr()


def get_instance(provider):
    return Womble(provider)
