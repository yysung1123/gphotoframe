import gtk
import gobject

from photoframe import PhotoFrame
from utils.config import GConf
from utils.wrandom import WeightedRandom
from plugins import *

class PhotoListStore(gtk.ListStore):
    """ListStore for Photo sources.

    0,      1,      2,        3,      4,       5
    source, target, argument, weight, options, object
    """

    def __init__(self):
        super(PhotoListStore, self).__init__(str, str, str, int, str, object)

        self.conf = GConf()
        self._load_gconf()

        self.photoframe = PhotoFrame(self)
        self._timer()

    def append(self, d, iter=None):
        if 'source' not in d: return 

        obj = MAKE_PHOTO_TOKEN[ d['source'] ]( 
            d['target'], d['argument'], d['weight'] )
        list = [ d['source'], d['target'], d['argument'], d['weight'],
                 d['options'], obj ]

        self.insert_before(iter, list)
        obj.prepare()

    def _timer(self):
        self._change_photo()
        self.interval = self.conf.get_int('interval', 30)
        gobject.timeout_add(self.interval * 1000, self._timer)
        return False

    def _change_photo(self):
        target_list = [ x[5] for x in self if x[5].photos ]
        if target_list:
            target = WeightedRandom(target_list)
            target().get_photo(self.photoframe)
        else:
            nophoto = NoPhoto()
            nophoto.show(self.photoframe)
        return True

    def _load_gconf(self):
        for dir in self.conf.all_dirs('sources'):
            data = { 'target' : '', 'argument' : '', 
                     'weight' : 1, 'options' : '' }

            for entry in self.conf.all_entries(dir):
                value = self.conf.get_value(entry)

                if value:
                    path = entry.get_key()
                    key = path[ path.rfind('/') + 1: ]
                    data[key] = value

            if 'source' in data:
                self.append(data)

    def save_gconf(self):
        self.conf.recursive_unset('sources')
        self.conf.recursive_unset('flickr') # for ver. 0.1 

        for i, row in enumerate(self):
            for num, k in enumerate(( 
                    'source', 'target', 'argument', 'weight', 'options')):
                value = row[num]
                if not value: continue
                key = 'sources/%s/%s' % (i, k)

                self.conf.set_value(key, value)
