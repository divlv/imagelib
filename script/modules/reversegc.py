import json
import requests
import codecs
import re
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

    def getAddressByGPS(self, latitude, longitude) -> json:
        self.log.debug(
            "Called ReverseGeoCoder.getAddressByGPS(%s, %s)" % (latitude, longitude)
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        }
        url = self.reverseGeoCodingUrlTemplate % (latitude, longitude)

        response = requests.get(url, headers=headers)

        if response.status_code == self.HTTP_OK:
            self.log.debug("Response.text: " + response.text)
            return json.loads(response.text)
        else:
            self.log.error(
                "Cannot get data from Nominatim. Error response code: "
                + str(response.status_code)
            )
            return {}
