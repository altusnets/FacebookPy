""" Module which handles the follow features like unfollowing and following """
from datetime import datetime
import os
import random
import json
import sqlite3

from socialcommons.time_util import sleep
from socialcommons.util import delete_line_from_file
from socialcommons.util import update_activity
from socialcommons.util import add_user_to_blacklist
from socialcommons.util import click_element
from socialcommons.util import web_address_navigator
from socialcommons.util import get_relationship_counts
from socialcommons.util import emergency_exit
from socialcommons.util import load_user_id
from socialcommons.util import find_user_id
from socialcommons.util import explicit_wait
from socialcommons.util import get_username_from_id
from socialcommons.util import is_page_available
from socialcommons.util import reload_webpage
from socialcommons.util import click_visibly
from socialcommons.util import get_action_delay
from socialcommons.print_log_writer import log_followed_pool
from socialcommons.print_log_writer import log_uncertain_unfollowed_pool
from socialcommons.print_log_writer import log_record_all_unfollowed
from socialcommons.print_log_writer import get_log_time
from socialcommons.database_engine import get_database
from socialcommons.quota_supervisor import quota_supervisor
from .settings import Settings

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException


def get_following_status(browser, track, username, person, person_id, logger,
                         logfolder):
    """ Verify if you are following the user in the loaded page """
    if track == "profile":
        ig_homepage = "https://www.facebook.com/"
        web_address_navigator(browser, ig_homepage + person, logger, Settings)

    follow_button_XP = ("//div/div/a[@role='button'][text()='Follow']")
    failure_msg = "--> Unable to detect the following status of '{}'!"
    user_inaccessible_msg = (
        "Couldn't access the profile page of '{}'!\t~might have changed the"
        " username".format(person))

    # check if the page is available
    valid_page = is_page_available(browser, logger, Settings)
    if not valid_page:
        logger.warning(user_inaccessible_msg)
        person_new = verify_username_by_id(browser,
                                           username,
                                           person,
                                           None,
                                           logger,
                                           logfolder)
        if person_new:
            web_address_navigator(browser, ig_homepage + person_new, logger, Settings)
            valid_page = is_page_available(browser, logger, Settings)
            if not valid_page:
                logger.error(failure_msg.format(person_new.encode("utf-8")))
                return "UNAVAILABLE", None

        else:
            logger.error(failure_msg.format(person.encode("utf-8")))
            return "UNAVAILABLE", None

    # wait until the follow button is located and visible, then get it
    follow_button = explicit_wait(browser, "VOEL", [follow_button_XP, "XPath"],
                                  logger, 7, False)
    if not follow_button:
        browser.execute_script("location.reload()")
        update_activity(Settings)

        follow_button = explicit_wait(browser, "VOEL",
                                      [follow_button_XP, "XPath"], logger, 14,
                                      False)
        if not follow_button:
            # cannot find the any of the expected buttons
            logger.error(failure_msg.format(person.encode("utf-8")))
            return None, None

    # get follow status
    following_status = follow_button.text

    return following_status, follow_button


def follow_user(browser, track, login, userid_to_follow, button, blacklist,
                logger, logfolder, Settings):
    """ Follow a user either from the profile page or post page or dialog
    box """
    # list of available tracks to follow in: ["profile", "post" "dialog"]

    # check action availability
    if quota_supervisor(Settings, "follows") == "jump":
        return False, "jumped"

    if track in ["profile", "post"]:
        if track == "profile":
            # check URL of the webpage, if it already is user's profile
            # page, then do not navigate to it again
            user_link = "https://www.facebook.com/{}/".format(userid_to_follow)
            web_address_navigator(browser, user_link, logger, Settings)

        # find out CURRENT following status
        following_status, follow_button = \
            get_following_status(browser,
                                 track,
                                 login,
                                 userid_to_follow,
                                 None,
                                 logger,
                                 logfolder)
        if following_status in ["Follow", "Follow Back"]:
            click_visibly(browser, Settings, follow_button)  # click to follow
            follow_state, msg = verify_action(browser, "follow", track, login,
                                              userid_to_follow, None, logger,
                                              logfolder)
            if follow_state is not True:
                return False, msg

        elif following_status in ["Following", "Requested"]:
            if following_status == "Following":
                logger.info(
                    "--> Already following '{}'!\n".format(userid_to_follow))

            elif following_status == "Requested":
                logger.info("--> Already requested '{}' to follow!\n".format(
                    userid_to_follow))

            sleep(1)
            return False, "already followed"

        elif following_status in ["Unblock", "UNAVAILABLE"]:
            if following_status == "Unblock":
                failure_msg = "user is in block"

            elif following_status == "UNAVAILABLE":
                failure_msg = "user is inaccessible"

            logger.warning(
                "--> Couldn't follow '{}'!\t~{}".format(userid_to_follow,
                                                        failure_msg))
            return False, following_status

        elif following_status is None:
            # TODO:BUG:2nd login has to be fixed with userid of loggedin user
            sirens_wailing, emergency_state = emergency_exit(browser, Settings, "https://www.facebook.com", login,
                                                             login, logger, logfolder)
            if sirens_wailing is True:
                return False, emergency_state

            else:
                logger.warning(
                    "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
                        userid_to_follow))
                return False, "unexpected failure"
    elif track == "dialog":
        click_element(browser, Settings, button)
        sleep(3)

    # general tasks after a successful follow
    logger.info("--> Followed '{}'!".format(userid_to_follow.encode("utf-8")))
    update_activity(Settings, 'follows')

    # get user ID to record alongside username
    user_id = get_user_id(browser, track, userid_to_follow, logger)

    logtime = datetime.now().strftime('%Y-%m-%d %H:%M')
    log_followed_pool(login, userid_to_follow, logger,
                      logfolder, logtime, user_id)

    follow_restriction("write", userid_to_follow, None, logger)

    if blacklist['enabled'] is True:
        action = 'followed'
        add_user_to_blacklist(userid_to_follow,
                              blacklist['campaign'],
                              action,
                              logger,
                              logfolder)

    # get the post-follow delay time to sleep
    naply = get_action_delay("follow", Settings)
    sleep(naply)

    return True, "success"


