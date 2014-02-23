import requests
import json
import simplejson
import time


class SongzaSong():
    def __init__(self, account, song, extended = None):
        self.account = account
        for item in song:
            setattr(self, item, song[item])
        if extended:
            for item in extended:
                if item == "song": continue
                setattr(self, item, extended[item])

    def __repr__(self):
        return '<SongzaSong %s / %s / %s >' % (self.artist['name'], self.album, self.title)


class SongzaStation():
    def __init__(self, account, station):
        self.account = account
        #print json.dumps(station, indent = 4)
        for item in station:
            setattr(self, item, station[item])

    def enumerate(self):
        songs = []
        while len(songs) < self.song_count:
            song = self.account.getv1('station/%d/next' % self.id)
            if song.text == "rate limit exceeded":
                print 'hit rate limit'
                time.sleep(1)
            else:
                song_o = SongzaSong(self.account, song.json()['song'], song.json())
                if song_o.id not in songs:
                    songs.append(song_o.id)
                    print 'got new song %s' % song_o
                    yield song_o
                else:
                    print 'got duplicate song %s' % song_o

    def next(self):
        song = self.account.get('station/%d/next' % self.id)
        return SongzaSong(self.account, song['song'], song)

    def __repr__(self):
        return '<SongzaStation %s >' % (self.name)


class SongzaAccount():
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def login(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': "pysongza (https://github.com/adamjacobmuller/pysongza)"})
        result = self.session.post('https://songza.com/api/1/login/pw', {'username': self.username, 'password': self.password})
        items = result.json()
        for item in items:
            setattr(self, item, items[item])

    def get(self, url, *args, **kwargs):
        #print 'url is %s' % url
        return self.session.get(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.session.post(url, *args, **kwargs)

    def getjv1(self, url, *args, **kwargs):
        reqobj = self.get('http://songza.com/api/1/%s' % url, *args, **kwargs)
        try:
            return reqobj.json()
        except ValueError:
            print reqobj
            print reqobj.text
            raise

    def postjv1(self, url, *args, **kwargs):
        reqobj = self.post('http://songza.com/api/1/%s' % url, *args, **kwargs)
        try:
            return reqobj.json()
        except ValueError:
            print reqobj
            print reqobj.text
            raise

    def getv1(self, url, *args, **kwargs):
        return self.get('http://songza.com/api/1/%s' % url, *args, **kwargs)

    def postv1(self, url, *args, **kwargs):
        return self.post('http://songza.com/api/1/%s' % url, *args, **kwargs)

    def votes(self, vote = None):
        limit = 100
        offset = 0
        if vote is not None:
            vote_r = '&vote=%s' % vote
        else:
            vote_r = ''
        while True:
            x = self.getjv1('user/%d/song-votes?limit=%d&offset=%d%s' % (self.id, limit, offset, vote_r))
            for vote in x:
                yield (
                    vote['vote'],
                    SongzaSong(self, vote['song']),
                    SongzaStation(self, vote['station'])
                )
            if len(x) < limit:
                break
            else:
                offset += limit


if __name__ == "__main__":
    settings = json.load(open("pysongza.json", "r"))
    songza = SongzaAccount(settings['username'], settings['password'])
    songza.login()
    votes = songza.votes()
    for vote in votes:
        print("%4s %s on %s" % vote)
        #for song in vote[2].enumerate():
        #    print song.listen_url
