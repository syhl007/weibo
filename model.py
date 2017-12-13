class MyException(Exception):
    pass

class Item:
    def __init__(self, type, url):
        self.type = type
        self.url = url


class Mblog:
    def __init__(self, id, created_at, source, url, reposts_count, attitudes_count, comments_count, text, pics=None,
                 retweeted=None):
        self.id = id
        self.url = url
        self.created_at = created_at
        self.text = text
        self.source = source
        self.attitudes_count = attitudes_count
        self.comments_count = comments_count
        self.reposts_count = reposts_count
        self.pics_data = pics
        self.retweeted_data = retweeted

    def serialize(self):
        dicts = {'id': self.id,
                 'created_at': self.created_at,
                 'source': self.source,
                 'url': self.url,
                 'reposts_count': self.reposts_count,
                 'attitudes_count': self.attitudes_count,
                 'comments_count': self.comments_count,
                 'text': self.text,
                 'pics': self.pics_data,
                 'retweeted': None}
        if self.retweeted_data is not None:
            dicts.update({'retweeted': self.retweeted_data.id})
        return dicts

    def __eq__(self, other):
        return self.id == other.id


class Comment:
    def __init__(self, id, user_id, user_name, source, created_at, text, reply):
        self.id = id
        self.user_id = user_id
        self.user_name = user_name
        self.source = source
        self.created_at = created_at
        self.text = text
        self.reply = reply

    def serialize(self):
        dicts = {'id': self.id,
                 'user_id': self.user_id,
                 'user_name': self.user_name,
                 'source': self.source,
                 'created_at': self.created_at,
                 'text': self.text,
                 'reply': self.reply}
        return dicts

    def __eq__(self, other):
        return self.id == other.id


class User:
    def __init__(self, id, name, description, fans, like):
        self.id = id
        self.name = name
        self.description = description
        self.fans = fans
        self.like = like

    def serialize(self):
        dicts = {'id': self.id,
                 'user_id': self.name,
                 'user_name': self.description,
                 'source': self.fans,
                 'like': self.like}
        return dicts

    def __eq__(self, other):
        return self.id == other.id


class Friend:
    def __init__(self, id, user, liked=False, followed=False, last_time=None, start_time=None, mention=0, comment=0,
                 reply=0, key=None):
        self.id = id
        self.user = user
        self.liked = liked
        self.followed = followed
        self.last_time = last_time
        self.start_time = start_time
        self.mention = mention
        self.comment = comment
        self.reply = reply
        self.key = key

    def mentioned(self):
        self.mention += 1

    def commented(self):
        self.comment += 1

    def replyed(self):
        self.reply += 1

    def set_key(self, key_list):
        if self.key is None:
            self.key = []
        self.key.append(key_list)

    def serialize(self):
        dicts = {'id': self.id,
                 'user': self.user,
                 'liked': self.liked,
                 'followed': self.followed,
                 'last_time': self.last_time,
                 'start_time': self.start_time,
                 'mention': self.mention,
                 'comment': self.comment,
                 'reply': self.reply,
                 'key':self.key}
        return dicts

    def __eq__(self, other):
        return self.id == other.id