import logging
import random
import time

import names
from celery import shared_task
from password_generator import PasswordGenerator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from apps.insta_users.models import InstaUser

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
            login = self.driver.find_element_by_xpath(
                '/html/body/div[1]/section/main/div/div/div[1]/div/form/div/div[3]/button')
            login.submit()

            # waiting for save login info dialog to shows up
            try:
                self.wait.until(EC.text_to_be_present_in_element(
                    (By.XPATH, '/html/body/div[1]/section/main/div/div/div/section/div/div[2]'),
                    'Save Your Login Info?'
                ))
            except:
                pass

            cookies = "; ".join([f"{_c['name']}={_c['value']}" for _c in self.driver.get_cookies()])

            try:
                self.driver.find_element_by_xpath("/html/body/div[1]/section/div[2]/div/p[2]/div/button/span").click()
            except:
                pass

        except Exception as e:
            logger.error(f'getting instagram session id for user {username} failed due to: {e}')

        # close and kill driver activities
        self.driver.quit()

        return cookies


@shared_task
def instagram_sign_up():
    try:
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0')

        insta_page = 'https://www.instagram.com/accounts/emailsignup/'
        temp_mail_page = 'https://email-fake.com/'

        driver_insta = webdriver.Firefox(firefox_profile=profile)
        driver_mail = webdriver.Firefox()
        driver_insta.get(insta_page)
        if driver_insta.find_element(By.CSS_SELECTOR, 'button.aOOlW.bIiDR'):
            driver_insta.find_element(By.CSS_SELECTOR, 'button.aOOlW.bIiDR').click()

        driver_mail.get(temp_mail_page)

        email_element = driver_mail.find_element_by_xpath('//*[@id="email_ch_text"]').text

        sign_up_email_elem = driver_insta.find_element(By.NAME, 'emailOrPhone')
        sign_up_email_elem.send_keys(email_element)

        sign_up_name_elem = driver_insta.find_element(By.NAME, 'fullName')
        full_name = names.get_full_name()
        sign_up_name_elem.send_keys(full_name)

        insta_wait = WebDriverWait(driver_insta, 10)
        insta_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.sqdOP.yWX7d.y3zKF')))
        user_auto_generate_elem = driver_insta.find_element(By.CSS_SELECTOR, 'button.sqdOP.yWX7d.y3zKF')
        user_auto_generate_elem.click()

        password_elem = driver_insta.find_element(By.NAME, 'password')
        pwo = PasswordGenerator()
        password = pwo.generate()
        password_elem.send_keys(password)

        sign_up_button_elem = driver_insta.find_elements(By.CSS_SELECTOR, 'button.sqdOP.L3NKy.y3zKF')
        sign_up_button_elem[-1].click()
        time.sleep(10)

        month_select = Select(driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select'))
        month_value = random.randint(1, 12)
        month_select.select_by_value(str(month_value))

        day_select = Select(driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select'))
        day_value = random.randint(1, 28)
        day_select.select_by_value(str(day_value))

        year_select = Select(driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select'))
        year_value = random.randint(1970, 2000)
        year_select.select_by_value(str(year_value))

        next_btn_elem = driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
        next_btn_elem.click()

        mail_wait = WebDriverWait(driver_mail, 300)
        mail_wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div/div/div[2]/div[2]/div[4]/div[3]/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[2]')))

        # refresh_btn = driver_mail.find_element_by_xpath('/html/body/div[2]/div/div[2]/table/tbody/tr[3]/td[1]/a/button')
        # refresh_btn.click()
        # time.sleep(5)

        confirmation_code_element = driver_mail.find_element_by_xpath('/html/body/div[3]/div/div/div/div[2]/div[2]/div[4]/div[3]/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[2]').text

        confirm_input = driver_insta.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div[1]/div[2]/form/div/div[1]/input')
        confirm_input.send_keys(confirmation_code_element)

        next_btn = driver_insta.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div[1]/div[2]/form/div/div[2]')
        next_btn.click()
        driver_insta.quit()
        driver_mail.quit()

        user_name = email_element.split('@')[0]

        InstaUser.objects.create(username=user_name, password=password)

    except Exception as e:
        logger.error(f'Instagram sign up failed -- error: {str(e)}')




