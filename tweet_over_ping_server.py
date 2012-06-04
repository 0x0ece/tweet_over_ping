#!/usr/bin/python
# requires nfqueue, python-dpkt, python-twitter:
# (deb) apt-get install nfqueue-bindings-python python-dpkt
#       pip/easy_install python-twitter
# run iptables to intercept echo requests
#       iptables -A INPUT -p icmp --icmp-type 8 -j NFQUEUE --queue-num 1
# configure (see later)
# have fun!

# Configuration
# 1. register an application on dev.twitter.com (be sure you have read/write access)
# 2. get an access token for your user
# 3. fill the following variables (you can invent top_key, be sure to put the same in the client)

# put your consumer key/secret:
twitter_config = {
	'consumer_key': '',
	'consumer_secret': '',
}
# list all your users, with Twitter's access token key/secret and a top_key
config = {
	'twitterUsername1': {
		'top_key': 'ToPsecretKey1',
		'access_token_key': '',
		'access_token_secret': '',
	},
	'twitterUsername2': {
		'top_key': 'ToPsecretKey2',
		'access_token_key': '',
		'access_token_secret': '',
	},
}

# main
import struct
import sys
import time
import asyncore
from socket import AF_INET, AF_INET6, inet_ntoa
import nfqueue

# callback
import hmac
import hashlib
from dpkt.ip import IP
from dpkt.icmp import ICMP

# send
import twitter

# verbose
import binascii


# callback function:
# 1. check icmp, echo reply, right format (accept=ignore non-matching patckets)
# 2. verify user+mac (drop if wrong)
# 3. send to twitter (drop if failure)
# 4. accept the packet, the network stack will generate echo reply
def cb(i,payload):
	print ' [*] Packet received'

	# step 1. check TweetOverPing packet (and managed user)
	try:
		# extract the icmp packet
		pkt = IP(payload.get_data())
  		icmp = pkt.data
		if (pkt.p != 1 or icmp.type != 8):
			raise Exception('Echo Request')

		# parse the ToP packet
   		data = icmp.data.data
		msg = data[:-32]
		mac = data[-32:]
		[user, sep, tweet] = msg.partition(':')
		tweet = tweet.rstrip()
		if (len(mac) != 32 or not user or not tweet):
			raise Exception('TweetOverPing')

		# get user config
		try:
			user_config = config[user]
		except KeyError:
			raise Exception('TweetOverPing')

	except Exception as e:
		print " [-] Not a %s packet" % (e,)
		payload.set_verdict(nfqueue.NF_ACCEPT)
		return 0

	# some debug info
	print "     msg length: %d" % (len(msg),)
	print "     user:  %s" % (user,)
	print "     tweet: %s" % (tweet,)
	print "     mac:   %s" % (binascii.hexlify(mac),)

	# steps 2-4
	try:
		# verify mac
		verif = hmac.new(user_config['top_key'], msg, hashlib.sha256).digest()
		if (mac != verif):
			raise Exception('MAC')
		print " [+] mac verification ok"

		# connect to twitter and send the tweet
		api = twitter.Api(
			consumer_key = twitter_config['consumer_key'],
			consumer_secret = twitter_config['consumer_secret'],
			access_token_key = user_config['access_token_key'],
			access_token_secret = user_config['access_token_secret']
		)
		status = api.PostUpdate( "%s"  % (tweet,) )

	except Exception as e:
		print " [-] Error: %s" % (e,)
		payload.set_verdict(nfqueue.NF_DROP)
		return 1
	else:
		payload.set_verdict(nfqueue.NF_ACCEPT)
		print " [+] TweetOverPing accepted"
		sys.stdout.flush()
		return 0

# based on: 
# https://www.wzdftpd.net/redmine/projects/nfqueue-bindings/repository/entry/examples/nfq_asyncore.py
class AsyncNfQueue(asyncore.file_dispatcher):
	"""An asyncore dispatcher of nfqueue events.
	
	"""

	def __init__(self, cb, nqueue=1, family=AF_INET, maxlen=5000, map=None):
		self._q = nfqueue.queue()
		self._q.set_callback(cb)
		self._q.fast_open(nqueue, family)
		self._q.set_queue_maxlen(maxlen)
		self.fd = self._q.get_fd()
		asyncore.file_dispatcher.__init__(self, self.fd, map)
		self._q.set_mode(nfqueue.NFQNL_COPY_PACKET)
		print ' [*] Waiting for packets. To exit press CTRL+C'

	def handle_read(self):
		print ' [*] Processing at most 5 events'		
		self._q.process_pending(5)

	# We don't need to check for the socket to be ready for writing
	def writable(self):
		return False

async_queue = AsyncNfQueue(cb)
asyncore.loop()

