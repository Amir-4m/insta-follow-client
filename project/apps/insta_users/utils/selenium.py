import logging
import random
import time
from base64 import b64encode

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
    proxies = ['209.205.212.36:10000', '209.205.212.36:10001', '209.205.212.36:10002', '209.205.212.36:10003', '209.205.212.36:10004',
               '209.205.212.36:10005', '209.205.212.36:10006', '209.205.212.36:10007', '209.205.212.36:10008', '209.205.212.36:10009',
               '209.205.212.36:10010', '209.205.212.36:10011', '209.205.212.36:10012', '209.205.212.36:10013', '209.205.212.36:10014',
               '209.205.212.36:10015', '209.205.212.36:10016', '209.205.212.36:10017', '209.205.212.36:10018', '209.205.212.36:10019',
               '209.205.212.36:10020', '209.205.212.36:10021', '209.205.212.36:10022', '209.205.212.36:10023', '209.205.212.36:10024',
               '209.205.212.36:10025', '209.205.212.36:10026', '209.205.212.36:10027', '209.205.212.36:10028', '209.205.212.36:10029',
               '209.205.212.36:10030', '209.205.212.36:10031', '209.205.212.36:10032', '209.205.212.36:10033', '209.205.212.36:10034',
               '209.205.212.36:10035', '209.205.212.36:10036', '209.205.212.36:10037', '209.205.212.36:10038', '209.205.212.36:10039',
               '209.205.212.36:10040', '209.205.212.36:10041', '209.205.212.36:10042', '209.205.212.36:10043', '209.205.212.36:10044',
               '209.205.212.36:10045', '209.205.212.36:10046', '209.205.212.36:10047', '209.205.212.36:10048', '209.205.212.36:10049',
               '209.205.212.36:10050', '209.205.212.36:10051', '209.205.212.36:10052', '209.205.212.36:10053', '209.205.212.36:10054',
               '209.205.212.36:10055', '209.205.212.36:10056', '209.205.212.36:10057', '209.205.212.36:10058', '209.205.212.36:10059',
               '209.205.212.36:10060', '209.205.212.36:10061', '209.205.212.36:10062', '209.205.212.36:10063', '209.205.212.36:10064',
               '209.205.212.36:10065', '209.205.212.36:10066', '209.205.212.36:10067', '209.205.212.36:10068', '209.205.212.36:10069',
               '209.205.212.36:10070', '209.205.212.36:10071', '209.205.212.36:10072', '209.205.212.36:10073', '209.205.212.36:10074',
               '209.205.212.36:10075', '209.205.212.36:10076', '209.205.212.36:10077', '209.205.212.36:10078', '209.205.212.36:10079',
               '209.205.212.36:10080', '209.205.212.36:10081', '209.205.212.36:10082', '209.205.212.36:10083', '209.205.212.36:10084',
               '209.205.212.36:10085', '209.205.212.36:10086', '209.205.212.36:10087', '209.205.212.36:10088', '209.205.212.36:10089',
               '209.205.212.36:10090', '209.205.212.36:10091', '209.205.212.36:10092', '209.205.212.36:10093', '209.205.212.36:10094',
               '209.205.212.36:10095', '209.205.212.36:10096', '209.205.212.36:10097', '209.205.212.36:10098', '209.205.212.36:10099',
               '209.205.212.36:10100', '209.205.212.36:10101', '209.205.212.36:10102', '209.205.212.36:10103', '209.205.212.36:10104',
               '209.205.212.36:10105', '209.205.212.36:10106', '209.205.212.36:10107', '209.205.212.36:10108', '209.205.212.36:10109',
               '209.205.212.36:10110', '209.205.212.36:10111', '209.205.212.36:10112', '209.205.212.36:10113', '209.205.212.36:10114',
               '209.205.212.36:10115', '209.205.212.36:10116', '209.205.212.36:10117', '209.205.212.36:10118', '209.205.212.36:10119',
               '209.205.212.36:10120', '209.205.212.36:10121', '209.205.212.36:10122', '209.205.212.36:10123', '209.205.212.36:10124',
               '209.205.212.36:10125', '209.205.212.36:10126', '209.205.212.36:10127', '209.205.212.36:10128', '209.205.212.36:10129',
               '209.205.212.36:10130', '209.205.212.36:10131', '209.205.212.36:10132', '209.205.212.36:10133', '209.205.212.36:10134',
               '209.205.212.36:10135', '209.205.212.36:10136', '209.205.212.36:10137', '209.205.212.36:10138', '209.205.212.36:10139',
               '209.205.212.36:10140', '209.205.212.36:10141', '209.205.212.36:10142', '209.205.212.36:10143', '209.205.212.36:10144',
               '209.205.212.36:10145', '209.205.212.36:10146', '209.205.212.36:10147', '209.205.212.36:10148', '209.205.212.36:10149',
               '209.205.212.36:10150', '209.205.212.36:10151', '209.205.212.36:10152', '209.205.212.36:10153', '209.205.212.36:10154',
               '209.205.212.36:10155', '209.205.212.36:10156', '209.205.212.36:10157', '209.205.212.36:10158', '209.205.212.36:10159',
               '209.205.212.36:10160', '209.205.212.36:10161', '209.205.212.36:10162', '209.205.212.36:10163', '209.205.212.36:10164',
               '209.205.212.36:10165', '209.205.212.36:10166', '209.205.212.36:10167', '209.205.212.36:10168', '209.205.212.36:10169',
               '209.205.212.36:10170', '209.205.212.36:10171', '209.205.212.36:10172', '209.205.212.36:10173', '209.205.212.36:10174',
               '209.205.212.36:10175', '209.205.212.36:10176', '209.205.212.36:10177', '209.205.212.36:10178', '209.205.212.36:10179',
               '209.205.212.36:10180', '209.205.212.36:10181', '209.205.212.36:10182', '209.205.212.36:10183', '209.205.212.36:10184',
               '209.205.212.36:10185', '209.205.212.36:10186', '209.205.212.36:10187', '209.205.212.36:10188', '209.205.212.36:10189',
               '209.205.212.36:10190', '209.205.212.36:10191', '209.205.212.36:10192', '209.205.212.36:10193', '209.205.212.36:10194',
               '209.205.212.36:10195', '209.205.212.36:10196', '209.205.212.36:10197', '209.205.212.36:10198', '209.205.212.36:10199',
               '209.205.212.36:10200', '209.205.212.36:10201', '209.205.212.36:10202', '209.205.212.36:10203', '209.205.212.36:10204',
               '209.205.212.36:10205', '209.205.212.36:10206', '209.205.212.36:10207', '209.205.212.36:10208', '209.205.212.36:10209',
               '209.205.212.36:10210', '209.205.212.36:10211', '209.205.212.36:10212', '209.205.212.36:10213', '209.205.212.36:10214',
               '209.205.212.36:10215', '209.205.212.36:10216', '209.205.212.36:10217', '209.205.212.36:10218', '209.205.212.36:10219',
               '209.205.212.36:10220', '209.205.212.36:10221', '209.205.212.36:10222', '209.205.212.36:10223', '209.205.212.36:10224',
               '209.205.212.36:10225', '209.205.212.36:10226', '209.205.212.36:10227', '209.205.212.36:10228', '209.205.212.36:10229',
               '209.205.212.36:10230', '209.205.212.36:10231', '209.205.212.36:10232', '209.205.212.36:10233', '209.205.212.36:10234',
               '209.205.212.36:10235', '209.205.212.36:10236', '209.205.212.36:10237', '209.205.212.36:10238', '209.205.212.36:10239',
               '209.205.212.36:10240', '209.205.212.36:10241', '209.205.212.36:10242', '209.205.212.36:10243', '209.205.212.36:10244',
               '209.205.212.36:10245', '209.205.212.36:10246', '209.205.212.36:10247', '209.205.212.36:10248', '209.205.212.36:10249']
    random_proxy = proxies[random.randint(0, len(proxies) - 1)].split(":")
    print(random_proxy)
    logger.info("Instagram Signing Up has been Started")
    # proxy = "http://rezahavaei:be9916-31138d-ed44f7-e8ed13-c5f21e@usa.rotating.proxyrack.net:333"
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override",
                           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36')
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.http", random_proxy[0])
    profile.set_preference("network.proxy.http_port", int(random_proxy[1]))
    # profile.add_extension('driver_extensions/close_proxy_authentication-1.1-sm+tb+fx.xpi')
    # credentials = '{user}:{passw}'.format(user='rezahavaei', passw='be9916-31138d-ed44f7-e8ed13-c5f21e')
    # credentials = b64encode(credentials.encode('ascii')).decode('utf - 8')
    # profile.set_preference('extensions.closeproxyauth.authtoken', credentials)
    # profile.set_preference("network.proxy.socks_remote_dns", True)
    profile.update_preferences()

    insta_page = 'https://www.instagram.com/accounts/emailsignup/'
    temp_mail_page = 'https://email-fake.com/'

    driver_insta = webdriver.Firefox(firefox_profile=profile)
    driver_mail = webdriver.Firefox(firefox_profile=profile)

    try:
        driver_insta.get(insta_page)
        try:
            driver_insta.find_element(By.CSS_SELECTOR, 'button.aOOlW.bIiDR').click()
        except Exception:
            pass

        driver_mail.get(temp_mail_page)
        # time.sleep(5)
        email_element_wait = WebDriverWait(driver_mail, 30)
        email_element_wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="email_ch_text"]')))
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

        month_select = Select(
            driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[1]/select'))
        month_value = random.randint(1, 12)
        month_select.select_by_value(str(month_value))

        day_select = Select(
            driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[2]/select'))
        day_value = random.randint(1, 28)
        day_select.select_by_value(str(day_value))

        year_select = Select(
            driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select'))
        year_value = random.randint(1970, 2000)
        year_select.select_by_value(str(year_value))

        next_btn_elem = driver_insta.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div[1]/div/div[6]/button')
        next_btn_elem.click()

        time.sleep(15)
        refresh_btn = driver_mail.find_element_by_xpath('/html/body/div[2]/div/div[2]/table/tbody/tr[3]/td[1]/a/button')
        refresh_btn.click()

        mail_wait = WebDriverWait(driver_mail, 300)
        mail_wait.until(EC.presence_of_element_located((By.XPATH,
                                                        '/html/body/div[3]/div/div/div/div[2]/div[2]/div[4]/div[3]/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[2]')))

        confirmation_code_element = driver_mail.find_element_by_xpath(
            '/html/body/div[3]/div/div/div/div[2]/div[2]/div[4]/div[3]/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[2]').text

        confirm_input = driver_insta.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div[1]/div[2]/form/div/div[1]/input')
        confirm_input.send_keys(confirmation_code_element)

        next_btn = driver_insta.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div[1]/div[2]/form/div/div[2]')
        next_btn.click()
        time.sleep(30)

        InstaUser.objects.create(username=email_element, password=password, fake_user=True)

        logger.info(f'Instagram User Created with the Credential of [username: {email_element}] and [password: {password}]')

    except Exception as e:
        logger.error(f'Instagram sign up failed -- error: {str(e)}')

    # driver_insta.quit()
    # driver_mail.quit()
    InstaUser.objects.create(username=email_element, password=password, fake_user=True)


def get_ip():
    # myProxy = 'http://rezahavaei:be9916-31138d-ed44f7-e8ed13-c5f21e@usa.rotating.proxyrack.net:333'

    my_proxy = '209.205.212.36:333'

    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.http", "209.205.212.36")
    profile.set_preference("network.proxy.http_port", 333)
    profile.add_extension('driver_extensions/close_proxy_authentication-1.1-sm+tb+fx.xpi')
    credentials = '{user}:{passw}'.format(user='rezahavaei', passw='be9916-31138d-ed44f7-e8ed13-c5f21e')
    credentials = b64encode(credentials.encode('ascii')).decode('utf - 8')
    profile.set_preference('extensions.closeproxyauth.authtoken', credentials)
    profile.set_preference("network.proxy.socks_remote_dns", True)
    profile.update_preferences()
    driver = webdriver.Firefox(firefox_profile=profile)

    driver.get("http://httpbin.org/ip")
