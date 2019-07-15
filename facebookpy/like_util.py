""" Module that handles the like features """
import random
import re

from socialcommons.time_util import sleep
from socialcommons.util import format_number
from socialcommons.util import add_user_to_blacklist
from socialcommons.util import click_element
from socialcommons.util import is_private_profile
from socialcommons.util import update_activity
from socialcommons.util import web_address_navigator
from socialcommons.util import get_number_of_posts
from socialcommons.util import get_action_delay
from socialcommons.quota_supervisor import quota_supervisor
from .unfollow_util  import get_following_status
from .settings import Settings

from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException

def get_links_for_username(browser,
                           username,
                           person,
                           amount,
                           logger,
                           logfolder,
                           randomize=False,
                           media=None,
                           taggedImages=False):
    """Fetches the number of links specified
    by amount and returns a list of links"""
    if media is None:
        # All known media types
        media = ['', 'Post', 'Video']
    elif media == 'Photo':
        # Include posts with multiple images in it
        media = ['', 'Post']
    else:
        # Make it an array to use it in the following part
        media = [media]

    logger.info('Getting {} image list...'.format(person))

    user_link = "https://www.facebook.com/{}/".format(person)
    if taggedImages:
        user_link = user_link + 'tagged/'

    # Check URL of the webpage, if it already is user's profile page,
    # then do not navigate to it again
    web_address_navigator( browser, user_link, Settings)

    if "Page Not Found" in browser.title:
        logger.error(
            'Facebook error: The link you followed may be broken, or the '
            'page may have been removed...')
        return False

    # if private user, we can get links only if we following
    following, follow_button = get_following_status(browser, 'profile',
                                                    username, person, None,
                                                    logger, logfolder)
    if following == 'Following':
        following = True
    is_private = is_private_profile(Settings, browser, logger, following)
    if (is_private is None) or (is_private is True and not following) or (
            following == 'Blocked'):
        return False

    # Get links
    links = []
    main_elem = browser.find_element_by_tag_name('article')
    posts_count = get_number_of_posts(browser)
    attempt = 0

    if posts_count is not None and amount > posts_count:
        logger.info(
            "You have requested to get {} posts from {}'s profile page BUT"
            " there only {} posts available :D".format(amount, person,
                                                       posts_count))
        amount = posts_count

    while len(links) < amount:
        initial_links = links
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        # update server calls after a scroll request
        update_activity(Settings)
        sleep(0.66)

        # using `extend`  or `+=` results reference stay alive which affects
        # previous assignment (can use `copy()` for it)
        links = links + get_links(browser, person, logger, media, main_elem)
        links = sorted(set(links), key=links.index)

        if len(links) == len(initial_links):
            if attempt >= 7:
                logger.info(
                    "There are possibly less posts than {} in {}'s profile "
                    "page!".format(
                        amount, person))
                break
            else:
                attempt += 1
        else:
            attempt = 0

    if randomize is True:
        random.shuffle(links)

    return links[:amount]


def get_media_edge_comment_string(media):
    """
    AB test (Issue 3712) alters the string for media edge, this resoves it
    """
    options = ['edge_media_to_comment', 'edge_media_preview_comment']
    for option in options:
        try:
            media[option]
        except KeyError:
            continue
        return option


