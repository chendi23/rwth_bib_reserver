# -*- coding: utf-8 -*-
"""
@Time : 2021/11/28 11:10 上午
@Auth : zcd_zhendeshuai
@File : auto_booking.py
@IDE  : PyCharm

"""
import datetime
import os
import re
import sys
import time
# import bs4
import requests
from selenium import webdriver
import threading
from apscheduler.schedulers.background import BlockingScheduler, BackgroundScheduler
from logger_config import get_logger

logger = get_logger('./booking.log')


class MyThread(threading.Thread):
    def __init__(self, func, args, name):
        super(MyThread, self).__init__()
        self.name = name
        self.func = func
        self.args = args
        logger.debug('begin thread:' + self.name)
        self.results = self.func(*self.args)
        logger.debug('exit thread:' + self.name)

    def get_results(self):
        return self.results


def booking_preprocessing(library='morgan', idx='am'):
    required_path = str(library) + '_' + str(idx) + '_path'
    lib_path_dict = {
        'bib2_am_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[7]/div[2]/table/tbody/tr[1]/td[9]/input',
        'bib2_pm_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[7]/div[2]/table/tbody/tr[2]/td[9]/input',
        'bib1_am_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[6]/div[2]/table/tbody/tr[1]/td[9]/input',
        'bib1_pm_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[6]/div[2]/table/tbody/tr[2]/td[9]/input',
        'bib_InfoZentrum_0_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[9]/div[2]/table/tbody/tr[1]/td[9]/input',
        'bib_InfoZentrum_1_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[9]/div[2]/table/tbody/tr[2]/td[9]/input',
        'bib_InfoZentrum_2_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[9]/div[2]/table/tbody/tr[1]/td[9]/input',
        'morgan_am_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[4]/div[2]/table/tbody/tr[1]/td[9]/input',
        'morgan_pm_path': '/html/body/div[2]/div[5]/div/div/div[2]/div/form/div[4]/div[2]/table/tbody/tr[2]/td[9]/input',
    }
    root_url = 'https://buchung.hsz.rwth-aachen.de/angebote/aktueller_zeitraum/_Lernraumbuchung.html'

    driver = webdriver.Chrome()
    driver.get(root_url)

    driver.find_element_by_xpath(lib_path_dict[required_path]).click()
    driver.switch_to.window(driver.window_handles[1])

    tomorrow_booking_button_path = '/html/body/form/div/div[2]/div/div[2]/div[1]/label/div[2]/input'
    driver.find_element_by_xpath(tomorrow_booking_button_path).click()
    time.sleep(5)
    fid_path = '/html/body/form/input[1]'
    fid_element = driver.find_element_by_xpath(fid_path)
    fid = fid_element.get_attribute('value')
    return fid


def send_booking_table(fid, personal_dict):
    if not personal_dict:
        personal_dict = {
            'Termin': str(datetime.date.today()),
            'sex': 'M',
            'vorname': 'Paul',
            'name': 'Chris',
            'strasse': 'Kingsroad',
            'ort': '52072 Aachen',
            'statusorig': 'Sch\xFCler',
            'email': '1724714798@google.com',
            'telefon': '015279661265',
            'tnbed': '1'
        }
    personal_dict['fid'] = fid
    personal_dict['pw_email'] = ''
    personal_dict['pw_pwd_%s' % fid] = ''

    headers = {
        'authority': 'buchung.hsz.rwth-aachen.de',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'upgrade-insecure-requests': '1',
        'origin': 'https://buchung.hsz.rwth-aachen.de',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://buchung.hsz.rwth-aachen.de/cgi/anmeldung.fcgi',
        'accept-language': 'zh-CN,zh;q=0.9',
    }

    response = requests.post('https://buchung.hsz.rwth-aachen.de/cgi/anmeldung.fcgi', headers=headers,
                             data=personal_dict)
    logger.debug('Booking request is already sent ^ ^')
    result_pat = re.compile('"bs_form_entext">(.*?)<')
    tmp_res = re.findall(result_pat, (response.text))
    res = tmp_res[-2] + tmp_res[-1]
    logger.debug('-----response-----:%s' % res)


def job_reserve(library, idx, personal_dict):
    fid = booking_preprocessing(library=library, idx=idx)
    send_booking_table(fid=fid, personal_dict=personal_dict)
    return 'A booking trial is finished'


def thread_job_reserve(library, idx, personal_dict):
    thread_job = MyThread(func=job_reserve, args=(library, idx, personal_dict),
                          name='booking: place={}\t idx={}'.format(library, idx))
    logger.debug(thread_job.get_results())


def start_scheduler_reserve_job(mode='hard_working', personal_dict=None):
    scheduler = BlockingScheduler()
    scheduler.start()
    if mode == 'hard_working':
        scheduler.add_job(job_reserve,
                          trigger='cron',
                          hour='8',
                          args=['bib2', 'am', personal_dict],
                          )
        scheduler.add_job(job_reserve,
                          trigger='cron',
                          hour='8',
                          args=['bib2', 'pm', personal_dict])
    elif mode == 'lazy':
        scheduler.add_job(job_reserve,
                          trigger='cron',
                          day_of_week='mon-fri',
                          hour='8',
                          args=['bib2', 'am', personal_dict])
        scheduler.add_job(job_reserve,
                          trigger='cron',
                          day_of_week='mon-fri',
                          hour='8',
                          args=['bib2', 'pm', personal_dict])
    return


if __name__ == '__main__':
    # start_scheduler_reserve_job()
    scheduler = BlockingScheduler()
    scheduler.add_job(thread_job_reserve,
                      trigger='date',
                      args=['bib1', 'am',{}],
                      )
    scheduler.add_job(thread_job_reserve,
                      trigger='date',
                      args=['bib1', 'pm', {}],
                      )
    if not scheduler.running:
        scheduler.start()