def get_given_user_followers(browser,
                             login,
                             user_name,
                             userid,
                             amount,
                             dont_include,
                             randomize,
                             blacklist,
                             follow_times,
                             simulation,
                             jumps,
                             logger,
                             logfolder):
    """
    For the given username, follow their followers.

    :param browser: webdriver instance
    :param login:
    :param user_name: given username of account to follow
    :param amount: the number of followers to follow
    :param dont_include: ignore these usernames
    :param randomize: randomly select from users' followers
    :param blacklist:
    :param follow_times:
    :param logger: the logger instance
    :param logfolder: the logger folder
    :return: list of user's followers also followed
    """
    user_name = user_name.strip()

    user_link = "https://www.facebook.com/{}".format(userid)
    web_address_navigator(browser, user_link, logger, Settings)

    if not is_page_available(browser, logger, Settings):
        return [], []

    # check how many people are following this user.
    allfollowers, allfollowing = get_relationship_counts(browser, "https://www.facebook.com/", user_name,
                                                         userid, logger, Settings)

    # skip early for no followers
    if not allfollowers:
        logger.info("'{}' has no followers".format(user_name))
        return [], []

    elif allfollowers < amount:
        logger.warning(
            "'{}' has less followers- {}, than the given amount of {}".format(
                user_name, allfollowers, amount))

    # locate element to user's followers
    user_followers_link = "https://www.facebook.com/{}/followers".format(
        userid)
    web_address_navigator(browser, user_followers_link, logger, Settings)

    try:
        followers_links = browser.find_elements_by_xpath(
            '//div[2]/ul/li/div/div/div[2]/div/div[2]/div/a')
        followers_list = []
        for followers_link in followers_links:
            splitted = followers_link.get_attribute('href').replace(
                'https://www.facebook.com/', '').split('?')
            if splitted[0] == 'profile.php':
                u = splitted[0]+'?'+splitted[1]
            else:
                u = splitted[0]
            followers_list.append(u)
        logger.info(followers_list)

        # click_element(browser, Settings, followers_link[0])
        # # update server calls
        # update_activity(Settings)

    except NoSuchElementException:
        logger.error(
            'Could not find followers\' link for {}'.format(user_name))
        return [], []

    except BaseException as e:
        logger.error("`followers_link` error {}".format(str(e)))
        return [], []

    # channel = "Follow"

    # TODO: Fix it: Add simulated
    simulated_list = []
    if amount < len(followers_list):
        person_list = random.sample(followers_list, amount)
    else:
        person_list = followers_list

    return person_list, simulated_list


def dump_follow_restriction(profile_name, logger, logfolder):
    """ Dump follow restriction data to a local human-readable JSON """

    try:
        # get a DB and start a connection
        db, id = get_database(Settings)
        conn = sqlite3.connect(db)

        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute(
                "SELECT * FROM followRestriction WHERE profile_id=:var",
                {"var": id})
            data = cur.fetchall()

        if data:
            # get the existing data
            filename = "{}followRestriction.json".format(logfolder)
            if os.path.isfile(filename):
                with open(filename) as followResFile:
                    current_data = json.load(followResFile)
            else:
                current_data = {}

            # pack the new data
            follow_data = {user_data[1]: user_data[2] for user_data in
                           data or []}
            current_data[profile_name] = follow_data

            # dump the fresh follow data to a local human readable JSON
            with open(filename, 'w') as followResFile:
                json.dump(current_data, followResFile)

    except Exception as exc:
        logger.error(
            "Pow! Error occurred while dumping follow restriction data to a "
            "local JSON:\n\t{}".format(
                str(exc).encode("utf-8")))

    finally:
        if conn:
            # close the open connection
            conn.close()


