import random

class PingPlugin(object):
    def pong(self, cardinal, user, channel, msg):
        options = ["stares {} down.",
                   "waggles its tail once.",
                   "meow",
                   "miaow"]
        action = random.choice(options).format(user.group(1))
        print "(%s) *** %s %s." % (channel, cardinal.nickname, action)
        cardinal.describe(channel, action)

    pong.regex = r'(?i)^ping[.?!]?$'
    pong.commands = ['ping']
    pong.help = "Responds to a ping message.'"

def setup():
    return PingPlugin()
