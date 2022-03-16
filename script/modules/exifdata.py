#
import datetime
import string
import time
import globals
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS
from modules import ilmodule

#
# This class is used to extract the EXIF/GPS data from an image file
#
# More at https://developer.here.com/blog/getting-started-with-geocoding-exif-image-metadata-in-python3
#
class ExifDataExtractor(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        self.printable = set(string.printable)
        self.getMessageBus().subscribe(self.onMessageExif, globals.TOPIC_EXIF)
        self.getMessageBus().subscribe(self.onMessageGps, globals.TOPIC_GPS)

    def onMessageExif(self, arg):
        sourceFile = arg["image_path"]
        self.log.debug("Reading EXIF data from: " + sourceFile)

        imageExif = self.get_exif(sourceFile)
        processedExifData = self.get_labeled_exif(imageExif)

        keysToDelete = ["GPSInfo"]
        # Cleanup unnecessary keys
        for key in keysToDelete:
            if key in processedExifData:
                del processedExifData[key]

        arg["EXIF"] = processedExifData

        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        print(arg)

    def onMessageGps(self, arg):
        self.getImageGPSData(arg)

    def get_decimal_from_dms(self, dms, ref):
        degrees = dms[0]
        minutes = dms[1] / 60.0
        seconds = dms[2] / 3600.0

        if ref in ["S", "W"]:
            degrees = -degrees
            minutes = -minutes
            seconds = -seconds

        return round(degrees + minutes + seconds, 5)

    def get_geotagging(self, exif):
        geotagging = {}

        if not exif:
            self.log.warning("No EXIF metadata found")
            return geotagging

        for (idx, tag) in TAGS.items():
            if tag == "GPSInfo":
                if idx not in exif:
                    self.log.warning("No EXIF geotagging found")
                    return geotagging

                for (key, val) in GPSTAGS.items():
                    if key in exif[idx]:
                        geotagging[val] = exif[idx][key]

        # Post-process latitude and longitude data: ##################
        if "GPSLatitude" in geotagging and geotagging["GPSLatitude"] is not None:
            lat = self.get_decimal_from_dms(
                geotagging["GPSLatitude"], geotagging["GPSLatitudeRef"]
            )
            # Set human-readable latitude
            geotagging["GPSLatitude"] = str(lat)
        else:
            geotagging["GPSLatitude"] = None

        if "GPSLongitude" in geotagging and geotagging["GPSLongitude"] is not None:
            lon = self.get_decimal_from_dms(
                geotagging["GPSLongitude"], geotagging["GPSLongitudeRef"]
            )
            # Set human-readable longitude
            geotagging["GPSLongitude"] = str(lon)
        else:
            geotagging["GPSLongitude"] = None

        # Construct time from tuple (h, m,s):
        if "GPSTimeStamp" in geotagging and geotagging["GPSTimeStamp"] is not None:
            geotagging["GPSTimeStamp"] = str(
                datetime.time(
                    int(geotagging["GPSTimeStamp"][0]),
                    int(geotagging["GPSTimeStamp"][1]),
                    int(geotagging["GPSTimeStamp"][2]),
                )
            )
        else:
            geotagging["GPSTimeStamp"] = None

        if "GPSAltitude" in geotagging and geotagging["GPSAltitude"] is not None:
            geotagging["GPSAltitude"] = str(geotagging["GPSAltitude"])
        else:
            geotagging["GPSAltitude"] = None

        return geotagging

    def get_exif(self, filename):
        image = Image.open(filename)
        image.verify()
        return image._getexif()

    # Check if string is bytes and decode if needed return as is otherwise:
    def leaveOnlyRealString(self, string):
        if isinstance(string, bytes):
            return ""
        else:
            return string

    def get_labeled_exif(self, exif):
        labeled = {}

        if exif:
            for (key, val) in exif.items():
                labeled[TAGS.get(key)] = (
                    str(self.leaveOnlyRealString(val)).strip().rstrip("\x00")
                )

        # Delete "MakerNote" - May contain invalid symbols
        if "MakerNote" in labeled:
            del labeled["MakerNote"]

        return labeled

    def getImageGPSData(self, image_data):
        sourceFile = image_data["image_path"]
        self.log.debug("Reading GPS data from: " + sourceFile)

        gpsdata = {}
        try:
            exif = self.get_exif(sourceFile)
            gpsdata = self.get_geotagging(exif)

            neededGpsDataKeys = [
                "GPSLatitudeRef",
                "GPSLatitude",
                "GPSLongitudeRef",
                "GPSLongitude",
                "GPSAltitude",
                "GPSTimeStamp",
                "GPSDateStamp",
            ]
            # Keep only needed keys:
            gpsdata = {key: gpsdata[key] for key in neededGpsDataKeys if key in gpsdata}

            image_data["gps"] = gpsdata

        except:
            self.log.error("Error reading image data")
            self.log.warn("Proceeding with EMPTY EXIF/GPS data")
        finally:
            self.getMessageBus().sendMessage(globals.TOPIC_EXIF, arg=image_data)
