
#################################################
# upload images to avideo
# and download images from avideo
#################################################

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import time
import requests
import argparse
import sys
import os

# for explicit wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# pip install selenium-wire
#from seleniumwire import webdriver

# for generating a random string
import random
import string
from datetime import datetime

# enumerate files
from os import listdir
from os.path import isfile, join


#################################################
# customizable variables

# create an account with the avideo server and
# put the username and password here
my_user = "test" 
my_pass = "xyzXYZ123#"

# specify the path where one can find the firefox webdriver
geckodriver_install = "/usr/local/bin/geckodriver"

avideo_base = "http://destini02.csl.sri.com"
# avideo_base = "https://destini02.csl.sri.com"

avideo_url = avideo_base

# note: encoder listens to port 8000 in the docker-compose config
avideo_encoder_url  = avideo_base + ":8000"
# avideo_encoder_url  = avideo_base + ":8443"

# disable warnings for unverified https
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# max sleep interval for explicit wait calls (in sec)
max_sleep = 10

#################################################


def safe_str(obj):
    return obj.encode('ascii', 'ignore').decode('ascii')


#################################################


def webdriver_setup ():

    options = Options()

    # uncomment the following to enable headless mode
    options.headless = True

    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("network.prefetch-next", False)

    try:
        driver = webdriver.Firefox(options=options,firefox_profile=firefox_profile,executable_path=geckodriver_install)
        # driver.implicitly_wait (10) # sec

    except Exception as e:
        print (f"Error: webdriver failed {e}")
        return None

    return driver


#################################################

def avideo_login (driver):

    print ("Entering avideo_login")

    avideo_login = avideo_url + "/user"

    try:
        driver.get(avideo_login)

        myuser = driver.find_element_by_css_selector('input[id=inputUser]').send_keys(my_user)
        mypass = driver.find_element_by_css_selector('input[id=inputPassword]').send_keys(my_pass)
        driver.find_element_by_css_selector('button[id=mainButton]').click()

        resp = safe_str(driver.page_source)

        if "Sign out" in resp:
            print ("Login Successful!")
        else:
            print ("Login Failed")
            with open('login.html', 'w') as f:
                f.write(resp)
            return False

    except Exception as e:
        print (f"Error: login failed {e}")
        driver.quit()
        return False 

    time.sleep(2)

    print ("Exiting avideo_login")

    return True

#################################################

def encoder_login (driver):

    print ("Entering encoder_login")

    try:
        driver.get(avideo_encoder_url)

        # debug
        encoder_source = safe_str(driver.page_source)
        with open('encoder.html', 'w') as f:
             f.write(encoder_source)

        time.sleep(3)
        streamer = driver.find_element_by_css_selector('input[id=siteURL]').clear()
        streamer = driver.find_element_by_css_selector('input[id=siteURL]').send_keys(avideo_url)
        myuser = driver.find_element_by_css_selector('input[id=inputUser]').send_keys(my_user)
        mypass = driver.find_element_by_css_selector('input[id=inputPassword]').send_keys(my_pass)
        driver.find_element_by_css_selector('button[id=mainButton]').click()

    except Exception as e:
        print (f"Error: Encoder login failed {e}")
        driver.quit()
        return False

    time.sleep(5)
    resp = safe_str(driver.page_source)
    
    if "Logoff" in resp:
        print ("Login Successful!")
    else:
        print ("Login Failed")
        with open('login.html', 'w') as f:
            f.write(resp)
            return False

    return True

#################################################


def upload(upfilepath, mytitle, image_tag, driver):

    print ("starting upload at ", avideo_encoder_url)

    time.sleep(1)

    try:
        driver.get(avideo_encoder_url)
        title = driver.find_element_by_css_selector('input[id=title]').send_keys(mytitle)
        descr = driver.find_element_by_css_selector('textarea[id=description]').send_keys(image_tag)
        time.sleep(2)
        file  = driver.find_element_by_css_selector('input[type=file]').send_keys(upfilepath)
        time.sleep(2)
        driver.find_element_by_css_selector('button[type=submit]').click()

    except Exception as e:
        print (f"Error: avideo encoder failed {e}")
        driver.quit()
        return False 


    # debug: wait for the upload to finish
    time.sleep(60)

    # check to see if the upload is complete
    # perform a query using a "unique" tag associated the video 

    search_url = avideo_base + "/?search=" + image_tag

    print ("search_url: " + search_url)

    num_try = 0
    max_try = 3
    done = False

    while num_try < max_try and done == False:
      num_try = num_try + 1
      print ("upload check for key %s attempt: %d" % (image_tag, num_try))
      driver.get(search_url)
      html_source = safe_str(driver.page_source)
      
      with open('search.html', 'w') as f:
          f.write(html_source)

      try:
          element = WebDriverWait(driver, max_sleep).until (
              EC.presence_of_element_located((By.XPATH, "//meta[@property='og:description']"))
          )
      except TimeoutException:
          print("Timeout while locating locate meta og:description")
          continue
      except NoSuchElementException:
          print("Unable to locate meta description")
          continue

      soup = BeautifulSoup(html_source, features="html.parser")

      description = soup.find("meta",  property="og:description")

      print (description["content"] if description else "no meta description found")

      if description and image_tag in description["content"]: 
          print ("image found. attempt: %d" % num_try)
          # print ("og:description: %s" % description)
          done = True
      else: 
          print ("image not found. attempt: %d" % num_try)
          # print ("og:description: %s" % description)
          time.sleep(1)

    if done: 
        return True
    else:
        return False

