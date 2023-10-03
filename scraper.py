from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def main():
    # Define the custom user agent
    custom_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"

    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument('--headless')
    options.binary_location = "/usr/bin/chromium-browser"
    driver = webdriver.Chrome(options=options)

    # Get le user input (which asn they wanna see??)
    asn = input("Enter the ASN: ")

    # validate:(
    if not asn.isdigit():
        print("Invalid ASN.")
        exit()

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

            # Print the results
            print(flag, asn, asn_name)

    else:
        print("Tbody not found.")

    # Close the browser
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
