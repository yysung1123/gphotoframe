from __future__ import division
import os

try:
    import cluttergtk
    import clutter
except:
    from ..utils.nullobject import Null
    cluttergtk = Null()
    cluttergtk.Texture = Null()

from ..utils.iconimage import IconImage
from ..utils.config import GConf
from photoimagegtk import *

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        self.image = self.embed = cluttergtk.Embed()
        #self.embed.realize()

        color = self.conf.get_string('border_color') or '#edeceb'
        self.stage = self.embed.get_stage()
        self.stage.set_color(clutter.color_from_string(color))

        self.photo_image = ActorPhotoImage(self.stage)
        self.actors = [ ActorSourceIcon(self.stage), 
                        ActorGeoIcon(self.stage),
                        ActorFavIcon(self.stage), ]

        self.photo_image.show()
        self.embed.show()

    def _set_photo_image(self, pixbuf):
        self.border = border = self.conf.get_int('border_width', 5)

        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()
        self.embed.set_size_request(self.w + border * 2, self.h + border * 2)
        self.photo_image.change(pixbuf, border, border)

        for actor in self.actors:
            actor.set_icon(self)

    def clear(self):
        pass

    def on_enter_cb(self, w, e):
        for actor in self.actors:
            actor.show(True)

    def on_leave_cb(self, w, e):
        for actor in self.actors:
            actor.hide()

    def check_actor(self, stage, event):
        x, y = int(event.x), int(event.y)
        actor = self.stage.get_actor_at_pos(clutter.PICK_ALL, x, y)
        result = (actor != self.photo_image)
        return result

class ActorPhotoImage(cluttergtk.Texture):

    def __init__(self, stage):
        super(ActorPhotoImage, self).__init__()
        super(ActorPhotoImage, self).hide()

        self.set_reactive(True)
        self.connect('button-press-event', self._on_button_press_cb)
        stage.add(self)

    def change(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(self, pixbuf)
        self.set_position(x, y)

    def _on_button_press_cb(self, actor, event):
        pass

    def _set_texture_from_pixbuf(self, texture, pixbuf):
        bpp = 4 if pixbuf.props.has_alpha else 3

        texture.set_from_rgb_data(
            pixbuf.get_pixels(),
            pixbuf.props.has_alpha,
            pixbuf.props.width,
            pixbuf.props.height,
            pixbuf.props.rowstride,
            bpp, 0)

class ActorIcon(object):

    def calc_position(self, photoimage, icon, position):
        icon_pixbuf = icon.get_pixbuf()
        icon_w, icon_h = icon_pixbuf.get_width(), icon_pixbuf.get_height()
        offset = 10

        if position == 0 or position == 3:
            x = photoimage.border + offset
        else:
            x = photoimage.border + photoimage.w - icon_w - offset 

        if position == 0 or position == 1:
            y = photoimage.border + offset
        else:
            y = photoimage.border + photoimage.h - icon_h - offset 

        return x, y

class ActorSourceIcon(ActorIcon):

    def __init__(self, stage):
        self.texture = ActorPhotoImage(stage)
        self.texture.connect('button-press-event', self._on_button_press_cb)

        self.conf = GConf()
        self._get_ui_data()

    def set_icon(self, photoimage):
        self.photo = photoimage.photo
        if self.photo == None: return

        icon = self._get_icon()
        x, y = self.calc_position(photoimage, icon, self.position)
        if photoimage.w > 80 and photoimage.h > 80: # for small photo image
            icon_pixbuf = icon.get_pixbuf()
            self.texture.change(icon_pixbuf, x, y)
            self.show()

    def show(self, force=False):
        if self.show_always or force:
            self.texture.show()

    def hide(self, force=False):
        if self.show_always is not True:
            self.texture.hide()

    def _get_icon(self):
        return self.photo.get('icon')()

    def _get_ui_data(self):
        self.show_always = self.conf.get_bool('ui/source/show', True)
        self.position = self.conf.get_int('ui/source/position', 1)

    def _on_button_press_cb(self, actor, event):
        self.photo.open()

class ActorGeoIcon(ActorSourceIcon):

    def show(self, force=False):
        if not hasattr(self, 'photo') or self.photo == None: return

        if (self.photo.get('geo') and 
            self.photo['geo']['lat'] != 0 and
            self.photo['geo']['lon'] != 0):
            super(ActorGeoIcon, self).show(force)

    def _get_icon(self):
        return IconImage('gnome-globe')

    def _get_ui_data(self):
        self.show_always = GConf().get_bool('ui/geo/show', False)
        self.position = GConf().get_int('ui/geo/position', 2)

    def _on_button_press_cb(self, actor, event):
        lat = self.photo['geo']['lat']
        lon = self.photo['geo']['lon']
        
        url = "http://maps.google.com/maps?q=%s,%s+%%28%s%%29" % (
            lat, lon, self.photo['title'] or '(no title)')
        os.system("gnome-open '%s'" % url)

class ActorFavIcon(ActorIcon):

    def __init__(self, stage, num=5):
        self.icon = [ ActorFavIconOne(stage, i, self.cb) for i in xrange(num)]
        self.show_always = GConf().get_bool('ui/fav/show', False)
        self.position = GConf().get_int('ui/fav/position', 0)

    def show(self, force=False):
        if (not hasattr(self, 'photo') or 
            self.photo == None or 'fav' not in self.photo): 
            return

        if self.photo.has_key('rate'):
            # for narrow photo image width
            space = self.image.get_pixbuf().get_width() * 1.3
            num = int ((self.photoimage.w - 60) / space) \
                if self.photoimage.w - 60 < 5 * space else 5
        else:
            num = 1

        for i in xrange(num):
            self.icon[i].show()

    def hide(self):
        if self.show_always is True: return
        for icon in self.icon:
            icon.hide()

    def set_icon(self, photoimage):
        self.photo = photoimage.photo
        self.photoimage = photoimage

        if self.photo == None or 'fav' not in self.photo: return

        self.image = IconImage('emblem-favorite')
        self.x, self.y = self.calc_position(photoimage, self.image, self.position)
        self._change_icon()

    def _change_icon(self):
        direction = -1 if 0 < self.position < 3 else 1

        for i, icon in enumerate(self.icon):
            state = self.photo['fav'].fav <= i
            pixbuf = self.image.get_pixbuf(state)
            space = int(pixbuf.get_width() * 1.3)
            icon.change(pixbuf, self.x + i * direction * space, self.y)

            if self.show_always:
                icon.show()

    def cb(self, rate):
        self.photo.fav(rate + 1)
        self._change_icon()

class ActorFavIconOne(ActorPhotoImage):

    def __init__(self, stage, num, cb):
        super(ActorFavIconOne, self).__init__(stage)
        self.number = num
        self.cb = cb

    def _on_button_press_cb(self, actor, event):
        self.cb(self.number)