def follow_restriction(operation, username, limit, logger):
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
                "SELECT * FROM followRestriction WHERE profile_id=:id_var "
                "AND username=:name_var",
                {"id_var": id, "name_var": username})
            data = cur.fetchone()
            follow_data = dict(data) if data else None

            if operation == "write":
                if follow_data is None:
                    # write a new record
                    cur.execute(
                        "INSERT INTO followRestriction (profile_id, "
                        "username, times) VALUES (?, ?, ?)",
                        (id, username, 1))
                else:
                    # update the existing record
                    follow_data["times"] += 1
                    sql = "UPDATE followRestriction set times = ? WHERE " \
                          "profile_id=? AND username = ?"
                    cur.execute(sql, (follow_data["times"], id, username))

                # commit the latest changes
                conn.commit()

            elif operation == "read":
                if follow_data is None:
                    return False

                elif follow_data["times"] < limit:
                    return False

                else:
                    exceed_msg = "" if follow_data[
                        "times"] == limit else "more than "
                    logger.info("---> {} has already been followed {}{} times"
                                .format(username, exceed_msg, str(limit)))
                    return True

    except Exception as exc:
        logger.error(
            "Dap! Error occurred with follow Restriction:\n\t{}".format(
                str(exc).encode("utf-8")))

    finally:
        if conn:
            conn.close()


def unfollow_user(browser, track, username, userid, person, person_id, button,
                  relationship_data, logger, logfolder, Settings):
    """ Unfollow a user either from the profile or post page or dialog box """
    # list of available tracks to unfollow in: ["profile", "post" "dialog"]

    # check action availability
    if quota_supervisor(Settings, "unfollows") == "jump":
        return False, "jumped"

    if track in ["profile", "post"]:
        """ Method of unfollowing from a user's profile page or post page """
        if track == "profile":
            user_link = "https://www.facebook.com/{}/".format(person)
            web_address_navigator(browser, user_link, logger, Settings)

        # find out CURRENT follow status
        following_status, follow_button = get_following_status(browser,
                                                               track,
                                                               username,
                                                               person,
                                                               person_id,
                                                               logger,
                                                               logfolder)

        if following_status in ["Following", "Requested"]:
            click_element(browser, Settings, follow_button)  # click to unfollow
            sleep(4)  # TODO: use explicit wait here
            confirm_unfollow(browser)
            unfollow_state, msg = verify_action(browser, "unfollow", track,
                                                username,
                                                person, person_id, logger,
                                                logfolder)
            if unfollow_state is not True:
                return False, msg

        elif following_status in ["Follow", "Follow Back"]:
            logger.info(
                "--> Already unfollowed '{}'! or a private user that "
                "rejected your req".format(
                    person))
            post_unfollow_cleanup(["successful", "uncertain"], username,
                                  person, relationship_data, person_id, logger,
                                  logfolder)
            return False, "already unfollowed"

        elif following_status in ["Unblock", "UNAVAILABLE"]:
            if following_status == "Unblock":
                failure_msg = "user is in block"

            elif following_status == "UNAVAILABLE":
                failure_msg = "user is inaccessible"

            logger.warning(
                "--> Couldn't unfollow '{}'!\t~{}".format(person, failure_msg))
            post_unfollow_cleanup("uncertain", username, person,
                                  relationship_data, person_id, logger,
                                  logfolder)
            return False, following_status

        elif following_status is None:
            sirens_wailing, emergency_state = emergency_exit(browser, Settings, username,
                                                             userid, logger, logfolder)
            if sirens_wailing is True:
                return False, emergency_state

            else:
                logger.warning(
                    "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
                        person))
                return False, "unexpected failure"
    elif track == "dialog":
        """  Method of unfollowing from a dialog box """
        click_element(browser, Settings, button)
        sleep(4)  # TODO: use explicit wait here
        confirm_unfollow(browser)

    # general tasks after a successful unfollow
    logger.info("--> Unfollowed '{}'!".format(person))
    update_activity(Settings, 'unfollows')
    post_unfollow_cleanup("successful", username, person, relationship_data,
                          person_id, logger, logfolder)

    # get the post-unfollow delay time to sleep
    naply = get_action_delay("unfollow", Settings)
    sleep(naply)

    return True, "success"


