import os
import sys
import time

import gtk
import gobject
import gtk.glade

from gtts import gTTS

import bluetooth

#import socket
from bluetooth import *
from PyOBEX.client import BrowserClient
from PyOBEX.client import Client

GLADEFILE="bluezchat.glade"

# *****************

def alert(text, buttons=gtk.BUTTONS_NONE, type=gtk.MESSAGE_INFO):
    md = gtk.MessageDialog(buttons=buttons, type=type)
    md.label.set_text(text)
    md.run()
    md.destroy()

class BluezChatGui:
    def __init__(self):
        self.main_window_xml = gtk.glade.XML(GLADEFILE, "bluezchat_window")

        # connect our signal handlers
        dic = { "on_quit_button_clicked" : self.quit_button_clicked,
                "on_send_button_clicked" : self.send_button_clicked,
                "on_chat_button_clicked" : self.chat_button_clicked,
                "on_scan_button_clicked" : self.scan_button_clicked,
                "on_FT_button_clicked" :self.FT_button_clicked,
		"on_send_text_button_clicked":self.send_text_button_clicked,
                "on_devices_tv_cursor_changed" : self.devices_tv_cursor_changed
                }

        self.main_window_xml.signal_autoconnect(dic)

        # prepare the floor listbox
        self.devices_tv = self.main_window_xml.get_widget("devices_tv")
        self.discovered = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_STRING)
        self.devices_tv.set_model(self.discovered)
        renderer = gtk.CellRendererText()
        column1=gtk.TreeViewColumn("addr", renderer, text=0)
        column2=gtk.TreeViewColumn("name", renderer, text=1)
        self.devices_tv.append_column(column1)
        self.devices_tv.append_column(column2)

        self.quit_button = self.main_window_xml.get_widget("quit_button")
        self.scan_button = self.main_window_xml.get_widget("scan_button")
        self.chat_button = self.main_window_xml.get_widget("chat_button")
        self.send_button = self.main_window_xml.get_widget("send_button")
        self.FT_button =self.main_window_xml.get_widget("FT_button")
        self.main_text = self.main_window_xml.get_widget("main_text")
	self.send_text_button=self.main_window_xml.get_widget("send_text_button")
        self.text_buffer = self.main_text.get_buffer()

        self.input_tb = self.main_window_xml.get_widget("input_tb")

        self.listed_devs = []

        self.chat_button.set_sensitive(False)

        self.peers = {}
        self.sources = {}
        self.addresses = {}

        # the listening sockets
        self.server_sock = None

# --- gui signal handlers

    def quit_button_clicked(self, widget):
        gtk.main_quit()

    def send_text_button_clicked(self,widget):
	(model,iter)=self.devices_tv.get_selection().get_selected()
        address=model.get_value(iter,0)
        text = self.input_tb.get_text()
	f = open("demofile.txt", "w")
	f.write(text)
	ftet=("bluetooth-sendto --device="+address+" /home/xamy/Downloads/ff/Project/demofile.txt")
	os.system(ftet)



    def scan_button_clicked(self, widget):
	self.text_buffer.insert(self.text_buffer.get_end_iter(),"\nLooking for devices")
        self.quit_button.set_sensitive(False)
        self.scan_button.set_sensitive(False)
#        self.chat_button.set_sensitive(False)

        self.discovered.clear()
        for addr, name in bluetooth.discover_devices (lookup_names = True):
            self.discovered.append ((addr, name))

        self.quit_button.set_sensitive(True)
        self.scan_button.set_sensitive(True)
