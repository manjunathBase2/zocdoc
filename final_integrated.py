import json
import csv
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def scrape_doctor_profile(driver, url):
    wait = WebDriverWait(driver, 10)
    result = {}

    try:
        name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.loc-vs-fname')))
        result['Doctor Name'] = name_elem.text.strip()
    except:
        result['Doctor Name'] = None

    try:
        spec_elem = driver.find_element(By.CSS_SELECTOR, 'div.specialty.loc-vs-dspsplty')
        result['Speciality'] = spec_elem.text.strip()
    except:
        result['Speciality'] = None

    try:
        rating_elem = driver.find_element(By.CSS_SELECTOR, 'a.ratings span.rating-score')
        result['Rating'] = rating_elem.text.strip()
    except:
        result['Rating'] = None

    try:
        qf_ul = driver.find_element(By.CSS_SELECTOR, 'div.quickfacts-card ul')
        qf_lis = qf_ul.find_elements(By.TAG_NAME, 'li')
        quick_facts = [li.text.strip() for li in qf_lis]
        result['Quick Facts'] = quick_facts
    except:
        result['Quick Facts'] = []

    try:
        bio_elem = driver.find_element(By.CSS_SELECTOR, 'div.truncated.description.loc-vs-smrytxt')
        result['Bio'] = bio_elem.text.strip()
    except:
        result['Bio'] = None

    try:
        addr_elem = driver.find_element(By.CSS_SELECTOR, 'div.location.loc-vs-tplcadd')
        result['Address'] = addr_elem.text.strip()
    except:
        result['Address'] = None

    locations = []
    try:
        location_holder = driver.find_element(By.ID, 'location-card-holder')
        location_lines = location_holder.find_elements(By.CSS_SELECTOR, 'div.location-line.loc-vl-loc')
        for loc in location_lines:
            loc_info = {}

            try:
                try:
                    name_tag = loc.find_element(By.CSS_SELECTOR, 'a.title.loc-vl-locna h3')
                except:
                    name_tag = loc.find_element(By.CSS_SELECTOR, 'span.title.loc-vl-locna h3')
                loc_info['Name'] = name_tag.text.strip()
            except:
                loc_info['Name'] = None

            try:
                addr_first_line = loc.find_element(By.CSS_SELECTOR, 'span.address-first-line.loc-vl-locad').text.strip()
                city = loc.find_element(By.CSS_SELECTOR, 'span.loc-vl-loccty').text.strip()
                state = loc.find_element(By.CSS_SELECTOR, 'span.loc-vl-locsta').text.strip()
                zip_code = loc.find_element(By.CSS_SELECTOR, 'span.loc-vl-loczip').text.strip()
                loc_info['Address'] = f"{addr_first_line}, {city} {state} {zip_code}"
            except:
                loc_info['Address'] = None

            try:
                phone = loc.find_element(By.CSS_SELECTOR, 'div.phone a.loc-vl-telep').text.strip()
                loc_info['Phone'] = phone
            except:
                loc_info['Phone'] = None

            try:
                hours_div = loc.find_element(By.CSS_SELECTOR, 'div.hours')
                day_times = hours_div.find_elements(By.CSS_SELECTOR, 'div')
                hours = {}
                for dt in day_times:
                    day = dt.find_element(By.CSS_SELECTOR, 'span.day').text.strip()
                    time_ = dt.find_element(By.CSS_SELECTOR, 'span.time').text.strip()
                    hours[day] = time_
                loc_info['Hours'] = hours
            except:
                loc_info['Hours'] = None

            locations.append(loc_info)

        result['Office Locations'] = locations
    except:
        result['Office Locations'] = []

    return result