def confirm_unfollow(browser):
    """ Deal with the confirmation dialog boxes during an unfollow """
    attempt = 0

    while attempt < 3:
        try:
            attempt += 1
            button_xp = "//button[text()='Unfollow']"  # "//button[contains(
            # text(), 'Unfollow')]"
            unfollow_button = browser.find_element_by_xpath(button_xp)

            if unfollow_button.is_displayed():
                click_element(browser, Settings, unfollow_button)
                sleep(2)
                break

        except (ElementNotVisibleException, NoSuchElementException) as exc:
            # prob confirm dialog didn't pop up
            if isinstance(exc, ElementNotVisibleException):
                break

            elif isinstance(exc, NoSuchElementException):
                sleep(1)


def post_unfollow_cleanup(state, username, person, relationship_data,
                          person_id, logger, logfolder):
    """ Casual local data cleaning after an unfollow """
    if not isinstance(state, list):
        state = [state]

    delete_line_from_file("{0}{1}_followedPool.csv"
                          .format(logfolder, username), person, logger)

    if "successful" in state:
        if person in relationship_data[username]["all_following"]:
            relationship_data[username]["all_following"].remove(person)

    if "uncertain" in state:
        # this user was found in our unfollow list but currently is not
        # being followed
        logtime = get_log_time()
        log_uncertain_unfollowed_pool(username, person, logger, logfolder,
                                      logtime, person_id)
        # take a generic 3 seconds of sleep per each uncertain unfollow
        sleep(3)

    # save any unfollowed person
    log_record_all_unfollowed(username, person, logger, logfolder)


def get_user_id(browser, track, username, logger):
    """ Get user's ID either from a profile page or post page """
    user_id = "unknown"

    if track != "dialog":  # currently do not get the user ID for follows
        # from 'dialog'
        user_id = find_user_id(Settings, browser, track, username, logger)

    return user_id


def verify_username_by_id(browser, username, person, person_id, logger,
                          logfolder):
    """ Check if the given user has changed username after the time of
    followed """
    # try to find the user by ID
    if person_id is None:
        person_id = load_user_id(username, person, logger, logfolder)

    if person_id and person_id not in [None, "unknown", "undefined"]:
        # get the [new] username of the user from the stored user ID
        person_new = get_username_from_id(browser, "https://www.facebook.com", person_id, logger)
        if person_new:
            if person_new != person:
                logger.info(
                    "User '{}' has changed username and now is called '{}' :S"
                    .format(person, person_new))
            return person_new

        else:
            logger.info(
                "The user with the ID of '{}' is unreachable".format(person))

    else:
        logger.info(
            "The user ID of '{}' doesn't exist in local records".format(
                person))

    return None


def verify_action(browser, action, track, username, person, person_id, logger,
                  logfolder):
    """ Verify if the action has succeeded """
    # currently supported actions are follow & unfollow

    if action in ["follow", "unfollow"]:
        if action == "follow":
            post_action_text = "//button[text()='Following' or text(" \
                               ")='Requested']"

        elif action == "unfollow":
            post_action_text = "//button[text()='Follow' or text()='Follow " \
                               "Back']"

        button_change = explicit_wait(browser, "VOEL",
                                      [post_action_text, "XPath"], logger, 7,
                                      False)
        if not button_change:
            reload_webpage(browser, Settings)
            following_status, follow_button = get_following_status(browser,
                                                                   track,
                                                                   username,
                                                                   person,
                                                                   person_id,
                                                                   logger,
                                                                   logfolder)
            # find action state *.^
            if following_status in ["Following", "Requested"]:
                action_state = False if action == "unfollow" else True

            elif following_status in ["Follow", "Follow Back"]:
                action_state = True if action == "unfollow" else False

            else:
                action_state = None

            # handle it!
            if action_state is True:
                logger.info(
                    "Last {} is verified after reloading the page!".format(
                        action))

            elif action_state is False:
                # try to do the action one more time!
                click_visibly(browser, Settings, follow_button)

                if action == "unfollow":
                    sleep(4)  # TODO: use explicit wait here
                    confirm_unfollow(browser)

                button_change = explicit_wait(browser, "VOEL",
                                              [post_action_text, "XPath"],
                                              logger, 9, False)
                if not button_change:
                    logger.warning("Phew! Last {0} is not verified."
                                   "\t~'{1}' might be temporarily blocked "
                                   "from {0}ing\n"
                                   .format(action, username))
                    sleep(210)
                    return False, "temporary block"

            elif action_state is None:
                logger.error(
                    "Hey! Last {} is not verified out of an unexpected "
                    "failure!".format(action))
                return False, "unexpected"

    return True, "success"
