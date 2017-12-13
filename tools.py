import csv
import os
import re
import time

import jieba
import requests

from content import windows_ch, windows_ff
from model import Mblog, Comment, User, MyException, Friend


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if u'\u4e00' <= uchar <= u'\u9fa5':
        return True
    else:
        return False


def prepare_requset(url, method='GET', *arg, **kwargs):
    """生成request请求"""
    req = requests.Request(method=method, url=url)
    headers = kwargs.get("headers")
    if headers is None:
        req.headers.update(windows_ch)
    else:
        req.headers.update(headers)
    req.headers.update({'Server': 'web-v8-010.mweibo.yz.sinanode.com'})
    preped = req.prepare()
    return preped


def get_page(req, session, timeout=5):
    """获取页面返回"""
    error_count = 0
    data = {}
    while error_count < 5:
        try:
            data = session.send(req, timeout=timeout)
            data.raise_for_status()
            break
        except Exception as e:
            print(e)
            time.sleep(3)
            error_count += 1
    if error_count >= 5:
        raise MyException("获取页面失败：", req.url)
    return data


def get_uid_by_name(name):
    req = prepare_requset(url='https://m.weibo.cn/n/' + name)
    data = get_page(req=req, session=requests.session())
    uid = data.request.url.split('/')[-1]
    return uid


def get_container_id_by_uid(uid):
    url = "https://m.weibo.cn/api/container/getIndex?type=uid&value=" + str(uid)
    req = prepare_requset(url=url, headers=windows_ff)
    data = get_page(req=req, session=requests.session())
    try:
        user_info = data.json()
        if user_info.get('ok') != 1:
            print("[获取container_id异常]")
            raise MyException("获取container_id异常")
    except Exception as e:
        print(e)
        raise MyException("获取container_id异常")
    container_id = user_info.get('tabsInfo').get('tabs')[1].get('containerid')
    return container_id


def data_collector(container_id, project_name, pic_flag=False, start_page=1, max_page=255):
    s = requests.session()
    page = start_page
    error_count = 0
    while page <= max_page:
        try:
            req = prepare_requset(
                url='https://m.weibo.cn/api/container/getIndex?containerid=' + str(container_id) + '&page=' + str(page),
                headers=windows_ff)
            data = get_page(req=req, session=s).json()
        except Exception as e:
            print("[some error happened]", e.args[0])
            if error_count > 5:
                print("[page]", page)
                break
            error_count += 1
            time.sleep(3)
            continue
        error_count = 0
        if data.get('ok') != 1:
            print("[没了，一共" + str(page - 1) + "页]")
            break
        cards = data.get('cards')
        for card in cards:
            mblog = card.get('mblog')  # 微博主体
            if mblog is not None:
                try:
                    analysis_weibo(mblog, project_name=project_name, pic_flag=pic_flag, url=card.get('scheme'))
                except Exception as e:
                    print("微博解析异常")
            else:
                print("[不是一条有效微博，卡牌类型为：" + str(card.get('card_type')) + "]")
        page += 1


def get_comments(name, project_name):
    blog_dict = read_from_csv(path='./' + str(name) + '/' + str(name) + '.csv', obj=Mblog)
    for blog in blog_dict.values():
        if blog.comments_count is not None and int(blog.comments_count) > 0:
            comments = get_comment_list(id=blog.id)
            store_comment(comments=comments, project_name=project_name, item_id=blog.id)


def get_friends_list(uid, project_name):
    fans = get_fans_list(uid=uid)
    store_user_list(user_list=fans, project_name=project_name, filename=str(uid) + '_fans')
    followers = get_followers_list(uid=uid)
    store_user_list(user_list=followers, project_name=project_name, filename=str(uid) + '_followers')
    res_list = [user for user in followers if user in fans]
    store_user_list(user_list=res_list, project_name=project_name, filename=str(uid) + '_res_list')
    return fans, followers, res_list


def analysis_weibo(mblog, url, project_name, pic_flag=False, retweeded=False):
    """解析微博主体"""
    mid = mblog.get('id')
    if mblog.get('isLongText'):
        req = prepare_requset(url="https://m.weibo.cn/statuses/extend?id=" + str(id))
        data = get_page(req=req, session=requests.session())
        text = data.json().get('longTextContent')
    else:
        text = mblog.get('text')
    text = re.sub(r'<.*?>', '|', text)
    print(text)
    created_at = mblog.get('created_at')
    source = mblog.get('source')  # 发送设备
    attitudes_count = mblog.get('attitudes_count')  # 点赞数量
    comments_count = mblog.get('comments_count')  # 评论数量
    reposts_count = mblog.get('reposts_count')  # 转发数量
    blog = Mblog(id=mid, created_at=created_at, url=url, text=text, source=source, attitudes_count=attitudes_count,
                 comments_count=comments_count,
                 reposts_count=reposts_count)
    pics = mblog.get('pics')  # 图片微博
    if pic_flag and pics is not None:
        blog.pics_data = analysis_pics(pics=pics, item_name=blog.id, project_name=project_name)
    retweeted_status = mblog.get('retweeted_status')  # 转发微博
    if retweeted_status is not None:
        retweeted_data = analysis_weibo(retweeted_status, url=retweeted_status.get('scheme'), project_name=project_name,
                                        retweeded=True)
        blog.retweeted_data = retweeted_data
    if retweeded:
        store_blog(blog, project_name=project_name, item_name=mid)
    else:
        store_blog(blog, project_name=project_name)
    return blog


