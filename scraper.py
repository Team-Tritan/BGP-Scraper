from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json

debug = False

def get_user_choice():
    print("1. Convert .json to .csv (peers or prefixes)")
    print("2. Lookup an ASN (peers or prefixes)")
    print("3. Lookup prefixes by ASN dump (json peers file)")
    print ("4. Generate iptables script from json peers file")
    return input("Enter your choice: ").strip()

def read_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def write_csv_file(output_filename, data, headers):
    with open(output_filename, 'w') as f:
        f.write(",".join(headers) + "\n")
        for item in data:
            f.write(",".join([str(item[field]) for field in headers]) + "\n")

def generate_iptables_script(data, script_filename):
    with open(script_filename, 'w') as script_file:
        script_file.write("#!/bin/bash\n\n")
        for item in data:
            if 'ip' in item:
                ip_address = item['ip']
                script_file.write(f"iptables -A INPUT -s {ip_address} -j DROP\n")
                script_file.write(f"iptables -A OUTPUT -d {ip_address} -j DROP\n")
        print(f"iptables rules written to {script_filename}")

def main():
    choice = get_user_choice()

    if choice == "1":
        filename = input("Enter the filename: ").strip()
        data = read_json_file(filename)
        output_filename = input("Enter the output filename: ").strip()

        if "asn" in data[0]:
            headers = ["Flag", "ASN", "ASN Name"]
            write_csv_file(output_filename, data, headers)

        if "prefix" in data[0]:
            headers = ["Prefix"]
            write_csv_file(output_filename, data, headers)

    if choice == "2":
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')
        options.binary_location = "/usr/bin/chromium-browser"

        if debug:
            options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=options)
        asn = input("Enter the ASN: ").strip()

        if not asn.isdigit():
            print("Invalid ASN.")
            exit()

        shouldSort = input("Sort by country? (y/n): ").strip().lower() == "y"
        whatSort = input("What country? (e.g. US): ").strip() if shouldSort else None

        shouldDump = input("Dump results to .json file? (y/n): ").strip().lower() == "y"
        dumps = []

        print("\n1. Peers")
        print("2. Prefixes")
        choice = input("Enter your choice: ")

        if choice == "1":
            url = f'https://bgp.tools/as/{asn}#connectivity'
            driver.get(url)

            xpath = '/html/body/div[1]/div[5]/div[2]/div[1]/div[7]/table[3]/tbody'
            tbody = driver.find_element(By.XPATH, xpath)

            if tbody is not None:
                for tr in tbody.find_elements(By.TAG_NAME, 'tr'):
                    flag, asn, asn_name = "", "", ""
                    trs = tr.find_elements(By.TAG_NAME, 'td')
                    img = trs[0].find_element(By.TAG_NAME, 'img')
                    flag = img.get_attribute('title')
                    asn = trs[1].get_attribute('data-sort')
                    asn_name = trs[2].text

                    if shouldDump and (not shouldSort or flag == whatSort):
                        dumps.append({"flag": flag, "asn": asn, "asn_name": asn_name})

                    if not shouldSort or flag == whatSort:
                        print(f'{flag} {asn} {asn_name}')

                if shouldDump:
                    with open('peers.json', 'w') as f:
                        json.dump(dumps, f)

        if choice == "2":
            url = f'https://bgp.tools/as/{asn}#prefixes'
            driver.get(url)
            css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
            elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

            dumps = [{"prefix": element.text} for element in elements] if shouldDump else None
            prefixes = [element.text for element in elements]

            for prefix in prefixes:
                print(prefix)

            if shouldDump:
                with open('prefixes.json', 'w') as f:
                    json.dump(dumps, f)

    if choice == "3":
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')
        options.binary_location = "/usr/bin/chromium-browser"

        if debug:
            options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=options)
        filename = input("Enter the filename: ").strip()
        data = read_json_file(filename)
        output_filename = input("Enter the output filename: ").strip()

        with open(output_filename, 'w') as f:
            f.write("Prefix\n")
            for item in data:
                url = f'https://bgp.tools/as/{item["asn"]}#prefixes'
                driver.get(url)
                css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
                elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
                prefixes = [element.text for element in elements]
                f.write("\n".join(prefixes) + "\n")

        driver.quit()

    if choice == "4":
        generate_iptables_script(dumps, 'iptables_rules.sh')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