def check_link(browser, post_link, dont_like, mandatory_words,
               mandatory_language, mandatory_character,
               is_mandatory_character, check_character_set, ignore_if_contains,
               logger):
    """
    Check the given link if it is appropriate

    :param browser: The selenium webdriver instance
    :param post_link:
    :param dont_like: hashtags of inappropriate phrases
    :param mandatory_words: words of appropriate phrases
    :param ignore_if_contains:
    :param logger: the logger instance
    :return: tuple of
        boolean: True if inappropriate,
        string: the username,
        boolean: True if it is video media,
        string: the message if inappropriate else 'None',
        string: set the scope of the return value
    """

    # Check URL of the webpage, if it already is post's page, then do not
    # navigate to it again
    web_address_navigator( browser, post_link, Settings)

    """Check if the Post is Valid/Exists"""
    try:
        post_page = browser.execute_script(
            "return window._sharedData.entry_data.PostPage")

    except WebDriverException:  # handle the possible `entry_data` error
        try:
            browser.execute_script("location.reload()")
            update_activity(Settings)

            post_page = browser.execute_script(
                "return window._sharedData.entry_data.PostPage")

        except WebDriverException:
            post_page = None

    if post_page is None:
        logger.warning(
            'Unavailable Page: {}'.format(post_link.encode('utf-8')))
        return True, None, None, 'Unavailable Page', "Failure"

    """Gets the description of the post's link and checks for the dont_like
    tags"""
    graphql = 'graphql' in post_page[0]
    if graphql:
        media = post_page[0]['graphql']['shortcode_media']
        is_video = media['is_video']
        user_name = media['owner']['username']
        image_text = media['edge_media_to_caption']['edges']
        image_text = image_text[0]['node']['text'] if image_text else None
        location = media['location']
        location_name = location['name'] if location else None
        media_edge_string = get_media_edge_comment_string(media)
        # double {{ allows us to call .format here:
        owner_comments = browser.execute_script('''
            latest_comments = window._sharedData.entry_data.PostPage[
            0].graphql.shortcode_media.{}.edges;
            if (latest_comments === undefined) {{
                latest_comments = Array();
                owner_comments = latest_comments
                    .filter(item => item.node.owner.username == arguments[0])
                    .map(item => item.node.text)
                    .reduce((item, total) => item + '\\n' + total, '');
                return owner_comments;}}
            else {{
                return null;}}
        '''.format(media_edge_string), user_name)

    else:
        media = post_page[0]['media']
        is_video = media['is_video']
        user_name = media['owner']['username']
        image_text = media['caption']
        owner_comments = browser.execute_script('''
            latest_comments = window._sharedData.entry_data.PostPage[
            0].media.comments.nodes;
            if (latest_comments === undefined) {
                latest_comments = Array();
                owner_comments = latest_comments
                    .filter(item => item.user.username == arguments[0])
                    .map(item => item.text)
                    .reduce((item, total) => item + '\\n' + total, '');
                return owner_comments;}
            else {
                return null;}
        ''', user_name)

    if owner_comments == '':
        owner_comments = None

    """Append owner comments to description as it might contain further tags"""
    if image_text is None:
        image_text = owner_comments

    elif owner_comments:
        image_text = image_text + '\n' + owner_comments

    """If the image still has no description gets the first comment"""
    if image_text is None:
        if graphql:
            media_edge_string = get_media_edge_comment_string(media)
            image_text = media[media_edge_string]['edges']
            image_text = image_text[0]['node']['text'] if image_text else None

        else:
            image_text = media['comments']['nodes']
            image_text = image_text[0]['text'] if image_text else None

    if image_text is None:
        image_text = "No description"

    logger.info('Image from: {}'.format(user_name.encode('utf-8')))
    logger.info('Link: {}'.format(post_link.encode('utf-8')))
    logger.info('Description: {}'.format(image_text.encode('utf-8')))

    """Check if mandatory character set, before adding the location to the
    text"""
    if mandatory_language:
        if not check_character_set(image_text):
            return True, user_name, is_video, 'Mandatory language not ' \
                                              'fulfilled', "Not mandatory " \
                                                           "language"

    """Append location to image_text so we can search through both in one
    go."""
    if location_name:
        logger.info('Location: {}'.format(location_name.encode('utf-8')))
        image_text = image_text + '\n' + location_name

    if mandatory_words:
        if not any((word in image_text for word in mandatory_words)):
            return True, user_name, is_video, 'Mandatory words not ' \
                                              'fulfilled', "Not mandatory " \
                                                           "likes"

    image_text_lower = [x.lower() for x in image_text]
    ignore_if_contains_lower = [x.lower() for x in ignore_if_contains]
    if any((word in image_text_lower for word in ignore_if_contains_lower)):
        return False, user_name, is_video, 'None', "Pass"

    dont_like_regex = []

    for dont_likes in dont_like:
        if dont_likes.startswith("#"):
            dont_like_regex.append(dont_likes + "([^\d\w]|$)")
        elif dont_likes.startswith("["):
            dont_like_regex.append("#" + dont_likes[1:] + "[\d\w]+([^\d\w]|$)")
        elif dont_likes.startswith("]"):
            dont_like_regex.append("#[\d\w]+" + dont_likes[1:] + "([^\d\w]|$)")
        else:
            dont_like_regex.append(
                "#[\d\w]*" + dont_likes + "[\d\w]*([^\d\w]|$)")

    for dont_likes_regex in dont_like_regex:
        quash = re.search(dont_likes_regex, image_text, re.IGNORECASE)
        if quash:
            quashed = \
                (((quash.group(0)).split('#')[1]).split(' ')[0]).split('\n')[
                    0].encode(
                    'utf-8')  # dismiss possible space and newlines
            iffy = ((re.split(r'\W+', dont_likes_regex))[
                3] if dont_likes_regex.endswith(
                '*([^\\d\\w]|$)') else  # 'word' without format
                (re.split(r'\W+', dont_likes_regex))[
                1] if dont_likes_regex.endswith(
                '+([^\\d\\w]|$)') else  # '[word'
                (re.split(r'\W+', dont_likes_regex))[
                3] if dont_likes_regex.startswith(
                '#[\\d\\w]+') else  # ']word'
                (re.split(r'\W+', dont_likes_regex))[1])  # '#word'
            inapp_unit = 'Inappropriate! ~ contains "{}"'.format(
                quashed if iffy == quashed else
                '" in "'.join([str(iffy), str(quashed)]))
            return True, user_name, is_video, inapp_unit, "Undesired word"

    return False, user_name, is_video, 'None', "Success"