def analysis_pics(pics, project_name, item_name=None):
    """解析图片微博"""
    if item_name is None:
        item_name = str(time.time())
    path = "./" + project_name + "/" + item_name
    if not os.path.exists(path):
        os.makedirs(path)
    pic_list = []
    for pic in pics:
        pic_name = pic.get('pid')
        if pic.get('large') is not None:
            url = pic.get('large').get('url')
        else:
            url = pic.get('url')
        pic_list.append(store_img(url=url, path=path, file_name=pic_name))
    return pic_list


def get_comment_list(id, start_page=1, max_page=50):
    """获取评论列表"""
    url = "https://m.weibo.cn/api/comments/show?id=" + str(id)
    page = start_page
    session = requests.session()
    comments_list = []
    while page <= max_page:
        req = prepare_requset(url=url + "&page=" + str(page))
        datas = get_page(req=req, session=session).json()
        if datas.get('ok') != 1:
            break
        else:
            for data in datas.get('data'):
                user = data.get('user')
                text = data.get('text')
                comment = Comment(id=data.get('id'), user_id=user.get('id'), user_name=user.get('screen_name'),
                                  source=data.get('source'), created_at=data.get('created_at'),
                                  text=re.sub(r'<.*?>', '|', text),
                                  reply=data.get('reply_id'))
                comments_list.append(comment)
            page += 1
    return comments_list


def get_followers_list(uid, start_page=1, max_page=255):
    """获取关注列表"""
    url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_" + str(uid) + "&page="
    return get_user_list(url=url, start_page=start_page, max_page=max_page)


def get_fans_list(uid, start_page=1, max_page=255):
    """获取粉丝列表"""
    url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_" + str(uid) + "&since_id="
    return get_user_list(url=url, start_page=start_page, max_page=max_page)


def get_user_list(url, start_page=1, max_page=255):
    """解析用户列表"""
    session = requests.session()
    user_list = []
    page = start_page
    while page <= max_page:
        req = prepare_requset(url=url + str(page))
        datas = get_page(req=req, session=session).json()
        if datas.get('ok') != 1:
            break
        else:
            cards = datas.get('cards')[0].get('card_group')
            for card in cards:
                if card.get('card_type') == 10:
                    user_data = card.get('user')
                    user = User(id=user_data.get('id'), name=user_data.get('screen_name'),
                                description=user_data.get('description'), fans=user_data.get('followers_count'),
                                like=user_data.get('follow_count'))
                    if user not in user_list:
                        user_list.append(user)
        page += 1
    return user_list


def store_img(url, path, session=None, file_name=None):
    """存储图片"""
    if file_name is None:
        x = re.findall(r'^.*/(.*)$', url)
        file_name = x[0]
    else:
        file_name = str(file_name) + '.jpg'
    img_path = path + "/" + file_name
    print("存储图片中~~~~::", img_path)
    if not os.path.exists(img_path):
        count = 5
        req = requests.Request(method="GET", url=url)
        req.headers.update(windows_ch)
        # req.headers.update({'refer': root_url})
        prepared = req.prepare()
        if session is None:
            session = requests.Session()
        while (count > 0):
            try:
                with session.send(prepared, timeout=3) as img:
                    img_date = img.content
                    with open(img_path, 'wb') as f:
                        f.write(img_date)
                        return img_path
            except Exception as e:
                print(e)
                time.sleep(3)
                count -= 1
        return url
    else:
        return img_path