#        self.chat_button.set_sensitive(True)

    def send_button_clicked(self, widget):
	(model,iter)=self.devices_tv.get_selection().get_selected()
        address=model.get_value(iter,0)
        text = self.input_tb.get_text()
        if len(text) == 0: return

        #for addr, sock in list(self.peers.items()):
            #sock.send(text)

        #self.input_tb.set_text("")
        #self.add_text("\nme - %s" % text)
	language = 'en'

	myobj = gTTS(text, lang=language, slow=False)
	myobj.save("betatest.mp3")
	fat=("bluetooth-sendto --device="+address+" /home/xamy/Downloads/ff/Project/betatest.mp3")
	os.system(fat)
	os.remove("betatest.mp3")
    self.text_buffer.insert(self.text_buffer.get_end_iter(),"\nSend audio to device.")


    def chat_button_clicked(self, widget):
        (model, iter) = self.devices_tv.get_selection().get_selected()
        addr = model.get_value(iter, 0)
        self.add_text("\nConnecting to device ")
        bttt=("bt-device -c "+addr)
        fd="hcitool scan"
        os.system(fd)
    	self.text_buffer.insert(self.text_buffer.get_end_iter(),"\nWait\n('_-) (-_') ('_-) (-_') ('_-) (-_')\n")
        os.system(bttt)
	self.add_text("Connected ;-)")
        #if iter is not None:
        #    addr = model.get_value(iter, 0)
        #    if addr not in self.peers:
        #        self.add_text("\nconnecting to %s" % addr)
        #        self.connect(addr)
        #    else:
        #        self.add_text("\nAlready connected to %s!" % addr)

    def FT_button_clicked(self, widget):
        (model,iter)=self.devices_tv.get_selection().get_selected()
        address=model.get_value(iter,0)
	fft=("bluetooth-sendto --device="+address)
	os.system(fft)
	self.text_buffer.insert(self.text_buffer.get_end_iter(),"\nSent file")
        # send file
        print 'sending file to %s...'%address
        #self.client=self.BrowserClient(address,8888)
        #self.client.connect()
        #self.client.put('test.txt', 'HelloWorld!')
        #self.client.disconnect()

    def devices_tv_cursor_changed(self, widget):
        (model, iter) = self.devices_tv.get_selection().get_selected()
        if iter is not None:
            self.chat_button.set_sensitive(True)
        else:
            self.chat_button.set_sensitive(False)

# --- network events

    def incoming_connection(self, source, condition):
        sock, info = self.server_sock.accept()
        address = info

        self.add_text("\naccepted connection from %s" % str(address))

        # add new connection to list of peers
        self.peers[address] = sock
        self.addresses[sock] = address

        source = gobject.io_add_watch (sock, gobject.IO_IN, self.data_ready)
        self.sources[address] = source
        return True

    def data_ready(self, sock, condition):
        address = self.addresses[sock]
        data = sock.recv(1024)

        if len(data) == 0:
            self.add_text("\nlost connection with %s" % address)
            gobject.source_remove(self.sources[address])
            del self.sources[address]
            del self.peers[address]
            del self.addresses[sock]
            sock.close()
        else:
            self.add_text("\n%s - %s" % (address, str(data)))
        return True

# --- other stuff

    def cleanup(self):
        self.hci_sock.close()

    def connect(self, addr):
        sock = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
        #try:
        sock.connect((addr, 0x1001))
        #except bluez.error as e:
            #self.add_text("\n%s" % str(e))
            #sock.close()
            #return

        self.peers[addr] = sock
        source = gobject.io_add_watch (sock, gobject.IO_IN, self.data_ready)
        self.sources[addr] = source
        self.addresses[sock] = addr

    def add_text(self, text):
        self.text_buffer.insert(self.text_buffer.get_end_iter(), text)

    def start_server(self):
        self.server_sock = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
        self.server_sock.bind(("",0x0003))
        self.server_sock.listen(1)

        gobject.io_add_watch(self.server_sock,
                gobject.IO_IN, self.incoming_connection)

    def run(self):
        self.text_buffer.insert(self.text_buffer.get_end_iter(), "Welcome")
        self.start_server()
        gtk.main()

if __name__ == "__main__":
    gui = BluezChatGui()
gui.run()
