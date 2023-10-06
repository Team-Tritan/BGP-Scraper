from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json

debug = False

# Options selector
def get_user_choice():
    print("1. Convert .json to .csv (peers or prefixes)")
    print("2. Lookup an ASN (peers or prefixes)")
    print("3. Find prefixes from ASN dump (json peers file)")
    print("4. Generate iptables script from ASN dump (json peers dump)")
    return input("Enter your choice: ").strip()

# Read an output file by name
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

# Convert json to CSV
def write_csv_file(output_filename, data, headers):
    try:
        with open(output_filename, 'w') as f:
            f.write(",".join(headers) + "\n")
            for item in data:
                f.write(",".join([str(item[field]) for field in headers]) + "\n")
    except Exception as e:
        print(f"Error writing to {output_filename}: {str(e)}")

# Generate bash script to block ips
def generate_iptables_script(data, script_filename):
    try:
        with open(script_filename, 'w') as script_file:
            # Write the shebang 
            script_file.write("#!/bin/bash\n\n")
            for item in data:
                if 'prefix' in item:
                    prefix = item['prefix']
                    if ':' in prefix:
                        # IPv6 prefix
                        script_file.write(f"ip6tables -A INPUT -s {prefix} -j DROP\n")
                        script_file.write(f"ip6tables -A OUTPUT -d {prefix} -j DROP\n")
                    else:
                        # IPv4 prefix
                        script_file.write(f"iptables -A INPUT -s {prefix} -j DROP\n")
                        script_file.write(f"iptables -A OUTPUT -d {prefix} -j DROP\n")
                else:
                    print("Skipping item without 'prefix' field in JSON data.")
        print(f"Iptables rules written to {script_filename}")
    except Exception as e:
        print(f"Error generating iptables script: {str(e)}")

def main():
    # Get the users choice
    choice = get_user_choice()

    # Convert json to CSV
    if choice == "1":
        filename = input("Enter the filename: ").strip()
        data = read_json_file(filename)
        if data is not None:
            output_filename = input("Enter the output filename: ").strip()

            if "asn" in data[0]:
                headers = ["Flag", "ASN", "ASN Name"]
                write_csv_file(output_filename, data, headers)

            if "prefix" in data[0]:
                headers = ["Prefix"]
                write_csv_file(output_filename, data, headers)

    # Cleaned up so these are only defined once
    if choice in ["2", "3", "4"]:
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')

        # Ask for the host OS.
        os_type = input("What OS are you using? \n1. Debian or 2) Arch: ")

        # Set the binary based on host OS
        if os_type == "1":
            options.binary_location = "/usr/bin/chromium-browser"
        elif os_type == "2":
            options.binary_location = "/usr/sbin/chromium"

        # Debugging methods
        if debug:
            options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=options)

        if choice in ["2", "3"]:
            asn = input("Enter the ASN: ").strip()

            if not asn.isdigit():
                print("Invalid ASN.")
                exit()

        # Lookup an ASN
        if choice == "2":
            shouldSort = input("Sort by country? (y/n): ").strip().lower() == "y"
            whatSort = input("What country? (e.g. US): ").strip() if shouldSort else None
            shouldDump = input("Dump results to .json file? (y/n): ").strip().lower() == "y"
            dumps = []

            # Print the options
            print("\n1. Peers")
            print("2. Prefixes")
            lookup_choice = input("Enter your choice: ")

            # Peers
            if lookup_choice == "1":
                url = f'https://bgp.tools/as/{asn}#connectivity'
                try:
                    # Get the page data by xpath
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

                            # Add to the dumps list if we should dump
                            if shouldDump and (not shouldSort or flag == whatSort):
                                dumps.append({"flag": flag, "asn": asn, "asn_name": asn_name})

                            # Print the results if we should sort or if the flag matches
                            if not shouldSort or flag == whatSort:
                                print(f'{flag} {asn} {asn_name}')
                                
                        # Dump the results to a file if we should
                        if shouldDump:
                            with open('peers.json', 'w') as f:
                                json.dump(dumps, f)
                except Exception as e:
                    print(f"Error while processing: {str(e)}")

            # Prefixes
            elif lookup_choice == "2":
                url = f'https://bgp.tools/as/{asn}#prefixes'
                try:
                    # Get the page data by css selector
                    driver.get(url)
                    css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
                    elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

                    # Dump the results to a file if we should
                    dumps = [{"prefix": element.text} for element in elements] if shouldDump else None
                    prefixes = [element.text for element in elements]

                    # Print the results
                    for prefix in prefixes:
                        print(prefix)

                    # Dump the results to a file if we should
                    if shouldDump:
                        with open('prefixes.json', 'w') as f:
                            json.dump(dumps, f)
                except Exception as e:
                    print(f"Error while processing: {str(e)}")

        # Find prefixes from ASN dump
        if choice == "3":
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
        if choice == "4":
            filename = input("Enter the filename for the JSON peers file: ").strip()
            data = read_json_file(filename)
            if data is not None:
                generate_iptables_script(data, 'iptables_rules.sh')

    # Invalid choice
    if choice not in ["2", "3", "4"]:
        print("Invalid choice. Exiting...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