def store_blog(blog, project_name, item_name=None):
    """存储微博内容"""
    if item_name is None:
        item_name = project_name
    path = "./" + project_name + "/" + str(item_name) + ".csv"
    if isinstance(blog, Mblog):
        data = blog.serialize()
        with open(path, "a", encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(data.values())
    else:
        print("[异常类型]")


def store_comment(comments, project_name, item_id):
    """存储评论内容"""
    path = "./" + project_name + "/" + str(item_id) + "_comments.csv"
    with open(path, 'a', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for comment in comments:
            data = comment.serialize()
            writer.writerow(data.values())


def store_friends(friends, project_name, filename):
    """存储好友度"""
    path = "./" + project_name + "/" + str(filename) + ".csv"
    with open(path, 'a', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for friend in friends:
            data = friend.serialize()
            writer.writerow(data.values())


def store_user_list(user_list, project_name, filename):
    path = "./" + project_name + "/" + str(filename) + ".csv"
    with open(path, 'a', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for user in user_list:
            writer.writerow(user.serialize().values())


def read_from_csv(path, obj):
    """从文件中解析数据"""
    dicts = {}
    with open(file=path, encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            o = obj(*row)
            dicts[o.id] = o
    return dicts


def data_analysis(name):
    text_1 = []
    text_2 = []
    blog_list = read_from_csv(path='./' + str(name) + '/' + str(name) + '.csv', obj=Mblog)
    for blog in blog_list:
        text_1.append(blog.text)
        if blog.retweeted_data is not None and len(blog.retweeted_data) > 0:
            retweeted_blog = read_from_csv(path='./' + str(name) + '/' + blog.retweeted_data + '.csv', obj=Mblog)[
                0]
            text_2.append(retweeted_blog.text)
    return text_1, text_2


def key_word_list(name):
    text_1, text_2 = data_analysis(name=name)
    list_1 = jieba.lcut(''.join(text_1))
    list_2 = jieba.lcut(''.join(text_2))
    set_1 = set(list_1)
    dict_1 = {}
    for key in set_1:
        if True or is_chinese(key[0]):
            dict_1[key] = list_1.count(key)
    sort_1 = sorted(dict_1.items(), key=lambda x: x[1], reverse=True)
    set_2 = set(list_2)
    dict_2 = {}
    for key in set_2:
        if True or is_chinese(key[0]):
            dict_2[key] = list_2.count(key)
    sort_2 = sorted(dict_2.items(), key=lambda x: x[1], reverse=True)
    return dict_1, dict_2, sort_1, sort_2


# 数据获取与存储
def collect_weibo_data(uid=None, name=None, pic_flag=False, msg_trigger=None):
    project_name = name
    print_msg = print
    if msg_trigger is not None:
        print_msg = msg_trigger
    # 获取uid
    if uid is None and name is None:
        return None
    elif uid is None and name is not None:
        # project_name = name
        uid = get_uid_by_name(name)
    else:
        uid = str(uid)
    print_msg("[uid]" + uid)
    # 根据uid获取页面id
    container_id = get_container_id_by_uid(uid)
    # 创建工程目录
    if not os.path.exists("./" + project_name):
        os.makedirs("./" + project_name)
    print_msg("[工程目录创建完毕]")
    time.sleep(1)
    # 开始采集微博正文
    print_msg("[开始采集微博正文]")
    data_collector(container_id=container_id, project_name=project_name, pic_flag=pic_flag, start_page=1, max_page=999)
    print_msg("[正文采集完毕]")
    # 开始采集用户关注与被关注列表
    time.sleep(1)
    print_msg("[开始获取用户关注列表完毕]")
    get_friends_list(uid, project_name)
    print_msg("[获取用户关注列表完毕]")
    # 开始采集评论数据
    get_comments(name, project_name)
    print_msg("[获取评论完毕]")


# 好友关系测试
def real_friend(uid=None, name=None):
    # 获取uid
    if uid is None and name is None:
        return None
    elif uid is None and name is not None:
        # project_name = name
        uid = get_uid_by_name(name)
    else:
        uid = str(uid)
    print("uid", uid)
    blog_dict = read_from_csv(path='./' + name + '/' + name + '.csv', obj=Mblog)
    user_list = {}
    for bid in blog_dict.keys():
        path = './' + name + '/' + str(bid) + '_comments.csv'
        try:
            comment_dict = read_from_csv(path=path, obj=Comment)
            for comment in comment_dict.values():
                if len(comment.reply) == 0 and comment.user_id != uid:
                    if user_list.get(comment.user_id) is None:
                        friend = Friend(id=comment.user_id, user=comment.user_name, last_time=comment.created_at,
                                        comment=1)
                        user_list[comment.user_id] = friend
                    else:
                        friend = user_list.get(comment.user_id)
                        friend.commented()
                        friend.start_time = comment.created_at
                    key = comment.text
                    friend.set_key(key)
                elif len(comment.reply) > 0 and comment.user_id == uid:
                    re_comment = comment_dict.get(comment.reply)
                    if re_comment is None:
                        continue
                    if user_list.get(re_comment.user_id) is None:
                        friend = Friend(id=comment.user_id, user=comment.user_name, last_time=comment.created_at,
                                        reply=1)
                        user_list[comment.user_id] = friend
                    else:
                        friend = user_list.get(re_comment.user_id)
                        friend.replyed()
                        friend.start_time = comment.created_at
        except Exception as e:
            print(e.args[0])
            continue
    fans = read_from_csv(path='./' + name + '/' + uid + '_fans.csv', obj=User)
    followers = read_from_csv(path='./' + name + '/' + uid + '_followers.csv', obj=User)
    for friend in user_list.values():
        if fans.get(friend.id) is not None:
            friend.followed = True
        if followers.get(friend.id) is not None:
            friend.liked = True
    store_friends(friends=user_list.values(), project_name=name, filename=name + '_friends')
