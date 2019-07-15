""" Quickstart script for FacebookPy usage """

# imports
from facebookpy import FacebookPy
from facebookpy import smart_run
from socialcommons.file_manager import set_workspace
from facebookpy import settings

# set workspace folder at desired location (default is at your home folder)
set_workspace(settings.Settings, path=None)

# get an FacebookPy session!
session = FacebookPy(use_firefox=True)

with smart_run(session):
    """ Activity flow """
    # general settings
    session.set_dont_include(["friend1", "friend2", "friend3"])

    # activity
    # session.like_by_tags(["natgeo"], amount=10)

    session.set_relationship_bounds(enabled=True,
                                    potency_ratio=None,
                                    delimit_by_numbers=True,
                                    max_followers=7500,
                                    max_following=3000,
                                    min_followers=25,
                                    min_following=25,
                                    min_posts=1)

    session.set_user_interact(amount=3, randomize=True, percentage=80,
                              media='Photo')
    # session.set_do_like(enabled=True, percentage=90)
    session.set_do_follow(enabled=True, percentage=40, times=1)

    """ Select users form a list of a predefined targets...
    """

    # targets = ['ananya.mallik', 'Sushant.on', 'trina.roy.94064', 'supondev.nath']
    # number = random.randint(3, 5)
    # random_targets = targets

    # if len(targets) <= number:
    #     random_targets = targets
    # else:
    #     random_targets = random.sample(targets, number)

    # session.follow_by_list(followlist=random_targets, times=1, sleep_delay=600, interact=False)
    # session.friend_by_list(friendlist=random_targets, times=1, sleep_delay=600, interact=False)

    # session.follow_user_followers(random_targets,
    #                               amount=random.randint(30, 60),
    #                               randomize=True, sleep_delay=600,
    #                               interact=True)

    # session.follow_likers(random_targets, photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=False)
    # session.fetch_birthdays()
    # session.confirm_friends()
    # session.add_suggested_friends()
    session.add_likers_of_page(page_likers_url = "https://www.facebook.com/search/101771478880/likers?f=AbqfdHqQ9CNUi3xZPT6BlmnyGrDaZjR95UkZkJMjMQIlPUvwblytgVaUg69FjTdlHnRayhaftiKR9pPMZ5tkczTQbHbWWq-2nOCQ-qvVMC8IOw")
    session.add_likers_of_page(page_likers_url = "https://www.facebook.com/search/396185197414302/likers?f=Abr2VwU_kVVCXkwXPkbFfo5QA6ox7BqvKuYrW4-7EWS0b5Y61Y6gq3sCsC8zpAnZ1cxTfYD2IN38YJNRx5WY0lwG0tpwSLkhefV1l2_DnnKZVA")
    session.add_likers_of_page(page_likers_url = "https://www.facebook.com/search/1600562606933560/likers?f=AbpMXTubybrIpSgniVJL1ec2qzhJSC7nQcNm1hASbLwweGWRhGd1Kf7iTZ6eLkeBaQ25mzzuBAtRVHEzCFJFa6mNHlYErYW1Cq60kwSLCRrDag")
    session.add_likers_of_page(page_likers_url = "https://www.facebook.com/search/1294302220678964/likers?f=AbrmGJINmsaOpOTe2Bu8Hys68kZpJ_S5IWSiw7s5kMQ7K0qAzUAVLFZV7IieErNlc34bADViG3KFbs6KMTGcYqCWg1MnF6X1nkWG1uEiLxDzDA")
    session.add_likers_of_page(page_likers_url = "https://www.facebook.com/search/1164458926994976/likers?f=AboHFE1rZyA9tE6ykLZBMTtDtpiFvMuhEjcuZDkOYD-GtaUI_PuMgr9yuAR7yFLU4hByI0vp_2W8GqBY1LtkDlGc73nIhzUjCNVbChBxyf8uPw&ref=snippets")