def scrape_additional_details(driver, url):
    def safe_find_element(by, val):
        try:
            return driver.find_element(by, val)
        except NoSuchElementException:
            return None
        
    def safe_find_elements(by, val):
        try:
            return driver.find_elements(by, val)
        except NoSuchElementException:
            return []

    data = {}
    data["Doctor_profile_link"] = url

    phone_el = safe_find_element(By.CSS_SELECTOR, "a.phone-cta span")
    data["Phone"] = phone_el.text.strip() if phone_el else ""

    # New insurance scraping with JS execution
    try:
        driver.find_element(By.ID, "insurance")  # Ensure section is present
        insurance_li_texts = driver.execute_script("""
            let items = document.querySelectorAll('#insurance ul.loc-vi-insur li');
            return Array.from(items).map(li => li.innerText.trim());
        """)
        data["Insurance_Plans"] = "; ".join(insurance_li_texts)
    except NoSuchElementException:
        print("Insurance section not found.")
        data["Insurance_Plans"] = ""
    except Exception as e:
        print(f"Error extracting insurance plans: {e}")
        data["Insurance_Plans"] = ""

    specialties_div = safe_find_element(By.ID, "specialties")
    specialties_list = []
    if specialties_div:
        lis = specialties_div.find_elements(By.CSS_SELECTOR, "ul li.loc-vc-splts a")
        specialties_list = [li.text.strip() for li in lis if li.text.strip()]
    data["Medical_Specialities"] = "; ".join(specialties_list)

    specialty_exp_ul = safe_find_element(By.CSS_SELECTOR, "ul.show-less.loc-vc-splex")
    specialty_exp_list = []
    if specialty_exp_ul:
        lis = specialty_exp_ul.find_elements(By.TAG_NAME, "li")
        specialty_exp_list = [li.text.strip() for li in lis if li.text.strip()]
    data["Specialty_Expertise"] = "; ".join(specialty_exp_list)

    experience = ""
    cert_header_divs = driver.find_elements(By.CSS_SELECTOR, "div.webmd-card__header")
    for div in cert_header_divs:
        try:
            h2 = div.find_element(By.TAG_NAME, "h2").text
            if "Certifications & Education" in h2:
                h3 = div.find_element(By.TAG_NAME, "h3")
                experience = h3.text.strip() if h3 else ""
                break
        except:
            continue
    data["Experience"] = experience

    cert_div = safe_find_element(By.CSS_SELECTOR, "div.info")
    education_spans = []
    if cert_div:
        spans = cert_div.find_elements(By.TAG_NAME, "span")
        education_spans = [span.text.strip() for span in spans if span.text.strip()]
    data["Certifications_Education"] = "; ".join(education_spans)

    hospital_div = safe_find_element(By.ID, "hospital-affiliations")
    hospital_p_list = []
    if hospital_div:
        p_tags = hospital_div.find_elements(By.CSS_SELECTOR, "ul.loc-vc-hospi li p")
        hospital_p_list = [p.text.strip() for p in p_tags if p.text.strip()]
    data["Hospital_Affiliations"] = "; ".join(hospital_p_list)

    return data

def main():
    with open("profile_0_links.json", "r") as f:
        urls = json.load(f)

    fieldnames = [
        "Doctor_profile_link", "Doctor Name", "Speciality", "Rating", "Quick Facts", "Bio", "Address",
        "Office Locations", "Phone", "Insurance_Plans", "Medical_Specialities",
        "Specialty_Expertise", "Experience", "Certifications_Education", "Hospital_Affiliations"
    ]

    with open("doctor_profiles_final.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        options = uc.ChromeOptions()
        options.headless = False
        driver = uc.Chrome(options=options)

        for url in urls:
            print(f"Scraping: {url}")
            try:
                driver.get(url)
                time.sleep(3)  # Allow time for the page to load
                if "Page Not Found" in driver.title:
                    print("❌ Page not found, skipping...")
                    continue

                data = scrape_doctor_profile(driver, url)
                additional = scrape_additional_details(driver, url)
                full_data = {**additional, **data}
                writer.writerow(full_data)
                print("✅ Done")
            except Exception as e:
                print(f"❌ Failed to scrape {url} due to error: {e}")
                continue  # Explicitly continue to the next URL

        driver.quit()

if __name__ == "__main__":
    main()
