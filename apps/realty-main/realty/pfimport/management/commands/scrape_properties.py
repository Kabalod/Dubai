import os
import re
import time
import json
import datetime
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Scrape properties from PropertyFinder and produce a single JSON output file"

    def add_arguments(self, parser):
        parser.add_argument("start_value", type=int, help="Page start value")
        parser.add_argument("end_value", type=int, help="Page end value")
        parser.add_argument(
            "--sleep",
            type=int,
            default=1,
            help="Sleep time between iterations in seconds",
        )
        parser.add_argument(
            "--output", type=str, help="Output file path for the final JSON"
        )

    def handle(self, *args, **options):
        start_value = options["start_value"]
        end_value = options["end_value"]
        sleep_time = options["sleep"]

        # If output filename is not specified, create one with timestamp
        if options.get("output"):
            output_file = options["output"]
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"processed_{timestamp}.json"

        base_search = "https://www.propertyfinder.ae/en/search?l=1&c=2&t=1&fu=0&rp=y&ob=nd&page=220"

        # Setup session with headers and cookies
        session = requests.Session()
        session.headers.update(PF_PARSER_CONFIG.get("headers", {}))
        session.cookies.update(PF_PARSER_CONFIG.get("cookies", {}))

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting property scraping from page {start_value} to {end_value}..."
            )
        )

        # Process everything in one go directly to output file
        self.extract_and_process_to_file(
            session=session,
            base_url=base_search,
            start_page=start_value,
            end_page=end_value,
            output_file=output_file,
            sleep_time=sleep_time,
        )

        self.stdout.write(
            self.style.SUCCESS(f"All processing complete! Output: {output_file}")
        )

    def build_page_url(self, base_url, page_num):
        """Create URL for specific page number."""
        if "page=" in base_url:
            return re.sub(r"page=\d+", f"page={page_num}", base_url)
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}page={page_num}"

    def extract_links_from_page(self, html):
        """Extract property links from search results page."""
        soup = BeautifulSoup(html, "lxml")
        section = soup.select_one("[aria-label='Properties']")
        if not section:
            return []
        return [
            a["href"]
            for a in section.select("[data-testid='property-card-link']")
            if a.has_attr("href")
        ]

    def extract_first_script(self, html):
        """Extract JSON data from the first script tag."""
        soup = BeautifulSoup(html, "lxml")
        script = soup.body.find("script")
        text = script.string or ""
        idx = text.find("{")
        return text[idx:] if idx >= 0 else ""

    def transform_property(self, data):
        """Transform raw property data to structured format."""
        prop = (
            data.get("props", {})
            .get("pageProps", {})
            .get("propertyResult", {})
            .get("property", {})
        )

        if not prop:
            return None

        # Extract basic details
        property_id = prop.get("id")
        url = prop.get("share_url")
        title = prop.get("title")
        display_address = prop.get("location", {}).get("full_name")
        bedrooms = prop.get("bedrooms")
        bathrooms = prop.get("bathrooms")
        added_on = prop.get("listed_date")

        # Agent and broker info
        broker_name = prop.get("broker", {}).get("name")
        agent_name = prop.get("agent", {}).get("name")
        agent_info = prop.get("agent", {})
        broker_info = prop.get("broker", {})
        broker_license = prop.get("broker", {}).get("license_number")

        # Extract agent phone
        agent_phone = None
        for c in prop.get("contact_options", []):
            if c.get("type") == "phone":
                agent_phone = c.get("value")
                break

        # Property verification
        verified = prop.get("is_verified")
        reference = prop.get("reference")

        # Price details
        price_duration = "rent" if prop.get("isRent") else "sell"
        property_type = prop.get("property_type")
        price = prop.get("price", {}).get("value")
        price_currency = prop.get("price", {}).get("currency")

        # RERA details
        rera_obj = prop.get("rera", {}) or {}
        rera_number = rera_obj.get("number") if isinstance(rera_obj, dict) else None
        rera_permit_url = (
            rera_obj.get("permit_validation_url")
            if isinstance(rera_obj, dict)
            else None
        )

        # Location
        coord = prop.get("location", {}).get("coordinates", {}) or {}
        coordinates = {
            "latitude": coord.get("lat"),
            "longitude": coord.get("lon"),
        }

        # Property features
        offering_type = prop.get("offering_type")
        size_val = prop.get("size", {}).get("value")
        size_unit = prop.get("size", {}).get("unit")
        size_min = f"{size_val} {size_unit}" if size_val and size_unit else None
        furnishing = prop.get("furnished", "NO").upper()

        # Amenities and features
        features = [a.get("name") for a in prop.get("amenities", []) if a.get("name")]

        # Description
        description = prop.get("description")
        description_html = prop.get("descriptionHTML") or description

        # Images
        images = [
            img.get("full")
            for img in prop.get("images", {}).get("property", [])
            if img.get("full")
        ]

        similar_transactions = prop.get("similar_price_transactions")

        # Return structured data
        return {
            "id": property_id,
            "url": url,
            "title": title,
            "displayAddress": display_address,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "addedOn": added_on,
            "broker": broker_name,
            "agent": agent_name,
            "agentInfo": agent_info,
            "agentPhone": agent_phone,
            "verified": verified,
            "reference": reference,
            "brokerLicenseNumber": broker_license,
            "brokerInfo": broker_info,
            "priceDuration": price_duration,
            "propertyType": property_type,
            "price": price,
            "rera": rera_number,
            "priceCurrency": price_currency,
            "coordinates": coordinates,
            "type": offering_type,
            "sizeMin": size_min,
            "furnishing": furnishing,
            "features": features,
            "description": description,
            "descriptionHTML": description_html,
            "images": images,
            "similarTransactions": similar_transactions,
            "reraPermitUrl": rera_permit_url,
        }

    def extract_and_process_to_file(
        self, session, base_url, start_page, end_page, output_file, sleep_time
    ):
        """
        Streamlined process: Extract property links, scrape data, transform, and
        write directly to final JSON file all in one process without temp files.
        """
        # Use a set to track unique property IDs
        seen_ids = set()
        # A list to store all processed properties
        all_properties = []

        # First gather all property links from search pages
        self.stdout.write("Gathering property links...")
        all_links = set()

        for page in range(start_page, end_page + 1):
            url = self.build_page_url(base_url, page)
            self.stdout.write(f"Fetching page {page}: {url}")

            try:
                response = session.get(url)
                response.raise_for_status()

                links = self.extract_links_from_page(response.text)
                if not links:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No links found on page {page}, stopping link collection."
                        )
                    )
                    break

                all_links.update(links)
                self.stdout.write(
                    f"Found {len(links)} links on page {page}, total unique links: {len(all_links)}"
                )

                # Sleep to avoid rate limiting
                time.sleep(sleep_time)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error accessing page {page}: {e}"))

        # Process each property link directly
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting to process {len(all_links)} property pages..."
            )
        )

        for idx, link in enumerate(sorted(all_links), 1):
            self.stdout.write(f"Processing ({idx}/{len(all_links)}): {link}")

            try:
                # Get property page
                response = session.get(link)
                response.raise_for_status()

                # Extract JSON data
                script_text = self.extract_first_script(response.text)
                if not script_text:
                    self.stdout.write(
                        self.style.WARNING(f"No data found for {link}, skipping")
                    )
                    continue

                # Parse JSON data
                try:
                    data = json.loads(script_text)
                except json.JSONDecodeError:
                    self.stdout.write(
                        self.style.ERROR(f"Invalid JSON data from {link}, skipping")
                    )
                    continue

                # Transform data to structured format
                property_data = self.transform_property(data)
                if not property_data:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not transform data from {link}, skipping"
                        )
                    )
                    continue

                # Check for duplicate property IDs
                property_id = property_data.get("id")
                if property_id and property_id in seen_ids:
                    self.stdout.write(f"Skipping duplicate property ID: {property_id}")
                    continue

                if property_id:
                    seen_ids.add(property_id)

                # Add to our collection
                all_properties.append(property_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added property '{property_data.get('title')}' ({len(all_properties)} total)"
                    )
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {link}: {e}"))

            # Sleep to avoid rate limiting
            time.sleep(sleep_time)

        # Write all properties to the final JSON file
        self.stdout.write(f"Writing {len(all_properties)} properties to {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_properties, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(all_properties)} unique properties"
            )
        )


