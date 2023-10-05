from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import json

debug = False


def main():
    # Does the user want to convert .json to .csv, or lookup an ASN?
    print("1. Convert .json to .csv (peers or prefixes)")
    print("2. Lookup an ASN (peers or prefixes)")
    print("3. Lookup prefixes by ASN dump (json peers file)")
    choice = input("Enter your choice: ").strip()

    if choice == "1":
        # Get the filename
        filename = input("Enter the filename: ").strip()

        # Open the file
        with open(filename, 'r') as f:
            data = json.load(f)

        # Get the output filename
        output_filename = input("Enter the output filename: ").strip()

        # Open the output file
        with open(output_filename, 'w') as f:
            # Is it peers or prefixes?
            if "asn" in data[0]:
                # Write the header
                f.write("Flag,ASN,ASN Name\n")

                # Iterate through the data
                for item in data:
                    # Write the data to the file
                    f.write(
                        f'{item["flag"]},{item["asn"]},{item["asn_name"]}\n')
            if "prefix" in data[0]:
                # Write the header
                f.write("Prefix\n")

                # Iterate through the data
                for item in data:
                    # Write the data to the file
                    f.write(f'{item["prefix"]}\n')

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

        driver = webdriver.Chrome(
            options=options)

        # Get le user input (which asn they wanna see??)
        asn = input("Enter the ASN: ").strip()

        # validate:(
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
        choice = input("Enter your choice: ")

        if choice == "1":
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

        if choice == "2":
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

        driver = webdriver.Chrome(
            options=options)

        # Get le user input (which asn they wanna see??)
        filename = input("Enter the filename: ").strip()

        # Open the file
        with open(filename, 'r') as f:
            data = json.load(f)

        # Get the output filename
        output_filename = input("Enter the output filename: ").strip()

        # Open the output file
        with open(output_filename, 'w') as f:
            # Write the header
            f.write("Prefix\n")

            # Iterate through the data
            for item in data:
                # Navigate to the URL
                url = f'https://bgp.tools/as/{item["asn"]}#prefixes'
                driver.get(url)

                # im sorry : (
                css_selector = '#donotscrapebgptools-prefixlist-tbody td:nth-child(2) a'
                elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

                # Iterate through the elements to get the text content
                for element in elements:
                    prefix_text = element.text
                    print(prefix_text)

                    # Write the data to the file
                    f.write(f'{prefix_text}\n')

    # Close the browser
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
