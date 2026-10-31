import os
import re
import html
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED_URL = "https://learningenglish.voanews.com/podcast/?zoneId=987"
download_dir = "voa_2025_extracted"
zip_filename = "voa_words_stories_2025.zip"
os.makedirs(download_dir, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()

def extract_transcript(page_html, description):
    """Best-effort: pull the transcript from the episode page; fall back to the RSS summary."""
    text = page_html.decode("utf-8", errors="replace") if page_html else ""

    # VOA lesson pages mark the transcript with a heading like "Transcript"
    m = re.search(r'(?is)Transcript.*?</h[1-4]>(.*?)</section>', text)
    if not m:
        m = re.search(r'(?is)<div[^>]*class="[^"]*transcript[^"]*"[^>]*>(.*?)</div>', text)
    if m:
        chunk = m.group(1)
        chunk = re.sub(r"(?s)<script.*?</script>", "", chunk)
        chunk = re.sub(r"(?s)<style.*?</style>", "", chunk)
        chunk = re.sub(r"<br\s*/?>", "\n", chunk)
        chunk = re.sub(r"</p>", "\n\n", chunk)
        chunk = re.sub(r"<[^>]+>", "", chunk)
        chunk = html.unescape(chunk)
        lines = [ln.strip() for ln in chunk.splitlines()]
        body = "\n".join(ln for ln in lines if ln)
        if len(body) > 200:  # sanity check — avoid grabbing nav junk
            return body

    # Fallback: RSS description summary
    return html.unescape(re.sub(r"<[^>]*>", "", description or ""))

print("Connecting to VOA Learning English RSS database...")
try:
    xml_data = fetch_url(FEED_URL)
except Exception as e:
    print(f"Error accessing VOA Feed: {e}")
    raise SystemExit(1)

root = ET.fromstring(xml_data)
episodes_compiled = 0

print("Scanning for 2025 episodes...")
with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
    for item in root.findall(".//item"):
        # --- None-safe field extraction (the fix for your error) ---
        pub_date_el = item.find("pubDate")
        pub_date = (pub_date_el.text if pub_date_el is not None else "") or ""
        title_el = item.find("title")
        title = (title_el.text if title_el is not None else "") or "Untitled_Episode"
        desc_el = item.find("description")
        description = (desc_el.text if desc_el is not None else "") or ""
        link_el = item.find("link")
        page_url = (link_el.text if link_el is not None else "") or ""

        # --- Filter for 2025 episodes ---
        try:
            year = parsedate_to_datetime(pub_date).year
        except (TypeError, ValueError):
            continue
        if year != 2025:
            continue

        enclosure = item.find("enclosure")
        if enclosure is None or "url" not in enclosure.attrib:
            continue
        mp3_url = enclosure.attrib["url"]

        clean_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
        mp3_filename = os.path.join(download_dir, f"{clean_title}.mp3")
        txt_filename = os.path.join(download_dir, f"{clean_title}_transcript.txt")

        print(f"\nProcessing [2025]: {title}")

        # 1. Download and package the MP3 audio
        try:
            print(" -> Downloading Audio (MP3)...")
            urllib.request.urlretrieve(mp3_url, mp3_filename)
            zipf.write(mp3_filename, os.path.basename(mp3_filename))
            os.remove(mp3_filename)
        except Exception as e:
            print(f" -> Audio Download Failed: {e}")
            continue

        # 2. Fetch transcript from episode page (fallback to summary)
        try:
            print(" -> Extracting Transcript...")
            if page_url:
                page_html = fetch_url(page_url)
                transcript = extract_transcript(page_html, description)
            else:
                transcript = extract_transcript("", description)

            with open(txt_filename, "w", encoding="utf-8") as txt_file:
                txt_file.write(f"Title: {title}\n")
                txt_file.write(f"Published: {pub_date}\n")
                txt_file.write(f"Source URL: {page_url}\n")
                txt_file.write("=" * 40 + "\n\n")
                txt_file.write(transcript)

            zipf.write(txt_filename, os.path.basename(txt_filename))
            os.remove(txt_filename)
        except Exception as e:
            print(f" -> Transcript Compilation Failed: {e}")

        episodes_compiled += 1

try:
    os.rmdir(download_dir)
except OSError:
    pass

print("\n" + "=" * 40)
print(f"Task Complete! {episodes_compiled} total 2025 episodes compressed into '{zip_filename}'.")
print("=" * 40)