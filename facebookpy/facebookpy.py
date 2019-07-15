"""OS Modules environ method to get the setup vars from the Environment"""
# import built-in & third-party modules
import time
from math import ceil
import random
import traceback
import os
import sqlite3
from pyvirtualdisplay import Display
import logging
from contextlib import contextmanager
import unicodedata
from sys import exit as clean_exit
from tempfile import gettempdir

from .comment_util import comment_image
from .comment_util import verify_commenting
from .like_util import check_link
from .like_util import verify_liking
from .like_util import like_image
from .like_util import get_links_for_username
from .login_util import login_user
from socialcommons.print_log_writer import log_follower_num
from socialcommons.print_log_writer import log_following_num

from socialcommons.time_util import sleep
from socialcommons.util import validate_userid
from socialcommons.util import interruption_handler
from socialcommons.util import highlight_print
from socialcommons.util import truncate_float
from socialcommons.util import save_account_progress
from socialcommons.util import parse_cli_args
from .unfollow_util  import get_given_user_followers
from .unfollow_util  import unfollow_user
from .unfollow_util  import follow_user
from .unfollow_util  import follow_restriction
from .unfollow_util  import dump_follow_restriction
from .unfriend_util import friend_user
from .unfriend_util import unfriend_user
from .unfriend_util import unfriend_user_by_url
from .commenters_util import users_liked
from .commenters_util import get_post_urls_from_profile
from .database_engine import get_database
from socialcommons.browser import set_selenium_local_session
from socialcommons.browser import close_browser
from socialcommons.file_manager import get_workspace
from socialcommons.file_manager import get_logfolder

from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from socialcommons.exceptions import SocialPyError
from .settings import Settings
import pyautogui

HOME = "/Users/ishandutta2007"
CWD = HOME + "/Documents/Projects/FacebookPy"

