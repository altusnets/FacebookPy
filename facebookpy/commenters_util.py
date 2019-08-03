"""Methods to extract the data for the given usernames profile"""
# code created by modification of original code copied from
# https://github.com/timgrossmann/facebook-profilecrawl/blob/master/util
# /extractor.py
import time
from time import sleep
import random
from socialcommons.util import click_element
from socialcommons.util import update_activity
from socialcommons.util import web_address_navigator
from socialcommons.util import scroll_bottom
from socialcommons.util import get_users_from_dialog
from socialcommons.util import progress_tracker
from socialcommons.util import close_dialog_box
from .settings import Settings

from selenium.common.exceptions import NoSuchElementException


def users_liked(browser, post_url, logger, amount=100):
    post_likers = []
    try:
        web_address_navigator(browser, post_url, logger, Settings)
        post_likers = likers_from_post(browser, logger, amount)
        sleep(2)
    except NoSuchElementException:
        logger.info('Could not get information from post: {},  nothing to return'.format(post_url))
    return post_likers


def likers_from_post(browser, logger, Selectors, amount=20):
    """ Get the list of users from the 'Likes' dialog of a photo """

    liked_counter_button = \
        '//form/div/div/div/div/div/span/span/a[@role="button"]'

    try:
        liked_this = browser.find_elements_by_xpath(liked_counter_button)
        element_to_click = liked_this[0]

        sleep(1)
        click_element(browser, Settings, element_to_click)
        logger.info("opening likes")
        # update server calls
        # update_activity(Settings)

        sleep(1)

        # get a reference to the 'Likes' dialog box
        dialog = browser.find_element_by_xpath(
            Selectors.likes_dialog_body_xpath)

        # scroll down the page
        previous_len = -1
        browser.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", dialog)
        update_activity(Settings)
        sleep(1)

        start_time = time.time()
        user_list = []

        while (not user_list
               or (len(user_list) != previous_len)
               and (len(user_list) < amount)):

            previous_len = len(user_list)
            scroll_bottom(browser, dialog, 2)

            user_list = get_users_from_dialog(user_list, dialog, logger)

            # write & update records at Progress Tracker
            progress_tracker(len(user_list), amount, start_time, None)

            if previous_len + 10 >= amount:
                logger.info("Scrolling finished")
                sleep(1)
                break

        random.shuffle(user_list)
        sleep(1)

        close_dialog_box(browser)

        logger.info(
            "Got {} likers shuffled randomly whom you can follow:\n{}"
            "\n".format(
                len(user_list), user_list))
        return user_list

    except Exception as exc:
        logger.Error("Some problem occured!\n\t{}".format(str(exc).encode("utf-8")))
        return []


def get_post_urls_from_profile(browser, userid, logger, links_to_return_amount=1,
                               randomize=True):
    try:
        logger.info("Getting likers from user:  {}".format(userid))
        web_address_navigator(browser, 'https://www.facebook.com/' + userid + '/', logger, Settings)
        sleep(1)

        posts_a_elems = browser.find_elements_by_xpath(
            "//div/div/div/div/div/div/div/div/div/div/span/span/a")

        links = []
        for post_element in posts_a_elems:
            try:
                post_url = post_element.get_attribute("href")
                # TODO: "/posts/" doesnt cover all types
                # "/videos/", "/photos/" to be implemented later
                if "/posts/" in post_url:
                    links.append(post_url)
            except Exception as es:
                logger.error(es)

        if randomize is True:
            logger.info("shuffling links")
            random.shuffle(links)

        logger.info("Got {}, returning {} links: {}".format(
                    len(links), min(links_to_return_amount, len(links)), links[:links_to_return_amount]
                    ))
        sleep(1)
        return links[:links_to_return_amount]
    except Exception as e:
        logger.error("Error: Couldnt get pictures links.".format(e))
        return []
