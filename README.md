TweetOverPing
=============

[TweetOverPing](http://ping.theneeds.com/)
(ToP) is an app to tweet sustainably with just a ping, 
towards an eco-web. Light, simple, awesome!


Tweetting (over ping)
=====================

## Requirements

ToP client requires `openssl` and `hping3`.

These are available on most Linux distributions and other operating systems.

### Debian, Ubuntu & co.

    apt-get install hping3
    
### RedHat, CentOS, Fedora & co.

    yum install hping3

### MacOSX (brew)

    brew install hping


For the impatients
------------------

1. Register at [ping.theneeds.com](http://ping.theneeds.com), you'll get a _secret key_. Beware! Who has this key can tweet on your behalf.
1. Edit `tweet_over_ping.sh` and insert your Twitter username and the secret key (NOT your Twitter password!):

    ```
    #!/bin/sh
    
    TWITTER_USERNAME=myTwitterUser
    TOP_KEY=keyGotAtRegistration
    
    ...
    ```
    
1. Run:

    ```
    sh tweet_over_ping.sh "Hello world!"
    ```
    
1. Check your [Twitter timeline](https://twitter.com/) and enjoy!


How it works
------------

ToP client does three simple things for you. 
If you want to have more fun, you can try the following commands to understand what ToP client does behind the scene.

First, format your tweet. The syntax is `username:tweet`:
```
echo -n "myTwitterUser:Hello world!" > tweet.txt
```

Next, put a signature on the tweet to avoid tampering. ToP uses hmac with sha256:
```
openssl dgst -hmac keyGotAtRegistration -sha256 -binary < tweet.txt >> tweet.txt
```

Finally, send a ping to [ping.theneeds.com](http://ping.theneeds.com), with payload `tweet.txt`. Note that `hping3` requires the data size (`-d` option).
```
SIZE=`wc -c tweet.txt | cut -f 1 -d ' '`
hping3 -1 -c 1 -E tweet.txt -d $SIZE localhost
```

Setting up your own ToP server
==============================

Coming soon


