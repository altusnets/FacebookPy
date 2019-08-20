"""
Global variables

By design, import no any other local module inside this file.
Vice verse, it'd produce circular dependent imports.
"""


class Selectors:
    """
    Store XPath, CSS, and other element selectors to be used at many places
    """

    likes_dialog_body_xpath = '//*[@id="facebook"]/body/div[10]/div[2][@role="dialog"]'
