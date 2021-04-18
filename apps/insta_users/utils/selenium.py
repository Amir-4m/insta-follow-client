import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger(__name__)


class SeleniumService(object):

    def __init__(self, user_agent):
        self.profile = webdriver.FirefoxProfile()
        self.profile.set_preference("general.useragent.override", user_agent)
        self.driver = webdriver.Firefox(firefox_profile=self.profile)
        self.login_url = 'https://www.instagram.com/accounts/login/'
        self.wait = WebDriverWait(self.driver, 10)

    def get_instagram_session_id(self, username, password):
        cookies = ''

        try:
            self.driver.get(self.login_url)
            # self.wait.until(EC.text_to_be_present_in_element(
            #     (By.XPATH, '/html/body/div[2]/div/div/div/div[1]/h3/div[1]/h2'),
            #     'Accept cookies from Instagram on this browser?'
            # ))

            # accepting cookies
            # accept = self.driver.find_element_by_class_name('bIiDR')
            # accept.click()

            self.wait.until(EC.presence_of_element_located(
                (By.NAME, 'username'),
            ))

            # filling login form
            self.driver.find_element_by_name('username').send_keys(username)
            self.driver.find_element_by_name('password').send_keys(password)
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[1]/section/main/div/div/div[1]/div/form/div/div[3]/button'),
            ))

            # submitting login form
            login = self.driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div[1]/div/form/div/div[3]/button')
            login.submit()

            # waiting for save login info dialog to shows up
            self.wait.until(EC.text_to_be_present_in_element(
                (By.XPATH, '/html/body/div[1]/section/main/div/div/div/section/div/div[2]'),
                'Save Your Login Info?'
            ))
            # decline saving login info
            self.driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div/div/button').click()

            # convert cookies from json to browser format
            cookies = "; ".join([f"{_c['name']}={_c['value']}" for _c in self.driver.get_cookies()])

        except Exception as e:
            logger.error(f'getting instagram session id for user {username} failed due to: {e}')

        # close and kill driver activities
        self.driver.quit()

        return cookies
