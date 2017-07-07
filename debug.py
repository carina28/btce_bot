from myconfig import DEBUG
import time

if DEBUG:
    debug_status = 1

debug_messages = []


def debug(message, *date):
    if not date:
        date = time.ctime()
    msg = '[DEBUG]: %s: %s' % (date, message)
    if debug_status == 1:
        print msg
        debug_messages.append(msg)
    elif debug_status == 0:
        f = open('debug.log')
        f.write(msg)
        f.close()
