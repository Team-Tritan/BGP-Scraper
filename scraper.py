from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json

debug = False

# Function to get user's choice
def get_user_choice():
    print("1. Dump an ASN (peers or prefixes)")
    print("2. Find prefixes from ASN dump (json peers file)")
    print("3. Generate iptables script from ASN dump (json prefixes dump)")
    return input("Enter your choice: ").strip()

# Function to read a JSON file by name
def read_json_file(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {str(e)}")
        return None

# Function to generate iptables script from JSON data
def generate_iptables_script(data, script_filename):
    try:
        with open(script_filename, 'w') as script_file:
            # Write the shebang 
            script_file.write("#!/bin/bash\n\n")
            for item in data:
                if 'prefix' in item:
                    prefix = item['prefix']
                    # IPv6 prefix
                    if ':' in prefix:
                        script_file.write(f"ip6tables -A INPUT -s {prefix} -j DROP\n")
                        script_file.write(f"ip6tables -A OUTPUT -d {prefix} -j DROP\n")
                    # IPv4 prefix
                    else:
                        script_file.write(f"iptables -A INPUT -s {prefix} -j DROP\n")
                        script_file.write(f"iptables -A OUTPUT -d {prefix} -j DROP\n")
                else:
                    print("Skipping item without 'prefix' field in JSON data.")
        print(f"Iptables rules written to {script_filename}")
    except Exception as e:
        print(f"Error generating iptables script: {str(e)}")

# Main function
def main():
    # Get the user's choice
    choice = get_user_choice()

    # Set up Chrome options
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument('--headless')

    # Ask for the host OS 
    os_type = input("What OS are you using? \n1. Debian or 2) Arch: ")

    # Set the binary based on host OS
    if os_type == "1":
        options.binary_location = "/usr/bin/chromium-browser"
    elif os_type == "2":
        options.binary_location = "/usr/sbin/chromium"

    if debug:
        options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=options)

    if choice in ["1", "2", "3"]:
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

    if choice == "1":
        asn = input("Enter the ASN: ").strip()

        if not asn.isdigit():
            print("Invalid ASN.")
            exit()

        dumps = []
        shouldDump = False
        shouldSort = False
        whatSort = ""

        # Should we sort by flag?
        sort = input("Sort by country? (y/n): ").strip()

        if sort.lower() == "y":
            shouldSort = True

            # Ask the user what country they want to sort by
            whatSort = input("What country? (e.g. US): ").strip()

        # Ask the user if they want to dump the results to a .json file
        dump = input("Dump results to .json file? (y/n): ")

        if dump.lower() == "y":
            shouldDump = True

        # Does the user want to see their peers or their prefixes?
        print("\n1. Peers")
        print("2. Prefixes")
        lookup_choice = input("Enter your choice: ")

        if lookup_choice == "1":
            # Navigate to the URL
            url = f'https://bgp.tools/as/{asn}#connectivity'
            driver.get(url)

            # Find the tbody element using XPath
            xpath = '/html/body/div[1]/div[5]/div[2]/div[1]/div[7]/table[3]/tbody'
            tbody = driver.find_element(By.XPATH, xpath)

            # Check if tbody is found
            if tbody is not None:
                # Iterate through each tr inside tbody
                for tr in tbody.find_elements(By.TAG_NAME, 'tr'):
                    flag = ""
                    asn = ""
                    asn_name = ""

                    trs = tr.find_elements(By.TAG_NAME, 'td')

                    # Find the td element inside each tr
                    td1 = trs[0]
                    if td1 is not None:
                        # Get the image element inside the td
                        img = td1.find_element(By.TAG_NAME, 'img')

                        # Set the flag
                        flag = img.get_attribute('title')

                    # Remove the first td element
                    as_td = trs[1]
                    if as_td is not None:
                        # ASN is stored inside attribute "data-sort"
                        asn = as_td.get_attribute('data-sort')

                    # Get the asn_name
                    asn_name_td = trs[2]
                    if asn_name_td is not None:
                        asn_name = asn_name_td.text

                    # Append the data to the list
                    if shouldDump:
                        if shouldSort:
                            if flag == whatSort:
                                dumps.append({
                                    "flag": flag,
                                    "asn": asn,
                                    "asn_name": asn_name
                                })
                        else:  # dont sort
                            dumps.append({
                                "flag": flag,
                                "asn": asn,
                                "asn_name": asn_name
                            })

                    # Print the data
                    if shouldSort:
                        if flag == whatSort:
                            print(f'{flag} {asn} {asn_name}')
                    else:  # dont sort
                        print(f'{flag} {asn} {asn_name}')

            else:
                print("Tbody not found.")

            if shouldDump:
                with open('peers.json', 'w') as f:
                    json.dump(dumps, f)

        if lookup_choice == "2":
            # Navigate to the URL
            url = f'https://bgp.tools/as/{asn}#prefixes'
            driver.get(url)

            # im sorry : (
            css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
            elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

            # Iterate through the elements to get the text content
            for element in elements:
                prefix_text = element.text
                print(prefix_text)

                if shouldDump:
                    dumps.append({
                        "prefix": prefix_text
                    })

            if shouldDump:
                with open('prefixes.json', 'w') as f:
                    json.dump(dumps, f)
                    
    if choice == "2":
        filename = input("Enter the filename: ").strip()
        data = read_json_file(filename)
        if data is not None:
                # Get the prefixes for each ASN based on output
            output_filename = input("Enter the output filename: ").strip()
            with open(output_filename, 'w') as f:
                f.write("Prefix\n")
                # Loop through the data
                for item in data:
                    url = f'https://bgp.tools/as/{item["asn"]}#prefixes'
                    try:
                        # Get the page data by css selector
                        driver.get(url)
                        css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
                        elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
                        prefixes = [element.text for element in elements]
                        f.write("\n".join(prefixes) + "\n")
                    except Exception as e:
                        print(f"Error while processing: {str(e)}")

    if choice == "3":
        # Get the filename
        filename = input("Enter the filename: ").strip()
        data = read_json_file(filename)
        if data is not None:
            # Get the prefixes for each ASN based on output
            output_filename = input("Enter the output filename: ").strip()

            with open(output_filename, 'w') as f:
                f.write("Prefix\n")
                # Loop through the data
                for item in data:
                    url = f'https://bgp.tools/as/{item["asn"]}#prefixes'
                    try:
                        # Get the page data by css selector
                        driver.get(url)
                        css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
                        elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
                        prefixes = [element.text for element in elements]
                        f.write("\n".join(prefixes) + "\n")
                    except Exception as e:
                        print(f"Error while processing: {str(e)}")

    # Generate iptables script from ASN dump
    if choice == "3":
        filename = input("Enter the filename for the JSON prefixes file: ").strip()
        data = read_json_file(filename)
        if data is not None:
            generate_iptables_script(data, 'iptables_rules.sh')

    if choice not in ["1", "2", "3"]:
        print("Invalid choice. Exiting...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
