import requests 
import asyncio
import warnings 
import os 
import argparse 
import concurrent.futures
from pyppeteer import launch
from urllib.parse import urlparse
from colorama import Fore,Style
from concurrent.futures import ThreadPoolExecutor

"""
Description: A script to take a list of subdomains / ip addresses and take screenshot of valid tarets
Author: Sunggwan Choi 

Created for: Boan Project - Week2 
"""

def print_green(strings):
    try:
        print(Fore.GREEN + strings + Style.RESET_ALL)
    except Exception as e:
        print(Fore.GREEN + strings.encode('ascii',errors='ignore').decode('ascii') + Style.RESET_ALL)

def print_blue(strings):
    try:
        print(Fore.BLUE + strings + Style.RESET_ALL)
    except Exception as e:
        print(Fore.BLUE + strings.encode('ascii',errors='ignore').decode('ascii') + Style.RESET_ALL)

def print_red(string):
    try:
        print(Fore.RED + string + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + string.encode('ascii',errors='ignore').decode('ascii') + Style.RESET_ALL)



def parseFile(fName):
    """
    Description: Takes in a filename, returns a list of strings. 
    Used for parsing subdomains and ip list from a text file on disk.
    """

    result = []

    try:
        with open(fName,'r') as fd:
            for line in fd:
                line = line.strip()
                result.append(line)
    except Exception as e:
        print("[-] Error: ", str(e))

    return result 

def chaseRedirects(url):
    while True:
        yield url
        res = requests.head(url)
        if 300 < res.status_code < 400:
            url = res.headers['location']
        else:
            break

    return url

def findSchema(target):
    """
    Description: Find correct http,https schema for the given url. Useful when the targetlist 
    is just bunch of subdomains (ex. abc.google.com, bbb.google.com, etc...)

    TODO: Implement chaseRedirect. Currently, some of the pages which redirects to another page (some pages 
    even use javascript for redirection jesus) are not being found correctly due to not chasing redirects. 

    Param:
        - (str) target : Target; Most likely an ip address or a subdomain name 
    
    Returns:
        - (str) res.url : Full URL of the target 

    """
    fullURL = target  
    user_agent = 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36'

    s = requests.Session()
    s.headers['User-Agent'] = user_agent
    
    # Catch schema error - append http 
    try:
        res = s.get(fullURL,timeout=3, allow_redirects=True)
    except requests.exceptions.MissingSchema as e:
        fullURL = "http://" + fullURL
    
    # Catch http error - change to https 
    try:
        res = s.get(fullURL,timeout=3, allow_redirects=True)
    except requests.exceptions.ConnectionError as e:
        fullURL = fullURL.replace('http','https')

    # Catch https error - something is wrong 
    try:
        res = s.get(fullURL,timeout=3, allow_redirects=True)
    except Exception as e:
        return "[-] " + target
    
    
    # Returns the final (all redirected) url 
    return res.url

async def takeScreenshot(url, filename):
    """
    Description: Coroutine to take screenshot from the url, and save the screenshot as a png file.
    Param:
        - (str) url : URL to visit and take screenshot 
        - (str) filename : Name of the png file to be saved as 
    """
    try:
        browser = await launch(headless=True, args=['--no-sandbox'])
        page = await browser.newPage()
        page.setDefaultNavigationTimeout(20000)
        await page.setUserAgent('Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36')
        await page.goto(url)
        await page.screenshot({'path': filename})
        await browser.close() 
    except Exception as e:
        print_red("[-] [URL] " + url + " Error: " + str(e) + " Try again")

def parseArguments():
    """
    Description: Parse commandline argument from the user
    """

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-f', '--file', dest='f', type=str, help='full directory path of the subdomain list', required=True)

    # TODO: Implement two options down below 
    parser.add_argument('-u', '--url', dest='u', type=str, help='Single full url of the target to get screenshot')
    parser.add_argument('-o', '--output-dir', dest='o', type=str, help='Output directory of the screenshots')

    try:
        arguments = parser.parse_args()
    except Exception as e:
        print_red("[-] Argument parsing failed: " + str(e))
        exit(1)
    
    return arguments 

async def main():
    arguments = parseArguments()

    targetList = []
    finalList = []
    brokenList = []

    # ========== Argument handling section ==========

    # Check if user gave list of targets. Build finalList by actually visiting the endpoint. 
    if arguments.f is not None:
        targetFilename = arguments.f 
        targetList = parseFile(targetFilename)

        # Find http/https by asynchronously visiting the targets 
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(findSchema, target) for target in targetList]
            
            # Create valid url list and broken url list from the return value of findSchema function
            for future in futures:
                if "[-]" in future.result():
                    brokenList.append(future.result().split("[-] ")[1])
                else:
                    finalList.append(future.result())

    else:
        print("[DEBUG] for now, exit upon no filename input from the user")
        exit(1)

    # Check if user gave output directory 
    if arguments.o is not None:
        directory = arguments.o
    else:
        directory = os.getcwd() + "/images/"

    print_green("[+] Fetched correct URLs. Taking screenshots. \nThis May take a while...\n")

    # ========== Print Valid, Invalid Targets  ==========

    print("======== VALID TARGET ========")
    for target in finalList:
        print(target)
    print("\n")
    print("======== INVALID TARGET ========")
    for target in brokenList:
        print(target)
    print("\n")

    # ========== Take Screenshot section  ==========

    # List for async tasks 
    asyncList = []   

    for target in finalList:
        filename = directory + urlparse(target).netloc + ".png"
        print_green("[+] Taking screenshot, URL: " + target)

        # Create async task and append to the asynclist. This will be gathered later. 
        task = asyncio.ensure_future(takeScreenshot(target,filename))
        asyncList.append(task)

    responses = await asyncio.gather(*asyncList)

    print_blue("[+] Screenshots saved in ./images")


# Start of asyncio main 
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main())
    loop.run_until_complete(future)
    