def like_image(browser, username, blacklist, logger, logfolder, Settings):
    """Likes the browser opened image"""
    # check action availability
    if quota_supervisor(Settings, "likes") == "jump":
        return False, "jumped"

    like_xpath = "//section/span/button/span[@aria-label='Like']"
    unlike_xpath = "//section/span/button/span[@aria-label='Unlike']"

    # find first for like element
    like_elem = browser.find_elements_by_xpath(like_xpath)

    if len(like_elem) == 1:
        # sleep real quick right before clicking the element
        sleep(2)
        click_element(browser, Settings, like_elem[0])
        # check now we have unlike instead of like
        liked_elem = browser.find_elements_by_xpath(unlike_xpath)

        if len(liked_elem) == 1:
            logger.info('--> Image Liked!')
            update_activity(Settings, 'likes')

            if blacklist['enabled'] is True:
                action = 'liked'
                add_user_to_blacklist(
                    username, blacklist['campaign'], action, logger, logfolder)

            # get the post-like delay time to sleep
            naply = get_action_delay("like", Settings)
            sleep(naply)
            return True, "success"

        else:
            # if like not seceded wait for 2 min
            logger.info('--> Image was not able to get Liked! maybe blocked ?')
            sleep(120)

    else:
        liked_elem = browser.find_elements_by_xpath(unlike_xpath)
        if len(liked_elem) == 1:
            logger.info('--> Image already liked!')
            return False, "already liked"

    logger.info('--> Invalid Like Element!')

    return False, "invalid element"

def get_links(browser, page, logger, media, element):
    # Get image links in scope from hashtag, location and other pages
    link_elems = element.find_elements_by_tag_name('a')
    sleep(2)
    links = []
    try:
        if link_elems:
            new_links = [link_elem.get_attribute('href') for link_elem in
                         link_elems
                         if link_elem and link_elem.text in media]
            links.extend(new_links)
        else:
            logger.info("'{}' page does not contain a picture".format(page))
    except BaseException as e:
        logger.error("link_elems error {}".format(str(e)))
    return links


def verify_liking(browser, max, min, logger):
    """ Get the amount of existing existing likes and compare it against max
    & min values defined by user """
    try:
        likes_count = browser.execute_script(
            "return window._sharedData.entry_data."
            "PostPage[0].graphql.shortcode_media.edge_media_preview_like"
            ".count")

    except WebDriverException:
        try:
            browser.execute_script("location.reload()")
            update_activity(Settings)

            likes_count = browser.execute_script(
                "return window._sharedData.entry_data."
                "PostPage[0].graphql.shortcode_media.edge_media_preview_like"
                ".count")

        except WebDriverException:
            try:
                likes_count = (browser.find_element_by_css_selector(
                    "section._1w76c._nlmjy > div > a > span").text)

                if likes_count:
                    likes_count = format_number(likes_count)
                else:
                    logger.info(
                        "Failed to check likes' count  ~empty string\n")
                    return True

            except NoSuchElementException:
                logger.info("Failed to check likes' count\n")
                return True

    if max is not None and likes_count > max:
        logger.info(
            "Not liked this post! ~more likes exist off maximum limit at "
            "{}".format(likes_count))
        return False
    elif min is not None and likes_count < min:
        logger.info(
            "Not liked this post! ~less likes exist off minumum limit "
            "at {}".format(likes_count)
        )
        return False

    return True