class FacebookPy:
    """Class to be instantiated to use the script"""
    def __init__(self,
                 username=None,
                 userid=None,
                 password=None,
                 nogui=False,
                 selenium_local_session=True,
                 use_firefox=False,
                 browser_profile_path=None,
                 page_delay=25,
                 show_logs=True,
                 headless_browser=False,
                 proxy_address=None,
                 proxy_chrome_extension=None,
                 proxy_port=None,
                 disable_image_load=False,
                 bypass_suspicious_attempt=False,
                 bypass_with_mobile=False,
                 multi_logs=True):

        cli_args = parse_cli_args()
        username = cli_args.username or username
        userid = cli_args.userid or userid
        password = cli_args.password or password
        use_firefox = cli_args.use_firefox or use_firefox
        page_delay = cli_args.page_delay or page_delay
        headless_browser = cli_args.headless_browser or headless_browser
        proxy_address = cli_args.proxy_address or proxy_address
        proxy_port = cli_args.proxy_port or proxy_port
        disable_image_load = cli_args.disable_image_load or disable_image_load
        bypass_suspicious_attempt = (
            cli_args.bypass_suspicious_attempt or bypass_suspicious_attempt)
        bypass_with_mobile = cli_args.bypass_with_mobile or bypass_with_mobile

        # IS_RUNNING = True
        # workspace must be ready before anything
        if not get_workspace(Settings):
            raise SocialPyError(
                "Oh no! I don't have a workspace to work at :'(")

        self.nogui = nogui
        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.proxy_chrome_extension = proxy_chrome_extension
        self.selenium_local_session = selenium_local_session
        self.bypass_suspicious_attempt = bypass_suspicious_attempt
        self.bypass_with_mobile = bypass_with_mobile
        self.disable_image_load = disable_image_load

        self.username = username or os.environ.get('FACEBOOK_USER')
        self.password = password or os.environ.get('FACEBOOK_PW')

        self.userid = userid
        if not self.userid:
            self.userid = self.username.split('@')[0]

        Settings.profile["name"] = self.username

        self.page_delay = page_delay
        self.switch_language = True
        self.use_firefox = use_firefox
        Settings.use_firefox = self.use_firefox
        self.browser_profile_path = browser_profile_path

        self.do_comment = False
        self.comment_percentage = 0
        self.comments = ['Cool!', 'Nice!', 'Looks good!']
        self.photo_comments = []
        self.video_comments = []

        # self.do_reply_to_comments = False
        # self.reply_to_comments_percent = 0
        # self.comment_replies = []
        # self.photo_comment_replies = []
        # self.video_comment_replies = []

        self.liked_img = 0
        self.already_liked = 0
        self.liked_comments = 0
        self.commented = 0
        self.replied_to_comments = 0
        self.followed = 0
        self.already_followed = 0
        self.unfollowed = 0
        self.followed_by = 0
        self.following_num = 0
        self.inap_img = 0
        self.not_valid_users = 0
        self.video_played = 0
        self.already_Visited = 0

        self.follow_times = 1
        self.friend_times = 1
        self.invite_times = 1
        self.do_follow = False
        self.follow_percentage = 0
        self.dont_include = set()
        self.white_list = set()
        self.blacklist = {'enabled': 'True', 'campaign': ''}
        self.automatedFollowedPool = {"all": [], "eligible": []}
        self.do_like = False
        self.like_percentage = 0
        self.smart_hashtags = []

        self.dont_like = ['sex', 'nsfw']
        self.mandatory_words = []
        self.ignore_if_contains = []
        self.ignore_users = []

        self.user_interact_amount = 0
        self.user_interact_media = None
        self.user_interact_percentage = 0
        self.user_interact_random = False
        self.dont_follow_inap_post = True

        # self.use_clarifai = False
        # self.clarifai_api_key = None
        # self.clarifai_models = []
        # self.clarifai_workflow = []
        # self.clarifai_probability = 0.50
        # self.clarifai_img_tags = []
        # self.clarifai_img_tags_skip = []
        # self.clarifai_full_match = False
        # self.clarifai_check_video = False
        # self.clarifai_proxy = None

        self.potency_ratio = None   # 1.3466
        self.delimit_by_numbers = None

        self.max_followers = None   # 90000
        self.max_following = None   # 66834
        self.min_followers = None   # 35
        self.min_following = None   # 27

        self.delimit_liking = False
        self.liking_approved = True
        self.max_likes = 1000
        self.min_likes = 0

        self.delimit_commenting = False
        self.commenting_approved = True
        self.max_comments = 35
        self.min_comments = 0
        self.comments_mandatory_words = []
        self.max_posts = None
        self.min_posts = None
        self.skip_business_categories = []
        self.dont_skip_business_categories = []
        self.skip_business = False
        self.skip_no_profile_pic = False
        self.skip_private = True
        self.skip_business_percentage = 100
        self.skip_no_profile_pic_percentage = 100
        self.skip_private_percentage = 100

        self.relationship_data = {
            username: {"all_following": [], "all_followers": []}}

        self.simulation = {"enabled": True, "percentage": 100}

        self.mandatory_language = False
        self.mandatory_character = []
        self.check_letters = {}

        # use this variable to terminate the nested loops after quotient
        # reaches
        self.quotient_breach = False
        # hold the consecutive jumps and set max of it used with QS to break
        # loops
        self.jumps = {"consequent": {"likes": 0, "comments": 0, "follows": 0,
                                     "unfollows": 0},
                      "limit": {"likes": 7, "comments": 3, "follows": 5,
                                "unfollows": 4}}

        # stores the features' name which are being used by other features
        self.internal_usage = {}

        if (
                self.proxy_address and self.proxy_port > 0) or \
                self.proxy_chrome_extension:
            Settings.connection_type = "proxy"

        self.aborting = False
        self.start_time = time.time()

        # assign logger
        self.show_logs = show_logs
        Settings.show_logs = show_logs or None
        self.multi_logs = multi_logs
        self.logfolder = get_logfolder(self.username, self.multi_logs, Settings)
        self.logger = self.get_facebookpy_logger(self.show_logs)

        get_database(Settings, make=True)  # IMPORTANT: think twice before relocating

        if self.selenium_local_session is True:
            self.set_selenium_local_session(Settings)

    def get_facebookpy_logger(self, show_logs):
        """
        Handles the creation and retrieval of loggers to avoid
        re-instantiation.
        """

        existing_logger = Settings.loggers.get(self.username)
        if existing_logger is not None:
            return existing_logger
        else:
            # initialize and setup logging system for the FacebookPy object
            logger = logging.getLogger(self.username)
            logger.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                '{}general.log'.format(self.logfolder))
            file_handler.setLevel(logging.DEBUG)
            extra = {"username": self.username}
            logger_formatter = logging.Formatter(
                '%(levelname)s [%(asctime)s] [FacebookPy:%(username)s]  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(logger_formatter)
            logger.addHandler(file_handler)

            if show_logs is True:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_handler.setFormatter(logger_formatter)
                logger.addHandler(console_handler)

            logger = logging.LoggerAdapter(logger, extra)

            Settings.loggers[self.username] = logger
            Settings.logger = logger
            return logger

    def set_selenium_local_session(self, Settings):
        self.browser, err_msg = \
            set_selenium_local_session(self.proxy_address,
                                       self.proxy_port,
                                       self.proxy_chrome_extension,
                                       self.headless_browser,
                                       self.use_firefox,
                                       self.browser_profile_path,
                                       # Replaces
                                       # browser User
                                       # Agent from
                                       # "HeadlessChrome".
                                       self.disable_image_load,
                                       self.page_delay,
                                       self.logger,
                                       Settings)
        if len(err_msg) > 0:
            raise SocialPyError(err_msg)


    def login(self):
        """Used to login the user either with the username and password"""
        if not login_user(self.browser,
                          self.username,
                          self.userid,
                          self.password,
                          self.logger,
                          self.logfolder,
                          self.switch_language,
                          self.bypass_suspicious_attempt,
                          self.bypass_with_mobile):
            message = "Wrong login data!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "critical",
                            self.logger)

            self.aborting = True

        else:
            message = "Logged in successfully!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "info",
                            self.logger)
            # try to save account progress
            try:
                save_account_progress(self.browser,
                                    "https://www.facebook.com/",
                                    self.username,
                                    self.logger)
            except Exception:
                self.logger.warning(
                    'Unable to save account progress, skipping data update')

        self.followed_by = log_follower_num(self.browser,
                                            Settings,
                                            "https://www.facebook.com/",
                                            self.username,
                                            self.userid,
                                            self.logfolder)

        self.following_num = log_following_num(self.browser,
                                            Settings,
                                            "https://www.facebook.com/",
                                            self.username,
                                            self.userid,
                                            self.logfolder)

        return self


    def set_do_follow(self, enabled=False, percentage=0, times=1):
        """Defines if the user of the liked image should be followed"""
        if self.aborting:
            return self

        self.follow_times = times
        self.do_follow = enabled
        self.follow_percentage = percentage

        return self

    def set_user_interact(self,
                          amount=10,
                          percentage=100,
                          randomize=False,
                          media=None):
        """Define if posts of given user should be interacted"""
        if self.aborting:
            return self

        self.user_interact_amount = amount
        self.user_interact_random = randomize
        self.user_interact_percentage = percentage
        self.user_interact_media = media

        return self

    def set_dont_include(self, friends=None):
        """Defines which accounts should not be unfollowed"""
        if self.aborting:
            return self

        self.dont_include = set(friends) or set()
        self.white_list = set(friends) or set()

        return self

    def fetch_birthdays(self):
        self.browser.get("https://www.facebook.com/{}/friends".format(self.userid))
        time.sleep(2)
        try:
            for i in range(10):
                # self.browser.execute_script("window.scrollTo(0, " + str(1000+i*1000) + ")")
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            profile_as = self.browser.find_elements_by_css_selector("li > div > div > div.uiProfileBlockContent > div > div:nth-child(2) > div > a")

            print("Found", len(profile_as), "profiles")
            profiles = []
            for profile_a in profile_as:
                friend_url = profile_a.get_attribute('href').split('?')[0].split('#')[0]
                if len(friend_url.split('/')) > 4:
                    continue
                profiles.append(friend_url)

            for profile in profiles:

                self.browser.get(profile+'/about')
                overview_events = self.browser.find_elements_by_css_selector("div > ul > li > div > div > span > div:nth-child(2)")
                for overview_event in overview_events:
                    # print(profile, overview_event.text)
                    try:
                        from dateutil.parser import parse
                        dob = parse(overview_event.text)
                        print(profile, dob)
                        continue
                    except Exception as e:
                        self.logger.error(e)
        except Exception as e:
                self.logger.error(e)
                traceback.print_exc()



    def follow_likers(self, userids, photos_grab_amount=3,
                      follow_likers_per_photo=3, randomize=True,
                      sleep_delay=600,
                      interact=False):
        """ Follows users' likers """
        if self.aborting:
            return self

        message = "Starting to follow likers.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(userids, list):
            userids = [userids]

        if photos_grab_amount > 12:
            self.logger.info(
                "Sorry, you can only grab likers from first 12 photos for "
                "given username now.\n")
            photos_grab_amount = 12

        followed_all = 0
        followed_new = 0

        # hold the current global values for differentiating at the end
        already_followed_init = self.already_followed
        not_valid_users_init = self.not_valid_users
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        relax_point = random.randint(7,
                                     14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        self.quotient_breach = False

        for userid in userids:
            if self.quotient_breach:
                break

            post_urls = get_post_urls_from_profile(self.browser, userid,
                                                   photos_grab_amount,
                                                   randomize)
            sleep(1)
            if not isinstance(post_urls, list):
                post_urls = [post_urls]

            # self.logger.info('post_urls:')
            # self.logger.info(post_urls)

            for post_url in post_urls:
                if self.quotient_breach:
                    break

                likers = users_liked(self.browser, post_url, self.logger,
                                     follow_likers_per_photo)
                # This way of iterating will prevent sleep interference
                # between functions
                random.shuffle(likers)

                for liker in likers[:follow_likers_per_photo]:
                    if self.quotient_breach:
                        self.logger.warning(
                            "--> Follow quotient reached its peak!"
                            "\t~leaving Follow-Likers activity\n")
                        break

                    with self.feature_in_feature("follow_by_list", True):
                        followed = self.follow_by_list(liker,
                                                       self.follow_times,
                                                       sleep_delay,
                                                       interact)
                    if followed > 0:
                        followed_all += 1
                        followed_new += 1
                        self.logger.info(
                            "Total Follow: {}\n".format(str(followed_all)))
                        # Take a break after a good following
                        if followed_new >= relax_point:
                            delay_random = random.randint(
                                ceil(sleep_delay * 0.85),
                                ceil(sleep_delay * 1.14))
                            sleep_time = ("{} seconds".format(delay_random) if
                                          delay_random < 60 else
                                          "{} minutes".format(truncate_float(
                                              delay_random / 60, 2)))
                            self.logger.info(
                                "------=>  Followed {} new users ~sleeping "
                                "about {}"
                                .format(followed_new, sleep_time))
                            sleep(delay_random)
                            relax_point = random.randint(7, 14)
                            followed_new = 0
                            pass

        self.logger.info("Finished following Likers!\n")

        # find the feature-wide action sizes by taking a difference
        already_followed = (self.already_followed - already_followed_init)
        not_valid_users = (self.not_valid_users - not_valid_users_init)
        liked = (self.liked_img - liked_init)
        already_liked = (self.already_liked - already_liked_init)
        commented = (self.commented - commented_init)
        inap_img = (self.inap_img - inap_img_init)

        # print results
        self.logger.info("Followed: {}".format(followed_all))
        self.logger.info("Already followed: {}".format(already_followed))
        self.logger.info("Not valid users: {}".format(not_valid_users))

        if interact is True:
            print('')
            # print results out of interactions
            self.logger.info("Liked: {}".format(liked))
            self.logger.info("Already Liked: {}".format(already_liked))
            self.logger.info("Commented: {}".format(commented))
            self.logger.info("Inappropriate: {}".format(inap_img))

        return self

    def friend_by_list(self, friendlist, times=1, sleep_delay=600,
                       interact=False):
        for acc_to_friend in friendlist:
            friend_state, msg = friend_user(self.browser,
                                            "profile",
                                            self.username,
                                            acc_to_friend,
                                            self.friend_times,
                                            self.blacklist,
                                            self.logger,
                                            self.logfolder)

    def unfriend_by_list(self, friendlist, sleep_delay=6):
        for acc_to_unfriend in friendlist:
            friend_state, msg = unfriend_user(self.browser,
                                            "profile",
                                            self.username,
                                            acc_to_unfriend,
                                            None,
                                            self.blacklist,
                                            self.logger,
                                            self.logfolder,
                                            sleep_delay=sleep_delay)

    def unfriend_by_urllist(self, urllist, sleep_delay=6):
        for url in urllist:
            friend_state, msg = unfriend_user_by_url(self.browser,
                                            "profile",
                                            self.username,
                                            url,
                                            None,
                                            self.blacklist,
                                            self.logger,
                                            self.logfolder,
                                            sleep_delay=sleep_delay)

    def follow_by_list(self, followlist, times=1, sleep_delay=600,
                       interact=False):
        """Allows to follow by any scrapped list"""
        if not isinstance(followlist, list):
            followlist = [followlist]

        if self.aborting:
            self.logger.info(">>> self aborting prevented")
            # return self

        # standalone means this feature is started by the user
        standalone = True if "follow_by_list" not in \
                             self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        users_validated = True if not standalone and not \
            self.internal_usage["follow_by_list"]["validate"] else False

        self.follow_times = times or 0

        followed_all = 0
        followed_new = 0
        already_followed = 0
        not_valid_users = 0

        # hold the current global values for differentiating at the end
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        relax_point = random.randint(7, 14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        self.quotient_breach = False

        for acc_to_follow in followlist:
            if self.jumps["consequent"]["follows"] >= self.jumps["limit"][
                    "follows"]:
                self.logger.warning(
                    "--> Follow quotient reached its peak!\t~leaving "
                    "Follow-By-Tags activity\n")
                # reset jump counter before breaking the loop
                self.jumps["consequent"]["follows"] = 0
                # turn on `quotient_breach` to break the internal iterators
                # of the caller
                self.quotient_breach = True if not standalone else False
                break

            if follow_restriction("read", acc_to_follow, self.follow_times,
                                  self.logger):
                print('')
                continue

            if not users_validated:
                # Verify if the user should be followed
                validation, details = self.validate_user_call(acc_to_follow)
                if validation is not True or acc_to_follow == self.username:
                    self.logger.info(
                        "--> Not a valid user: {}".format(details))
                    not_valid_users += 1
                    continue

            # Take a break after a good following
            if followed_new >= relax_point:
                delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
                sleep_time = ("{} seconds".format(delay_random) if
                              delay_random < 60 else
                              "{} minutes".format(truncate_float(
                                  delay_random / 60, 2)))
                self.logger.info("Followed {} new users  ~sleeping about {}\n"
                                 .format(followed_new, sleep_time))
                sleep(delay_random)
                followed_new = 0
                relax_point = random.randint(7, 14)
                pass

            if not follow_restriction("read", acc_to_follow, self.follow_times,
                                      self.logger):
                follow_state, msg = follow_user(self.browser,
                                                "profile",
                                                self.username,
                                                acc_to_follow,
                                                None,
                                                self.blacklist,
                                                self.logger,
                                                self.logfolder, Settings)
                sleep(random.randint(1, 3))

                if follow_state is True:
                    followed_all += 1
                    followed_new += 1
                    # reset jump counter after a successful follow
                    self.jumps["consequent"]["follows"] = 0

                    if standalone:  # print only for external usage (
                        # internal callers have their printers)
                        self.logger.info(
                            "Total Follow: {}\n".format(str(followed_all)))

                    # Check if interaction is expected
                    if interact and self.do_like:
                        do_interact = random.randint(0,
                                                     100) <= \
                            self.user_interact_percentage
                        # Do interactions if any
                        if do_interact and self.user_interact_amount > 0:
                            original_do_follow = self.do_follow  # store the
                            # original value of `self.do_follow`
                            self.do_follow = False  # disable following
                            # temporarily cos the user is already followed
                            # above
                            self.interact_by_users(acc_to_follow,
                                                   self.user_interact_amount,
                                                   self.user_interact_random,
                                                   self.user_interact_media)
                            self.do_follow = original_do_follow  # revert
                            # back original `self.do_follow` value (either
                            # it was `False` or `True`)

                elif msg == "already followed":
                    already_followed += 1

                elif msg == "jumped":
                    # will break the loop after certain consecutive jumps
                    self.jumps["consequent"]["follows"] += 1

                sleep(1)

        if standalone:  # print only for external usage (internal callers
            # have their printers)
            self.logger.info("Finished following by List!\n")
            # print summary
            self.logger.info("Followed: {}".format(followed_all))
            self.logger.info("Already followed: {}".format(already_followed))
            self.logger.info("Not valid users: {}".format(not_valid_users))

            if interact is True:
                print('')
                # find the feature-wide action sizes by taking a difference
                liked = (self.liked_img - liked_init)
                already_liked = (self.already_liked - already_liked_init)
                commented = (self.commented - commented_init)
                inap_img = (self.inap_img - inap_img_init)

                # print the summary out of interactions
                self.logger.info("Liked: {}".format(liked))
                self.logger.info("Already Liked: {}".format(already_liked))
                self.logger.info("Commented: {}".format(commented))
                self.logger.info("Inappropriate: {}".format(inap_img))

        # always sum up general objects regardless of the request size
        self.followed += followed_all
        self.already_followed += already_followed
        self.not_valid_users += not_valid_users

        return followed_all

    def set_relationship_bounds(self,
                                enabled=None,
                                potency_ratio=None,
                                delimit_by_numbers=None,
                                min_posts=None,
                                max_posts=None,
                                max_followers=None,
                                max_following=None,
                                min_followers=None,
                                min_following=None):
        """Sets the potency ratio and limits to the provide an efficient
        activity between the targeted masses"""

        self.potency_ratio = potency_ratio if enabled is True else None
        self.delimit_by_numbers = delimit_by_numbers if enabled is True else \
            None

        self.max_followers = max_followers
        self.min_followers = min_followers

        self.max_following = max_following
        self.min_following = min_following

        self.min_posts = min_posts if enabled is True else None
        self.max_posts = max_posts if enabled is True else None

    def validate_user_call(self, user_name):
        """ Short call of validate_userid() function """
        validation, details = \
            validate_userid(self.browser,
                            "https://facebook.com/",
                            user_name,
                            self.username,
                            self.userid,
                            self.ignore_users,
                            self.blacklist,
                            self.potency_ratio,
                            self.delimit_by_numbers,
                            self.max_followers,
                            self.max_following,
                            self.min_followers,
                            self.min_following,
                            self.min_posts,
                            self.max_posts,
                            self.skip_private,
                            self.skip_private_percentage,
                            self.skip_no_profile_pic,
                            self.skip_no_profile_pic_percentage,
                            self.skip_business,
                            self.skip_business_percentage,
                            self.skip_business_categories,
                            self.dont_skip_business_categories,
                            self.logger,
                            self.logfolder, Settings)
        return validation, details

    def invite_restriction(self, operation, pagename, username, limit, logger):
        """ Keep track of the followed users and help avoid excessive follow of
        the same user """
        try:
            # get a DB and start a connection
            db, id = get_database(Settings)
            conn = sqlite3.connect(db)

            with conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                cur.execute(
                    "SELECT * FROM inviteRestriction WHERE profile_id=:id_var "
                    "AND pagename=:page_var AND username=:name_var",
                    {"id_var": id, "page_var": pagename,  "name_var": username})
                data = cur.fetchone()
                invite_data = dict(data) if data else None

                if operation == "write":
                    if invite_data is None:
                        # write a new record
                        cur.execute(
                            "INSERT INTO inviteRestriction (profile_id, "
                            "pagename, username, times) VALUES (?, ?, ?, ?)",
                            (id, pagename, username, 1))
                    else:
                        # update the existing record
                        invite_data["times"] += 1
                        sql = "UPDATE inviteRestriction set times = ? WHERE " \
                              "profile_id=? AND pagename = ? AND username = ?"
                        cur.execute(sql, (invite_data["times"], id, pagename, username))

                    # commit the latest changes
                    conn.commit()

                elif operation == "read":
                    if invite_data is None:
                        return False

                    elif invite_data["times"] < limit:
                        return False

                    else:
                        exceed_msg = "" if invite_data[
                            "times"] == limit else "more than "
                        logger.info("---> {} has already been invited {}{} times"
                                    .format(username, exceed_msg, str(limit)))
                        return True
        except Exception as exc:
            logger.error(
                "Dap! Error occurred with invite Restriction:\n\t{}".format(
                    str(exc).encode("utf-8")))
            traceback.print_exc()
        finally:
            if conn:
                conn.close()

    def fetch_smart_comments(self, is_video, temp_comments):
        if temp_comments:
            # Use clarifai related comments only!
            comments = temp_comments
        elif is_video:
            comments = (self.comments +
                        self.video_comments)
        else:
            comments = (self.comments +
                        self.photo_comments)

        return comments

    def confirm_friends(self, max_confirms=100, sleep_delay = 6):
        self.browser.get("https://www.facebook.com/friends/requests/")
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
        confirms = 0
        try:
            rows = self.browser.find_elements_by_css_selector("div.ruResponseSectionContainer")
            for i in range(0, len(rows)):
                try:
                    confirm_button = self.browser.find_elements_by_css_selector("div.ruResponseSectionContainer")[i].find_element_by_xpath("//div/div/div[2]/div/div/button[text()='Confirm']")
                    self.logger.info("Confirm button found, confirming...")
                    try:
                        confirm_button.click()
                    except Exception as e:
                        self.logger.error(e)
                    self.logger.info("Clicked {}".format(confirm_button.text))
                    confirms += 1
                    self.logger.info("Confirms sent in this iteration: {}".format(confirms))
                    if confirms >= max_confirms:
                        self.logger.info("max_confirms({}) for this iteration reached , Returning...".format(max_confirms))
                        return
                except Exception as e:
                    self.logger.error(e)
                sleep(delay_random)
        except Exception as e:
            self.logger.error(e)
        return confirms

    def add_suggested_friends(self, max_confirms=100, sleep_delay = 6):
        self.browser.get("https://www.facebook.com/friends/requests/")
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
        adds = 0
        try:
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            rows = self.browser.find_elements_by_css_selector("div.FriendButton")
            for i in range(0, len(rows)):
                try:
                    row_item = self.browser.find_elements_by_css_selector("div.FriendButton")[i]
                    # last_height = self.browser.execute_script("return document.body.scrollHeight")
                    confirm_button = row_item.find_element_by_xpath("//button[text()='Add Friend']")
                    self.logger.info("Add Friend button found, adding...")
                    try:
                        confirm_button.click()
                        # ActionChains(self.browser).move_to_element(confirm_button).perform()
                        # ActionChains(self.browser).click().perform()
                    except Exception as e:
                        self.logger.error(e)
                    self.logger.info("Clicked {}".format(confirm_button.text))
                    adds += 1
                    self.logger.info("Add Friends sent in this iteration: {}".format(adds))
                    if adds >= max_confirms:
                        self.logger.info("max Add Friends ({}) for this iteration reached , Returning...".format(max_confirms))
                        return
                except Exception as e:
                    self.logger.error(e)
                sleep(delay_random)
        except Exception as e:
            self.logger.error(e)
        return adds

    def get_recent_friends(self):
        self.browser.get("https://www.facebook.com/{}/friends_recent".format(self.userid))
        friend_elems = self.browser.find_elements_by_css_selector("ul > li > div > div > div.uiProfileBlockContent > div > div:nth-child(2) > div > a")
        friends = []
        for friend_elem  in friend_elems:
            uid = friend_elem.get_attribute('href').split('?')[0].split('/')[3]
            if uid == 'profile.php':
                continue
            friends.append(uid)
        return friends

    def get_recent_unnamed_friend_urls(self):
        self.browser.get("https://www.facebook.com/{}/friends_recent".format(self.userid))
        friend_elems = self.browser.find_elements_by_css_selector("ul > li > div > div > div.uiProfileBlockContent > div > div:nth-child(2) > div > a")
        friend_urls = []
        for friend_elem  in friend_elems:
            uid = friend_elem.get_attribute('href').split('?')[0].split('/')[3]
            if uid != 'profile.php':
                continue
            friend_urls.append(friend_elem.get_attribute('href'))
        return friend_urls

    def withdraw_outgoing_friends_requests(self, sleep_delay=6):
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
        self.browser.get("https://www.facebook.com/friends/requests/?fcref=ft&outgoing=1")
        sent_btns = self.browser.find_elements_by_css_selector("button.FriendRequestOutgoing.outgoingButton")
        for btn in sent_btns:
            try:
                if 'hidden_elem' in btn.get_attribute('class'):
                    continue
                ActionChains(self.browser).move_to_element(btn).perform()
                ActionChains(self.browser).click().perform()
                self.logger.info("{} Clicked".format(btn.text))
                sleep(delay_random)
                retry_times = 0
                while(retry_times < 10):
                    try:
                        sleep(delay_random)
                        dropx, dropy = pyautogui.locateCenterOnScreen(CWD + '/pngs/cancel_request.png', grayscale=True, confidence=.7)
                        self.logger.info("cancel_request.png is Visible, lets click it")
                        pyautogui.moveTo(dropx, dropy)
                        sleep(delay_random)
                        pyautogui.click()
                        pyautogui.doubleClick()
                        sleep(delay_random*5)
                        self.logger.info("cancel_request.png Clicked")
                        break
                    except Exception as e:
                        self.logger.info('cancel_request.png is not yet visible. Error: {}'.format(e))
                    retry_times = retry_times + 1
            except Exception as e:
                self.logger.error(e)

    def add_likers_of_page(self, page_likers_url, sleep_delay=6):
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
        self.browser.get(page_likers_url)
        add_btns = self.browser.find_elements_by_css_selector("button.FriendRequestAdd.addButton")

        pending = 0
        for btn in add_btns:
            try:
                if 'hidden_elem' in btn.get_attribute('class'):
                    pending += 1
                    continue
                ActionChains(self.browser).move_to_element(btn).perform()
                ActionChains(self.browser).click().perform()
                self.logger.info("{} Clicked".format(btn.text))
                sleep(delay_random)
            except Exception as e:
                self.logger.error(e)

        if pending > 0:
            self.logger.info("{} pending sent outs".format(pending))

    def invite_friends_to_page(self, friendslist, pagename, sleep_delay=6):
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
        net_invited_friends = []
        for friend in friendslist:
            try:
                if self.invite_restriction("read", pagename, friend, self.invite_times, self.logger):
                    self.logger.info('Already invited {} to page {}, {} times'.format(friend, pagename, self.invite_times))
                    net_invited_friends.append(friend)
                    continue
                self.logger.info("Visiting {}".format(friend))
                self.browser.get("https://www.facebook.com/{}".format(friend))
                ellipse_elem = self.browser.find_element_by_css_selector("div#pagelet_timeline_profile_actions > div > div > button > i")
                ActionChains(self.browser).move_to_element(ellipse_elem).perform()
                ActionChains(self.browser).click().perform()
                sleep(delay_random)
                retry_times = 0
                while(retry_times < 10):
                    try:
                        sleep(delay_random)
                        dropx, dropy = pyautogui.locateCenterOnScreen(CWD + '/pngs/invite_to_page_option.png', grayscale=True, confidence=.7)
                        self.logger.info("invite_to_page_option.png is Visible, lets click it")
                        pyautogui.moveTo(dropx, dropy)
                        sleep(delay_random)
                        pyautogui.click()
                        pyautogui.doubleClick()
                        sleep(delay_random)
                        self.logger.info("invite_to_page_option.png Clicked")
                        break
                    except Exception as e:
                        self.logger.info('invite_to_page_option.png is not yet visible. Error: {}'.format(e))
                    retry_times = retry_times + 1
                sleep(delay_random)
                rows = self.browser.find_elements_by_css_selector("div > div > div > div > div > div > div > div > div.uiScrollableArea > div.uiScrollableAreaWrap > div > div > ul > li > div > table > tbody > tr")
                for row in rows:
                    text_elem = row.find_element_by_css_selector("td:nth-child(2) > div.ellipsis > a > span")
                    if text_elem.text!=pagename:
                        continue
                    button_elem = row.find_element_by_css_selector("td:nth-child(3) > button")
                    if button_elem.text == 'Invited':
                        self.logger.info('Already invited: {}'.format(friend))
                        net_invited_friends.append(friend)
                        self.invite_restriction("write", pagename, friend, None, self.logger)
                    else:
                        ActionChains(self.browser).move_to_element(button_elem).perform()
                        ActionChains(self.browser).click().perform()
                        self.logger.info('~---> Just invited: {}'.format(friend))
                        net_invited_friends.append(friend)
                        self.invite_restriction("write", pagename, friend, None, self.logger)
                        sleep(delay_random)
            except Exception as e:
                self.logger.error("Failed for friend {} with error {}".format(friend, e))
        return net_invited_friends

    def interact_by_users(self,
                          usernames,
                          amount=10,
                          randomize=False,
                          media=None):
        """Likes some amounts of images for each usernames"""
        if self.aborting:
            return self

        message = "Starting to interact by users.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        # standalone means this feature is started by the user
        standalone = True if "interact_by_users" not in \
                             self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        users_validated = True if not standalone and not \
            self.internal_usage["interact_by_users"]["validate"] else False

        total_liked_img = 0
        already_liked = 0
        inap_img = 0
        commented = 0
        followed = 0
        already_followed = 0
        not_valid_users = 0

        self.quotient_breach = False

        for index, username in enumerate(usernames):
            if self.quotient_breach:
                # keep `quotient_breach` active to break the internal
                # iterators of the caller
                self.quotient_breach = True if not standalone else False
                break

            self.logger.info(
                'Username [{}/{}]'.format(index + 1, len(usernames)))
            self.logger.info('--> {}'.format(username.encode('utf-8')))

            if not users_validated:
                validation, details = self.validate_user_call(username)
                if not validation:
                    self.logger.info(
                        "--> not a valid user: {}".format(details))
                    not_valid_users += 1
                    continue

            track = 'profile'
            # decision making
            # static conditions
            not_dont_include = username not in self.dont_include
            follow_restricted = follow_restriction("read", username,
                                                   self.follow_times,
                                                   self.logger)
            counter = 0
            while True:
                following = (random.randint(0,
                                            100) <= self.follow_percentage and
                             self.do_follow and
                             not_dont_include and
                             not follow_restricted)
                commenting = (random.randint(0,
                                             100) <= self.comment_percentage
                              and
                              self.do_comment and
                              not_dont_include)
                liking = (random.randint(0, 100) <= self.like_percentage)

                counter += 1

                # if we have only one image to like/comment
                if commenting and not liking and amount == 1:
                    continue

                if following or commenting or liking:
                    self.logger.info(
                        'username actions: following={} commenting={} '
                        'liking={}'.format(
                            following, commenting, liking))
                    break

                # if for some reason we have no actions on this user
                if counter > 5:
                    self.logger.info(
                        'username={} could not get interacted'.format(
                            username))
                    break

            try:
                links = get_links_for_username(self.browser,
                                               self.username,
                                               username,
                                               amount,
                                               self.logger,
                                               self.logfolder,
                                               randomize,
                                               media)
            except NoSuchElementException:
                self.logger.error('Element not found, skipping this username')
                continue

            if links is False:
                continue

            # Reset like counter for every username
            liked_img = 0

            for i, link in enumerate(links[:amount]):
                if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                        "likes"]:
                    self.logger.warning(
                        "--> Like quotient reached its peak!\t~leaving "
                        "Interact-By-Users activity\n")
                    self.quotient_breach = True
                    # reset jump counter after a breach report
                    self.jumps["consequent"]["likes"] = 0
                    break

                # Check if target has reached
                if liked_img >= amount:
                    self.logger.info('-------------')
                    self.logger.info("--> Total liked image reached it's "
                                     "amount given: {}".format(liked_img))
                    break

                self.logger.info(
                    'Post [{}/{}]'.format(liked_img + 1, len(links[:amount])))
                self.logger.info(link)

                try:
                    inappropriate, user_name, is_video, reason, scope = (
                        check_link(self.browser,
                                   link,
                                   self.dont_like,
                                   self.mandatory_words,
                                   self.mandatory_language,
                                   self.is_mandatory_character,
                                   self.mandatory_character,
                                   self.check_character_set,
                                   self.ignore_if_contains,
                                   self.logger))
                    track = "post"

                    if not inappropriate:
                        # after first image we roll again
                        if i > 0:
                            liking = (random.randint(0,
                                                     100) <=
                                      self.like_percentage)
                            commenting = (random.randint(0,
                                                         100) <=
                                          self.comment_percentage and
                                          self.do_comment and
                                          not_dont_include)

                        # like
                        if self.do_like and liking and self.delimit_liking:
                            self.liking_approved = \
                                verify_liking(self.browser,
                                              self.max_likes,
                                              self.min_likes,
                                              self.logger)

                        if self.do_like and liking and self.liking_approved:
                            like_state, msg = like_image(self.browser,
                                                         user_name,
                                                         self.blacklist,
                                                         self.logger,
                                                         self.logfolder,
                                                         Settings)
                            if like_state is True:
                                total_liked_img += 1
                                liked_img += 1
                                # reset jump counter after a successful like
                                self.jumps["consequent"]["likes"] = 0

                                # comment
                                checked_img = True
                                temp_comments = []

                                # if self.use_clarifai and commenting:
                                #     try:
                                #         # checked_img, temp_comments, \
                                #             # clarifai_tags = (
                                #             #     self.query_clarifai())

                                #     except Exception as err:
                                #         self.logger.error(
                                #             'Image check error: {}'.format(
                                #                 err))

                                if commenting and checked_img:

                                    if self.delimit_commenting:
                                        (self.commenting_approved,
                                         disapproval_reason) = \
                                            verify_commenting(
                                                self.browser,
                                                self.max_comments,
                                                self.min_comments,
                                                self.comments_mandatory_words,
                                                self.logger)
                                    if self.commenting_approved:
                                        # smart commenting
                                        comments = self.fetch_smart_comments(
                                            is_video,
                                            temp_comments)
                                        if comments:
                                            comment_state, msg = comment_image(
                                                self.browser,
                                                user_name,
                                                comments,
                                                self.blacklist,
                                                self.logger,
                                                self.logfolder,
                                                Settings)
                                            if comment_state is True:
                                                commented += 1

                                    else:
                                        self.logger.info(disapproval_reason)

                                else:
                                    self.logger.info('--> Not commented')
                                    sleep(1)

                            elif msg == "already liked":
                                already_liked += 1

                            elif msg == "jumped":
                                # will break the loop after certain
                                # consecutive jumps
                                self.jumps["consequent"]["likes"] += 1

                    else:
                        self.logger.info(
                            '--> Image not liked: {}'.format(
                                reason.encode('utf-8')))
                        inap_img += 1

                except NoSuchElementException as err:
                    self.logger.info('Invalid Page: {}'.format(err))

            # follow
            if following and not (self.dont_follow_inap_post and inap_img > 0):

                follow_state, msg = follow_user(
                    self.browser,
                    track,
                    self.username,
                    username,
                    None,
                    self.blacklist,
                    self.logger,
                    self.logfolder)
                if follow_state is True:
                    followed += 1

                elif msg == "already followed":
                    already_followed += 1

            else:
                self.logger.info('--> Not following')
                sleep(1)

            if liked_img < amount:
                self.logger.info('-------------')
                self.logger.info("--> Given amount not fullfilled, image pool "
                                 "reached its end\n")

        if len(usernames) > 1:
            # final words
            interacted_media_size = (len(usernames) * amount - inap_img)
            self.logger.info(
                "Finished interacting on total of {} "
                "images from {} users! xD\n"
                .format(interacted_media_size, len(usernames)))

            # print results
            self.logger.info('Liked: {}'.format(total_liked_img))
            self.logger.info('Already Liked: {}'.format(already_liked))
            self.logger.info('Commented: {}'.format(commented))
            self.logger.info('Followed: {}'.format(followed))
            self.logger.info('Already Followed: {}'.format(already_followed))
            self.logger.info('Inappropriate: {}'.format(inap_img))
            self.logger.info('Not valid users: {}\n'.format(not_valid_users))

        self.liked_img += total_liked_img
        self.already_liked += already_liked
        self.commented += commented
        self.followed += followed
        self.already_followed += already_followed
        self.inap_img += inap_img
        self.not_valid_users += not_valid_users

        return self

    def follow_user_followers(self,
                              usernames,
                              amount=10,
                              randomize=False,
                              interact=False,
                              sleep_delay=600):
        """ Follow the `Followers` of given users """
        if self.aborting:
            return self

        message = "Starting to follow user `Followers`.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        followed_all = 0
        followed_new = 0
        not_valid_users = 0

        # below, you can use some static value `10` instead of random ones..
        relax_point = random.randint(7, 14)

        # hold the current global values for differentiating at the end
        already_followed_init = self.already_followed
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        self.quotient_breach = False

        for index, user in enumerate(usernames):
            if self.quotient_breach:
                break

            self.logger.info(
                "User '{}' [{}/{}]".format((user), index + 1, len(usernames)))

            try:
                person_list, simulated_list = get_given_user_followers(
                    self.browser,
                    self.username,
                    self.userid,
                    user,
                    amount,
                    self.dont_include,
                    randomize,
                    self.blacklist,
                    self.follow_times,
                    self.simulation,
                    self.jumps,
                    self.logger,
                    self.logfolder)

            except (TypeError, RuntimeWarning) as err:
                if isinstance(err, RuntimeWarning):
                    self.logger.warning(
                        u'Warning: {} , skipping to next user'.format(err))
                    continue

                else:
                    self.logger.error(
                        'Sorry, an error occurred: {}'.format(err))
                    self.aborting = True
                    return self

            print('')
            self.logger.info(
                "Grabbed {} usernames from '{}'s `Followers` to do following\n"
                .format(len(person_list), user))

            followed_personal = 0
            simulated_unfollow = 0

            for index, person in enumerate(person_list):
                if self.quotient_breach:
                    self.logger.warning(
                        "--> Follow quotient reached its peak!"
                        "\t~leaving Follow-User-Followers activity\n")
                    break

                self.logger.info(
                    "Ongoing Follow [{}/{}]: now following '{}'..."
                    .format(index + 1, len(person_list), person))

                validation, details = self.validate_user_call(person)
                if validation is not True:
                    self.logger.info(details)
                    not_valid_users += 1

                    if person in simulated_list:
                        self.logger.warning(
                            "--> Simulated Unfollow {}: unfollowing"
                            " '{}' due to mismatching validation...\n"
                            .format(simulated_unfollow + 1, person))

                        unfollow_state, msg = unfollow_user(
                            self.browser,
                            "profile",
                            self.username,
                            person,
                            None,
                            None,
                            self.relationship_data,
                            self.logger,
                            self.logfolder)
                        if unfollow_state is True:
                            simulated_unfollow += 1
                    # skip this [non-validated] user
                    continue

                # go ahead and follow, then interact (if any)
                with self.feature_in_feature("follow_by_list", False):
                    followed = self.follow_by_list(person,
                                                   self.follow_times,
                                                   sleep_delay,
                                                   interact)
                sleep(1)

                if followed > 0:
                    followed_all += 1
                    followed_new += 1
                    followed_personal += 1

                self.logger.info("Follow per user: {}  |  Total Follow: {}\n"
                                 .format(followed_personal, followed_all))

                # take a break after a good following
                if followed_new >= relax_point:
                    delay_random = random.randint(
                        ceil(sleep_delay * 0.85),
                        ceil(sleep_delay * 1.14))
                    sleep_time = ("{} seconds".format(delay_random) if
                                  delay_random < 60 else
                                  "{} minutes".format(truncate_float(
                                      delay_random / 60, 2)))
                    self.logger.info(
                        "------=>  Followed {} new users ~sleeping about {}\n"
                        .format(followed_new, sleep_time))
                    sleep(delay_random)
                    relax_point = random.randint(7, 14)
                    followed_new = 0

        # final words
        self.logger.info("Finished following {} users' `Followers`! xD\n"
                         .format(len(usernames)))
        # find the feature-wide action sizes by taking a difference
        already_followed = (self.already_followed - already_followed_init)
        inap_img = (self.inap_img - inap_img_init)
        liked = (self.liked_img - liked_init)
        already_liked = (self.already_liked - already_liked_init)
        commented = (self.commented - commented_init)

        # print results
        self.logger.info("Followed: {}".format(followed_all))
        self.logger.info("Already followed: {}".format(already_followed))
        self.logger.info("Not valid users: {}".format(not_valid_users))

        if interact is True:
            print('')
            # print results out of interactions
            self.logger.info("Liked: {}".format(liked))
            self.logger.info("Already Liked: {}".format(already_liked))
            self.logger.info("Commented: {}".format(commented))
            self.logger.info("Inappropriate: {}".format(inap_img))

        self.not_valid_users += not_valid_users

        return self

    def end(self):
        """Closes the current session"""

        # IS_RUNNING = False
        close_browser(self.browser, False, self.logger)

        with interruption_handler():
            # close virtual display
            if self.nogui:
                self.display.stop()

            # write useful information
            dump_follow_restriction(self.username,
                                    self.logger,
                                    self.logfolder)

            with open('{}followed.txt'.format(self.logfolder), 'w') \
                    as followFile:
                followFile.write(str(self.followed))

            # output live stats before leaving
            self.live_report()

            message = "Session ended!"
            highlight_print(Settings, self.username, message, "end", "info", self.logger)
            print("\n\n")

    @contextmanager
    def feature_in_feature(self, feature, validate_users):
        """
         Use once a host feature calls a guest
        feature WHERE guest needs special behaviour(s)
        """

        try:
            # add the guest which is gonna be used by the host :)
            self.internal_usage[feature] = {"validate": validate_users}
            yield

        finally:
            # remove the guest just after using it
            self.internal_usage.pop(feature)

    def live_report(self):
        """ Report live sessional statistics """

        print('')

        stats = [self.liked_img, self.already_liked,
                 self.commented,
                 self.followed, self.already_followed,
                 self.unfollowed,
                 self.inap_img,
                 self.not_valid_users]

        if self.following_num and self.followed_by:
            owner_relationship_info = (
                "On session start was FOLLOWING {} users"
                " & had {} FOLLOWERS"
                .format(self.following_num,
                        self.followed_by))
        else:
            owner_relationship_info = ''

        sessional_run_time = self.run_time()
        run_time_info = ("{} seconds".format(sessional_run_time) if
                         sessional_run_time < 60 else
                         "{} minutes".format(truncate_float(
                             sessional_run_time / 60, 2)) if
                         sessional_run_time < 3600 else
                         "{} hours".format(truncate_float(
                             sessional_run_time / 60 / 60, 2)))
        run_time_msg = "[Session lasted {}]".format(run_time_info)

        if any(stat for stat in stats):
            self.logger.info(
                "Sessional Live Report:\n"
                "\t|> LIKED {} images  |  ALREADY LIKED: {}\n"
                "\t|> COMMENTED on {} images\n"
                "\t|> FOLLOWED {} users  |  ALREADY FOLLOWED: {}\n"
                "\t|> UNFOLLOWED {} users\n"
                "\t|> LIKED {} comments\n"
                "\t|> REPLIED to {} comments\n"
                "\t|> INAPPROPRIATE images: {}\n"
                "\t|> NOT VALID users: {}\n"
                "\n{}\n{}"
                .format(self.liked_img,
                        self.already_liked,
                        self.commented,
                        self.followed,
                        self.already_followed,
                        self.unfollowed,
                        self.liked_comments,
                        self.replied_to_comments,
                        self.inap_img,
                        self.not_valid_users,
                        owner_relationship_info,
                        run_time_msg))
        else:
            self.logger.info("Sessional Live Report:\n"
                             "\t|> No any statistics to show\n"
                             "\n{}\n{}"
                             .format(owner_relationship_info,
                                     run_time_msg))

    def is_mandatory_character(self, uchr):
        if self.aborting:
            return self
        try:
            return self.check_letters[uchr]
        except KeyError:
            return self.check_letters.setdefault(uchr,
                                                 self.mandatory_character in
                                                 unicodedata.name(uchr))

    def run_time(self):
        """ Get the time session lasted in seconds """

        real_time = time.time()
        run_time = (real_time - self.start_time)
        run_time = truncate_float(run_time, 2)

        return run_time

    def check_character_set(self, unistr):
        self.check_letters = {}
        if self.aborting:
            return self
        return all(self.is_mandatory_character(uchr)
                   for uchr in unistr
                   if uchr.isalpha())


@contextmanager
def smart_run(session):
    try:
        if session.login():
            yield
        else:
            print("Not proceeding as login failed")

    except (Exception, KeyboardInterrupt) as exc:
        if isinstance(exc, NoSuchElementException):
            # the problem is with a change in IG page layout
            log_file = "{}.html".format(time.strftime("%Y%m%d-%H%M%S"))
            file_path = os.path.join(gettempdir(), log_file)
            with open(file_path, "wb") as fp:
                fp.write(session.browser.page_source.encode("utf-8"))
            print("{0}\nIf raising an issue, "
                  "please also upload the file located at:\n{1}\n{0}"
                  .format('*' * 70, file_path))

        # provide full stacktrace (else than external interrupt)
        if isinstance(exc, KeyboardInterrupt):
            clean_exit("You have exited successfully.")
        else:
            raise

    finally:
        session.end()