#################################################

def download (downfilepath, search_tag, driver):

    success = False

    search_url = avideo_base + "/?search=" + search_tag

    print ("search_url: " + search_url)

    driver.get(search_url)

    time.sleep(1)

    html_source = safe_str(driver.page_source)

    with open('results.html', 'w') as f:
       f.write(html_source)

    soup = BeautifulSoup(html_source, features="html.parser")


    storage_urls = []

    # for the 1st match 
    images = soup.findAll('source')
    for image in images:
        image_src = image.get('src')
        if not image_src:
            # print ("image_src is null")
            continue
        # print (image_src)
        if "_HD" in image['src']:
            # print ("cp1a found hd link in:" + format(image['src']))
            storage_urls.append(image['src'])

    # debug
    # print ("cp1 storage_urls: " + format(storage_urls))

    # for other matches ...
    images = soup.findAll('img')
    for image in images:
        image_datasrc = image.get('data-src')
        if not image_datasrc:
            # print ("cannot find data-src") 
            continue

        if ".webp" in image['data-src']:
            print ("webp link: " + image['data-src'])
            # construct the url for the HD link
            # hd_link = image_datasrc.replace("_thumbsV2.jpg?", "_HD.mp4")
            hd_link = image_datasrc.replace(".webp", "_HD.mp4")
            print ("hd link: " + hd_link)
            if hd_link in storage_urls:
                print ("already found: " + hd_link)
            else:
                print ("adding: " + hd_link)
            #     storage_urls.append(hd_link)

    # debug
    # print ("cp2 storage_urls :" + format(storage_urls))

    if storage_urls:
    
        ##############################
        # selenium doesn't seem to support one to download a file (e.g., jpeg file) directly
        # we construct a get request (need to import requests) with the user-agent string
        # and cookie used by selenium
    
        # find the cookies used by selenium
        try:
            selenium_cookies = driver.get_cookies ()
        except:
            print (f"Avideo Exception error: couldn't get cookies; {sys.exc_info ()[0]}")
            # break  # TBD: is this a pathological failure?
    
        cookies = {
            'value': selenium_cookies[0].get ('value'),
        }
    
        try: 
            # find the user-agent string used by selenium
            user_agent = driver.execute_script ("return navigator.userAgent;")
        except:
            print (f"Avideo Exception error 5: couldn't get useragent; {sys.exc_info ()[0]}")
            # break  # TBD: is this a pathological failure?
    
        headers = {
            'User-Agent': user_agent,
        }
    
        for url in storage_urls:
            try:
                response = requests.get (url, cookies = cookies, headers = headers, verify = False)
                video_download = response.content
    
            except:
                print (f"Avideo Exception err: url fetch failed; {sys.exc_info ()[0]}")
                break           # "do once"

            # assume there's one match
            with open (downfilepath, 'wb') as f_out:
                f_out.write (video_download)
                f_out.close()
                success = True


    return success

#################################################

def cleanup(driver):
    driver.close()

#################################################

def main():
    parser = argparse.ArgumentParser(description='upload an image to avideo and download the image from avideo')
    # parser.add_argument('-i', dest='infile',  help='path for upload image', default="/homes/vinod/w2.mp4")
    # parser.add_argument('-i', dest='infile',  help='path for upload image', default="/homes/cheung/selenium/boat.mp4")
    parser.add_argument('-i', dest='infile',  help='path for upload image', default="/destini-media/videos/Worship_out.mp4")  
    parser.add_argument('-o', dest='outfile', help='path for download image', default="worship.mp4")
    args = parser.parse_args()

    print ("input path: "  + args.infile)
    print ("output path: " + args.outfile)

    driver = webdriver_setup()
    
    if driver == None:
        return

    result = encoder_login(driver)
    if not result:
        cleanup(driver)
        return

    # uploading video

    letters = string.ascii_lowercase
    random.seed(datetime.now())

    tag = ''.join(random.choice(letters) for i in range(10))
    result = upload(args.infile, "fallout", tag, driver)

    if result:
        print ("Upload completed")
    else:
        print ("Error: Upload failed")

    # downloading video

    result = download(args.outfile, tag, driver)

    if result:
        print ("Download completed")
    else:
        print ("Error: Download failed")


    time.sleep(10)

    cleanup(driver)

if __name__ == '__main__':
    main()
