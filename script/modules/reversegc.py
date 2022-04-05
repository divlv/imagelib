import json
import requests
import time
import codecs
import re
import globals
from modules import ilmodule
from unicodedata import normalize

#
# This class is used to extract City, street, etc. name from GPS coordinates
#
#
class ReverseGeoCoder(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        self.punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')
        self.reverseGeoCodingUrlTemplate = "https://nominatim.openstreetmap.org/reverse?&accept-language=en&format=json&lat=%s&lon=%s&zoom=18&addressdetails=1"
        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_REVERSE_GEO)

    def onMessage(self, arg):
        self.getLogger().debug("Received message: " + str(arg))
        # Prevent too many requests to the API
        self.getLogger().debug(
            "Prevent too many requests to the API. Waiting for 1 seconds..."
        )
        time.sleep(1)
        self.getAddressByGPS(arg)

    def deaccent(self, text, delim=" "):
        """Generates an slightly worse ASCII-only slug."""
        result = []
        for word in self.punct_re.split(text.lower()):
            word = normalize("NFKD", word).encode("ascii", "ignore")
            word = word.decode("utf-8")
            if word:
                result.append(word)
        return delim.join(result)

    def cleanhtml(self, raw_html):
        cleanr = re.compile("<.*?>")
        cleantext = re.sub(cleanr, "", raw_html)
        return cleantext

    def unmangle_utf8(self, match):
        escaped = match.group(0)  # '\\u00e2\\u0082\\u00ac'
        hexstr = escaped.replace(r"\u00", "")  # 'e282ac'
        buffer = codecs.decode(hexstr, "hex")  # b'\xe2\x82\xac'

        try:
            return buffer.decode("utf8")  # '€'
        except UnicodeDecodeError:
            print("Could not decode buffer: %s" % buffer)

    def getAddressByGPS(self, image_data):

        # print(image_data)
        # Check "gps" key in the image_data
        latitude = ""
        longitude = ""
        
        if "gps" in image_data and "GPSLatitude" in image_data["gps"] and "GPSLongitude" in image_data["gps"]:
            latitude = image_data["gps"]["GPSLatitude"]
            longitude = image_data["gps"]["GPSLongitude"]

        if not latitude or not longitude:
            self.getLogger().debug("No GPS data found in image")
        else:
            self.getLogger().debug(
                "Called ReverseGeoCoder.getAddressByGPS(%s, %s)" % (latitude, longitude)
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
            }
            url = self.reverseGeoCodingUrlTemplate % (latitude, longitude)

            response = requests.get(url, headers=headers)

            if response.status_code == self.HTTP_OK:
                self.getLogger().debug("Response.text: " + response.text)

                nominatim = json.loads(response.text)

                address = {}
                if "address" in nominatim:
                    address = nominatim["address"]

                display_name = ""
                if "display_name" in nominatim:
                    display_name = nominatim["display_name"]

                image_data["address"] = address
                image_data["display_name"] = display_name

            else:
                self.getLogger().error(
                    "Cannot get data from Nominatim. Error response code: "
                    + str(response.status_code)
                )

        self.getMessageBus().sendMessage(globals.TOPIC_TEXT, arg=image_data)
