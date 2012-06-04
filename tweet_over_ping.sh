#!/bin/sh

# TweetOverPing client
#
# Before usage, you need to register at http://ping.theneeds.com and get your secret key
#
# Enter your Twitter username and the secret key (NOT your Twitter password!)
TWITTER_USERNAME=
TOP_KEY=

# Check if you like these options too
APPEND=" via @TweetOverPing"
HPING=hping3
OPENSSL=openssl
HOST=localhost
TMP_FILE=tweet_over_ping.txt

# check input
if [ -z $TOP_KEY ]; then
	echo "TweetOverPing client - Error: key not set" 1>&2
	echo "You need to register at http://ping.theneeds.com to get your secret key" 1>&2
	exit 1
fi
if [ "$(id -u)" != "0" ]; then
	echo "TweetOverPing client - Error: this script must be run as root (because of hping)" 1>&2
	exit 1
fi
if [ -z "$*" ]; then
	echo "TweetOverPing client (run as root)"
	echo "usage: tweet_over_ping.sh Your tweet here"
	echo "   or: tweet_over_ping.sh 'Quote #special characters!'"
	exit 1
fi
if [ -f $TMP_FILE ]; then
	echo "TweetOverPing client - Error: temp file already exists ($TMP_FILE)" 1>&2
	echo "Please manually remove it, or change the \$TMP_FILE variable within the script" 1>&2
	exit 1
fi

# 1. prepare the tweet "username:tweet"
echo $TWITTER_USERNAME:${*}$APPEND > $TMP_FILE

# 2. add signature (hmac sha256)
$OPENSSL dgst -hmac $TOP_KEY -sha256 -binary < $TMP_FILE >> $TMP_FILE

# 3. send the ping
SIZE=$(echo `wc -c $TMP_FILE` | cut -d' ' -f1)        # echo to trim, e.g. on mac
OUT=`$HPING -1 -c 1 -E $TMP_FILE -d $SIZE $HOST 2>&1`

# parse hping output
if [ $? -eq 0 ]; then
	TIME=`echo -n $OUT | grep round-trip | cut -d'/' -f4`
	echo "Tweet sent. Time: $TIME ms"
else
	echo "Something goes wrong. Check your username/key and try again."
	echo "If the problem persists try re-registering at http://ping.theneeds.com"
fi

# remove TMP_FILE
rm $TMP_FILE

