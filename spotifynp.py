#!/usr/bin/python2

import dbus
import gobject
import pynotify
import urllib
import gtk

from dbus.mainloop.glib import DBusGMainLoop
from dbus.exceptions import DBusException


class SpotifyNotifier(object):

    def __init__(self):
        """initialise."""
        bus_loop = DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus(mainloop=bus_loop)
        loop = gobject.MainLoop()
        self.notify_id = None
        try:
            self.props_changed_listener()
        except DBusException, e:
            if not ("org.mpris.MediaPlayer2.spotify "
                    "was not provided") in e.get_dbus_message():
                raise
        self.session_bus = self.bus.get_object("org.freedesktop.DBus",
                                 "/org/freedesktop/DBus")
        self.session_bus.connect_to_signal("NameOwnerChanged",
                                        self.handle_name_owner_changed,
                                        arg0="org.mpris.MediaPlayer2.spotify")

        loop.run()

    def props_changed_listener(self):
        """Hook up callback to PropertiesChanged event."""
        self.spotify = self.bus.get_object("org.mpris.MediaPlayer2.spotify",
                                           "/org/mpris/MediaPlayer2")
        self.spotify.connect_to_signal("PropertiesChanged",
                                        self.handle_properties_changed)

    def handle_name_owner_changed(self, name, older_owner, new_owner):
        """Introspect the NameOwnerChanged signal to work out if spotify has started."""
        if name == "org.mpris.MediaPlayer2.spotify":
            if new_owner:
                # spotify has been launched - hook it up.
                self.props_changed_listener()
            else:
                self.spotify = None


    def handle_properties_changed(self, interface, changed_props, invalidated_props):
        """Handle track changes."""
        metadata = changed_props.get("Metadata", {})
        playbackstatus = changed_props.get("PlaybackStatus", {})

        if metadata:
            if pynotify.init("Spotify Notifier Demo"):

                title = metadata.get("xesam:title").encode('UTF-8')
                album = metadata.get("xesam:album").encode('UTF-8')
                artist = metadata.get("xesam:artist")[0].encode('UTF-8')
                url = metadata.get('mpris:artUrl') 
                url = url.replace('thumb','image')
                f = urllib.urlopen(url)
                data = f.read()
                pbl = gtk.gdk.PixbufLoader()
                pbl.write(data)
                pbuf = pbl.get_pixbuf()
                pbl.close()

                alert = pynotify.Notification(title,"By %s from %s" % (artist, album))
                alert.set_icon_from_pixbuf(pbuf)
                alert.set_urgency(pynotify.URGENCY_NORMAL)
                alert.set_timeout(pynotify.EXPIRES_DEFAULT)
                alert.show()
        elif playbackstatus != '{}':
            if playbackstatus == 'Paused':
                if pynotify.init("Spotify Notifier Demo"):
                    alert = pynotify.Notification('Spotify',"Playback Paused")
                    alert.set_urgency(pynotify.URGENCY_NORMAL)
                    alert.set_timeout(pynotify.EXPIRES_DEFAULT)
                    alert.show()
            elif playbackstatus == 'Playing':
                if pynotify.init("Spotify Notifier Demo"):
                    bus = dbus.SessionBus()
                    player = bus.get_object('com.spotify.qt', '/')
                    iface = dbus.Interface(player, 'org.freedesktop.MediaPlayer2')
                    info = iface.GetMetadata()
                    # OUT: [dbus.String(u'xesam:album'), dbus.String(u'xesam:title'), dbus.String(u'xesam:trackNumber'), dbus.String(u'xesam:artist'), dbus.String(u'xesam:discNumber'), dbus.String(u'mpris:trackid'), dbus.String(u'mpris:length'), dbus.String(u'mpris:artUrl'), dbus.String(u'xesam:autoRating'), dbus.String(u'xesam:contentCreated'), dbus.String(u'xesam:url')]
                    title = str(info['xesam:title'])
                    url = str(info['mpris:artUrl'])
                    url = url.replace('thumb','image')
                    f = urllib.urlopen(url)
                    data = f.read()
                    pbl = gtk.gdk.PixbufLoader()
                    pbl.write(data)
                    pbuf = pbl.get_pixbuf()
                    pbl.close()
            
                    alert = pynotify.Notification(title,"By %s from %s" % (info['xesam:artist'][0],info['xesam:album'][0] ))
                    alert.set_icon_from_pixbuf(pbuf)
                    alert.set_urgency(pynotify.URGENCY_NORMAL)
                    alert.set_timeout(pynotify.EXPIRES_DEFAULT)
                    alert.show()




if __name__ == "__main__":
    SpotifyNotifier()
