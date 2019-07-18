# FacebookPy

[![MIT license](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://github.com/socialbotspy/FacebookPy/blob/master/LICENSE)
[![built with Selenium](https://img.shields.io/badge/built%20with-Selenium-yellow.svg)](https://github.com/SeleniumHQ/selenium)
[![built with Python3](https://img.shields.io/badge/built%20with-Python3-red.svg)](https://www.python.org/)
[![Travis](https://img.shields.io/travis/rust-lang/rust.svg)](https://travis-ci.org/socialbotspy/FacebookPy)

## **Installation**

It is recomended to use via pyenv
We will be supporting python 3.6.0 and above going forward

```
curl https://pyenv.run | bash
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
pyenv install 3.6.0
pyenv local 3.6.0
pip install -r requirements.txt
```

<br />

Now all you need is a **quickstart** script into your computer, go ahead and run it in the command prompt as:

```elm
python quickstart.py --username abc@gmail.com --userid abc.pqr --password 123
```

> **PRO**:
> Read about difference between username and userid for facebook: https://www.facebook.com/help/211813265517027?helpref=faq_content

> **PRO**:
> Read more about passing arguments from the command line interface in the section - [Pass arguments by CLI](#pass-arguments-by-cli).

<br />

##### 🚁 You can provide _username_ & _password_ inside the **quickstart** script, too!

```python
# inside quickstart script

session = FacebookPy(username="abc",
                  password="123")
```

<br />

# Documentation

### Table of Contents

* [FacebookPy Available Features](#facebookpy-available-features)
  * [Following](#following)
  * [Following by a list](#following-by-a-list)
  * [Follow someone else's followers](#follow-someone-elses-followers)
  * [Follow the likers of posts of users](#follow-the-likers-of-photos-of-users)
  * [Friending](#friending)
  * [Friending by a list](#friending-by-a-list)
  * [UnFriending by a list](#unfriending-by-a-list)
  * [UnFriending by url list](#unfriending-by-url-list)
  * [Restricting Likes](#restricting-likes)
  * [Ignoring Users](#ignoring-users)
  * [Excluding friends](#excluding-friends)
  * [Confirm friends received](confirm-friends-received)
  * [Add suggested friends](Add-suggested-friends)
  * [Quota Supervisor](#quota-supervisor)
  * [Get recent friends](#get-recent-friends):
  * [Invite friends to page](#invite-friends-to-page) 
  * [Add likers from term](#add-likers-from-term)
  * [Withdraw outgoing friends requests](#withdraw-outgoing-friends-requests)

<br />

## FacebookPy Available Features

### Following

```python
# default enabled=False, follows ~ 10% of the users from the images, times=1
# (only follows a user once (if unfollowed again))

session.set_do_follow(enabled=True, percentage=10, times=2)
```

### Following by a list

##### This will follow each account from a list of facebook nicknames

```python
follow_by_list(followlist=['samantha3', 'larry_ok'], times=1, sleep_delay=600, interact=False)
```

_only follows a user once (if unfollowed again) would be useful for the precise targeting_  
`sleep_delay` is used to define break time after some good following (_averagely ~`10` follows_)  
For example, if one needs to get followbacks from followers of a chosen account/group of accounts.

```python
accs = ['therock','natgeo']
session.follow_by_list(accs, times=1, sleep_delay=600, interact=False)
```

* You can also **interact** with the followed users by enabling `interact=True` which will use the configuration of `set_user_interact` setting:  

```python
session.set_user_interact(amount=4,
                 percentage=50,
                  randomize=True,
                   media='Photo')
session.follow_by_list(followlist=['samantha3', 'larry_ok'], times=2, sleep_delay=600, interact=True)
```

### Follow someone else's followers

```python
# Follows the followers of each given user
# The usernames can be either a list or a string
# The amount is for each account, in this case 30 users will be followed
# If randomize is false it will pick in a top-down fashion

session.follow_user_followers(['friend1', 'friend2', 'friend3'], amount=10, randomize=False)

# default sleep_delay=600 (10min) for every 10 user following, in this case
# sleep for 60 seconds

session.follow_user_followers(['friend1', 'friend2', 'friend3'], amount=10, randomize=False, sleep_delay=60)
```

> **Note**: [simulation](#simulation) takes place while running this feature.

### Follow the likers of posts(only non video/non-photo) of users

##### This will follow the people those liked photos of given list of users

```python
session.follow_likers(['user1' , 'user2'], photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=False)
```

```python
session.set_user_interact(amount=2,
                    percentage=70,
                    randomize=True,
                    media='Photo')
session.follow_likers(['user1' , 'user2'], photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=True)
```

### Friending

```python
session.friend('user1', daysold=365, max_pic = 100, sleep_delay=600, interact=False)
```

### Friending by a list

##### This will add as friend each account from a list of facebook userids

```python
friend_by_list(friendlist=['samantha3', 'larry_ok'], times=1, sleep_delay=600, interact=False)
```

### UnFriending by a list

##### This will unfriend each account from a list of facebook userids

```python
unfriend_by_list(friendlist=['samantha3', 'larry_ok'], sleep_delay=6)
```

### UnFriending by url list

##### This will unfriend each account from a list of facebook profile full urls

```python
unfriend_by_urllist(urllist=["facebook.com/profile.php?id=100023983575804&fref=pb&hc_location=friends_tab", "https://www.facebook.com/profile.php?id=100021936281017&fref=pb&hc_location=friends_tab"])
```

### Restricting Likes

```python
session.set_dont_like(['#exactmatch', '[startswith', ']endswith', 'broadmatch'])
```

### Ignoring Users

```python
# completely ignore liking images from certain users

session.set_ignore_users(['random_user', 'another_username'])
```

### Excluding friends

```python
# will prevent commenting on and unfollowing your good friends (the images will
# still be liked)

session.set_dont_include(['friend1', 'friend2', 'friend3'])
```

### Follow/Unfollow/exclude not working?

If you notice that one or more of the above functionalities are not working as expected - e.g. you have specified:

```python
session.set_do_follow(enabled=True, percentage=10, times=2)
```

### confirm friends received?

Confirm all the friends requests recieved.

    session.confirm_friends()

### add suggested friends?

From friends suggested by facebook add top few

    session.add_suggested_friends()

```python
session.set_do_follow(enabled=True, percentage=10, times=2)
```

### Bypass Suspicious Login Attempt

If you're having issues with the "we detected an unusual login attempt" message,
you can bypass it setting FacebookPy in this way:

```python
session = FacebookPy(username=facebook_username, password=facebook_password, bypass_suspicious_attempt=True)
```

### Quota Supervisor

```python
  session.set_quota_supervisor(
                      Settings, enabled=True,
                      sleep_after=["likes", "comments_d", "follows", "unfollows", "server_calls_h"],
                      sleepyhead=True,
                      stochastic_flow=True,
                      notify_me=True,
                      peak_likes=(57, 585),
                      peak_comments=(21, 182),
                      peak_follows=(48, None),
                      peak_unfollows=(35, 402),
                      peak_server_calls=(None, 4700))
```

### get recent friends

```python
  session.get_recent_friends()
```

### invite friends to page

```python
  session.invite_friends_to_page(friendslist=['samantha3', 'larry_ok'])
```

### add likers from term

It searches for pages with a term , then visits each of those pages and adds the likers of those pages

```python
     session.add_likers_from_term(search_term = "fantasy")
```


### withdraw outgoing friends requests

```python
    session.withdraw_outgoing_friends_requests()
```

## How to run:

 -  modify `quickstart.py` according to your requirements
 -  `python quickstart.py -u <myusername> -p <mypssword> -ui <my_userid>`


## How to schedule as a job:

    */10 * * * * bash /path/to/FacebookPy/run_facebookpy_only_once_for_mac.sh /path/to/FacebookPy/quickstart.py $USERNAME $PASSWORD $USERID


## Help build socialbotspy
Check out this short guide on [how to start contributing!](https://github.com/InstaPy/instapy-docs/blob/master/CONTRIBUTORS.md).
