#!/usr/bin/env python

import sys
import time
from btce import Actions, Rules, loop_time, pair_list
from debug import debug, debug_messages


try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    from gi.repository import GObject as gobject
except:
    print "GTK3.0 not found, please verify your system."
    pass
    try:
        from gtk import gtk as Gtk
        import gobject
    except:
        print "GTK not found, please verify your system."
        sys.exit(1)


class UI:

    def __init__(self):
        self.builder = Gtk.Builder()  # create an instance of the gtk.Builder
        self.builder.add_from_file("btce.glade")  # add the xml file to the Builder
        self.window = self.builder.get_object("MainWindow")  # This gets the 'window' object
        self.dialog_about = self.builder.get_object("aboutdialog")
        self.dialog_settings = self.builder.get_object("dialog_settings")
        self.dialog_welcome = self.builder.get_object("dialog_welcome")
        self.dialog_process = self.builder.get_object("dialog_process")
        self.text= self.builder.get_object("text")
        self.entry_key = self.builder.get_object("entry_key")
        self.entry_secret = self.builder.get_object("entry_secret")
        self.entry_pairs = self.builder.get_object("entry_pairs")
        self.button_debug = self.builder.get_object("button_debug")
        self.spin_amount = self.builder.get_object("spinbutton_amount")
        self.spin_minimum = self.builder.get_object("spinbutton_minimum")
        self.spin_fee = self.builder.get_object("spinbutton_fee")
        self.spin_loop = self.builder.get_object("spinbutton_loop")
        self.spin_timeout = self.builder.get_object("spinbutton_order_timeout")
        # adjustment_amount = Gtk.adjustment_amount(0.00, 5, 100, 0.01, 1, 10)
        # adjustment_minimum = Gtk.adjustment_minimum(0.01, 0.01, 100, 0.01, 0.1, 10)
        # adjustment_fee = Gtk.adjustment_fee(0.20, 0, 100, 0.01, 0.1, 10)
        # adjustment_loop = Gtk.adjustment_loop(30, 10, 100, 1, 10, 100)
        # adjustment_timeout = Gtk.timeout(30, 10, 100, 1, 10, 100)
        self.builder.connect_signals(self)
        self.window.show()
        self.welcome()

    def welcome(self):
        print "welcome dialog open"
        self.dialog_welcome.run()

    def on_dialog_welcome_close(self):
        print "welcome dialog close"
        self.dialog_welcome.hide()

    def on_button_stop_clicked(self, *args):
        print "stop button pressed"
        Gtk.main_quit()

    def on_MainWindow_destroy(self, object, data=None):
        print "killed main window"
        Gtk.main_quit()

    # About event handler
    def on_button_about_clicked(self, *args):
        print "help about selected"
        self.dialog_about.run()
        self.dialog_about.hide()

    def settings(self, *args):
        print "settings dialog run"
        self.dialog_settings.run()

    def on_button_reset_clicked(self, *args):
        print "reset button clicked"
        self.entry_key.set_text("")
        self.entry_secret.set_text("")
        self.entry_pairs.set_text("")
        self.button_debug.set_state(False)
        self.spin_amount.set_text("10")
        self.spin_minimum.set_text("0,01")
        self.spin_fee.set_text("0,2")
        self.spin_loop.set_text("30")
        self.spin_timeout.set_text("30")

    def on_button_start_clicked(self, *args):
        print "start button clicked"
        self.dialog_welcome.hide()
        self.settings()

    def main_loop(self):
        while True:
            for msg in debug_messages:
                self.text.get_buffer().set_text(msg)
            for pair in pair_list:
                debug("main process: %s" % pair)
                if Rules().rule_buy_1(pair) and Rules().rule_buy_2(pair):
                    return Actions().buy(pair)
                if Rules().rule_sell_1(pair) and Rules().rule_sell_2(pair):
                    return Actions().sell(pair)
            time.sleep(loop_time)

    def on_button_run_clicked(self, *args):
        print "run button clicked"
        debug("Starting")
        if self.dialog_settings:
            self.dialog_settings.hide()
        self.main_loop()

    def on_button_debug_toggled(self, *args):
        print "debug toggled"
        self.button_debug.set_state(is_active=True)

    def on_button_settings_clicked(self, *args):
        print "button setting clicked"
        self.settings()

    def on_button_save_clicked(self, *args):
        f = open('config.py', 'w')
        conf_key = self.entry_key.get_text()
        conf_secret = self.entry_secret.get_text()
        conf_pairs = self.entry_pairs.get_text()
        conf_debug = self.button_debug.get_active()
        conf_amount = self.spin_amount.get_text()
        conf_minimum = self.spin_minimum.get_text()
        conf_fee = self.spin_fee.get_text()
        conf_loop = self.spin_loop.get_text()
        conf_timeout = self.spin_timeout.get_text()
        config = """
PAIRS = [%s]
KEY = '%s'
SECRET = '%s'
AMOUNT = %g
DEBUG = %s
MINIMUM = %g
FEE = %g
LOOP = %g
ORDER_TIMEOUT = %g
        """ % (
            conf_pairs,
            conf_key,
            conf_secret,
            float(conf_amount),
            conf_debug,
            float(conf_minimum),
            float(conf_fee),
            float(conf_loop),
            float(conf_timeout)
        )
        f.write(config)
        f.close()


if __name__ == "__main__":
    main = UI()  # create an instance of our class
    Gtk.main()  # run the thing