PF_PARSER_CONFIG = {
    "mp_name": "pf",
    "is_rent": False,
    "search_error_message": "Ooops! You weren't supposed to see this",
    "search_page_max_count": 3000,
    "start_page": "https://www.propertyfinder.ae/",
    "search_postfix": "en/search?l=1&c=2&t=1&fu=0&rp=y&ob=nd&page=220",
    "sub_pages": {
        "property_type": {"Apartment": "t=1"},
        "buy_deal_type": {"off-plan": "cs=off_plan", "ready": "cs=completed"},
    },
    "cookies": {
        "flagship_user_id": "5p1z46z0gt7vhrwxo2047k",
        "website_ab_tests": "TOGGLE_HEADER_COMMUNITIES_ENTRYPOINT=off,TEST_LIMIT_SAVE_SEARCH=original,SEARCH_CREATE_ALERT_FLOW=variantA,TEST_SERP_WHATSAPP_CAPTCHA=variantA,TEST_PLP_WHATSAPP_CAPTCHA=variantA,TEST_AGENT_WHATSAPP_CAPTCHA=variantA,TEST_PRIMARY_TOP_BAR=off,TEST_AGENT_LEAD_WHATSAPP_CAPTCHA=original,TESTS_SEARCH_NO_COUNTRY_POD=original,TEST_PLP_TO_PDP=variantB,TEST_PLP_RENT_VS_BUY=variantA,TEST_HOMEPAGE_BANNER=variantA,TEST_PLP_FLOOR_PLANS_ENABLED=original,TEST_SEARCH_NP_SORT=variantA,TEST_PRIMARY_SCARCITY=original,TEST_PLP_NO_COUNTRY_POD=original,TEST_NP_NO_COUNTRY_POD=original,TEST_PLP_RECOMMENDATIONS=original,TEST_AGENT_INFO_STICKY=original,TEST_NEW_PROJECT_CARDS=variantA,TEST_NP_CATEGORY_NEW_TAG=variantA,TEST_HOMEPAGE_HOT_PROJECTS=variantA,NEW_PROJECTS_CAROUSEL=original,TEST_HOME_NO_COUNTRY_POD=original,TEST_PLP_NAVIGATION=variantA,TEST_SERP_CARAT=variantB,TEST_NP_IN_NAVIGATION=original,TEST_PRIMARY_STOCK_STATUS=variantA,TOGGLE_BOTTOM_NAVIGATION_ONBOARDING_ENABLED=off,TOGGLE_BOTTOM_NAVIGATION_ENABLED=off,TEST_BOTTOM_NAVIGATION_EGYPT=original,TEST_PRIMARY_CTA=variantA,TEST_WHATSAPP_CAPTCHA=variantA,TEST_PLP_FRESHNESS=original,TEST_PLP_HISTORICAL_TRANSACTIONS=original,TEST_PLP_AGENT_REVIEW=variantA,SEARCH_HP_NP_CATEGORY=variantB,TEST_HOMEPAGE_CTA=variantA,TOGGLE_HEADER_INSIGHTSHUB_ENTRYPOINT=original,TEST_PLP_UPFRONT_COST=variantA,SEARCH_HOMEPAGE_NEW_PROJECTS_CATEGORY=original,TEST_PLP_PRICE_POSITION=variantA,TEST_PLP_DATAGURU_ENTRYPOINTS=variantA,TEST_SERP_DYNAMIC_RANKING=variantA,TEST_PLP_NEW_CTA=variantA,NP-534-new-projects-nav-label=original,TOGGLE_TOWERINSIGHTS_FLOORPLANS=original,WEBSITE_PLP_PROJECT_LINK=original,serpDownPaymentEgp=original,test136=variantA",
        "anonymous_user_id": "5p1z46z0gt7vhrwxo2047k",
        "lux_uid": "173125380218613715",
        "_sp_ses.b9c1": "*",
        "consentGroup": "control",
        "cookie_for_measurement_id": "G-WC7F61HJCT",
        "_ga": "GA1.1.293419823.1731253803",
        "criteo_user_id": "F8Z_419XeTBUMUxoJTJGQXN1cThPbWtUeXpoWFRvNUpjc0JPcllDRVVBVyUyRk13b3BKdyUzRA",
        "_gcl_au": "1.1.468435590.1731253803",
        "_scid": "zYSE8Ri_iObCx_axhpVvR9iZQHw7sWNX",
        "_cq_duid": "1.1731253803.XK339FeBUmzZm5wf",
        "_cq_suid": "1.1731253803.rsaryiSOK3U8tdsz",
        "_ScCbts": "%5B%5D",
        "_clck": "1nhhbmw%7C2%7Cfqr%7C0%7C1775",
        "_sctr": "1%7C1731186000000",
        "ab.storage.deviceId.cbd8e26c-0129-41bb-a086-d0eadb922300": "g%3A66da7772-3c6b-ce55-cd44-072f0806c5f2%7Ce%3Aundefined%7Cc%3A1731253805899%7Cl%3A1731253805899",
        "sp": "740bdc9e-9a1d-4ca4-9234-6d1b20b4844f",
        "ab.storage.sessionId.cbd8e26c-0129-41bb-a086-d0eadb922300": "g%3A66241c0d-fd51-f6f6-afea-dc6970482245%7Ce%3A1731256592642%7Cc%3A1731253805897%7Cl%3A1731254792642",
        "_ga_4XL587PN9G": "GS1.1.1731253802.1.1.1731254792.10.0.63898674",
        "_scid_r": "3QSE8Ri_iObCx_axhpVvR9iZQHw7sWNXQY18jQ",
        "_clsk": "1cy6at8%7C1731254795398%7C10%7C1%7Cu.clarity.ms%2Fcollect",
        "cto_bundle": "kawdrl80ZEtaNDlYQ2RTJTJGN2h2NnltOHdDa3luOHRiRCUyQnRDOGdhOE5tQ0pMckVhSklwa1BtZkVnVjIzUVZpZmRBRUIzekN0Y0x4OXlCb3NONVJod01PSWVCc2Q5d0xMZ1dIdldINkFCT1VDZ09FRmNqRzdtQXI3WnhodzNYa2E5Q2tJQnJOenFkUFk1d1pkT0E5RVUwRmMyaEtLSDJyaGNRekpkOVlGdkNtYllqR0Zhem1XZVdDbUc3SjN0Y0t3WDMzc1p3b0YyelZLRUgzb201UVBPaFIwaUVQZyUzRCUzRA",
        "aws-waf-token": "3bf0f076-a614-47e3-beb0-2e3265cf531c:BgoAZdNxL8UCAAAA:Ls0t16poLrn/rydvJEk6ZFg7q5KJV5JEbhpF+9Ni2ogEP6Ld0swatL3hHvg5d/C++WqeDReGHVIhGSEh1zrCyPcEXy3aKsfkDQS9nKdZs8ZfCPgkBVDidMHankcm8mNKVy8CJvlNs44EXWqhLjReCml6ffDbX8xHLF3JO2snBFFv2jmkYTDIBBUYidbatYQ3rVAbjCvOyesiffH7RHF95aRQQ4UsnAwpeOV9EJ9vEKPGkXD4Feg5ScAAUfxuaYblOVNNps9IdzKvcl1K",
        "utag_main": "v_id:019316c495a900594f5ec377e19405065003405d00bd0$_sn:1$_se:169$_ss:0$_st:1731256598971$ses_id:1731253802410%3Bexp-session$_pn:9%3Bexp-session$dc_visit:1$dc_event:12%3Bexp-session$dc_region:eu-west-1%3Bexp-session$user_phone_number_formatted_for_fb:",
        "_ga_WC7F61HJCT": "GS1.1.1731253802.1.1.1731254798.53.0.1035552191",
        "_dd_s": "logs=1&id=7b7a0ccb-0760-40a9-8756-8bb1af848be3&created=1731253802254&expire=1731255701236",
        "_sp_id.b9c1": "1b5f6bc1-2943-4fd5-be5b-47ba7d7b37b3.1731253802.1.1731254801..0d22dfd6-db03-40a6-89bc-d6b8eb599671..f2f8ef14-2c2d-42d0-a58b-ea2597f7ddcc.1731253802222.305",
    },
    "headers": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=0, i",
        "referer": "Page 220: https://www.propertyfinder.ae/en/search?l=1&c=2&t=1&fu=0&rp=y&ob=nd&page=220",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    },
}
