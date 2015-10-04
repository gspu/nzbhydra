from freezegun import freeze_time

from furl import furl

from nzbhydra.database import Provider
from nzbhydra.searchmodules.nzbclub import NzbClub
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra.tests.providerTest import ProviderTestcase


class MyTestCase(ProviderTestcase):
    def setUp(self):
        set_and_drop()
        self.nzbclub = Provider(module="nzbclub", name="nzbclub", settings={"query_url": "http://127.0.0.1:5001/nzbclub", "base_url": "http://127.0.0.1:5001/nzbclub", "search_ids": []})
        self.nzbclub.save()

    def testUrlGeneration(self):
        w = NzbClub(self.nzbclub)
        self.args.update({"query": "a showtitle", "season": 1, "episode": 2})
        urls = w.get_showsearch_urls(args=self.args)
        self.assertEqual(1, len(urls))
        print(urls[0])
        self.assertEqual('a showtitle s01e02 or a showtitle 1x02', furl(urls[0]).args["q"])

        self.args.update({"query": "a showtitle", "season": 1, "episode": None})
        urls = w.get_showsearch_urls(args=self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle s01 or a showtitle "season 1"', furl(urls[0]).args["q"])

    @freeze_time("2015-09-24 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbClub(self.nzbclub)
        with open("mock/nzbclub--q-avengers.xml", encoding="latin-1") as f:
            entries = w.process_query_result(f.read(), "aquery")["entries"]
            self.assertEqual('Avengers.Age.of.Ultron.2015.720p.BluRay.x264.YIFY', entries[0].title)
            self.assertEqual("http://www.nzbclub.com/nzb_get/60269450/Avengers Age of Ultron 720p BrRip x264 YIFY Avengers Age of Ultron 2015 720p BluRay x264 YIFY.nzb", entries[0].link)
            self.assertEqual(1075514926, entries[0].size)
            self.assertEqual("60269450", entries[0].guid)
            self.assertEqual(1443019463, entries[0].epoch)
            self.assertEqual("2015-09-23T09:44:23-05:00", entries[0].pubdate_utc)
            self.assertEqual(0, entries[0].age_days)

    
    def testGetNzbLink(self):
        n = NzbClub(self.nzbclub)
        link = n.get_nzb_link("guid", "title")
        self.assertEqual("http://127.0.0.1:5001/nzbclub/nzb_get/guid/title.nzb", link)
    