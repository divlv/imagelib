#
from modules import ilmodule
import os
import re
import time
from time import mktime
from datetime import datetime
import json
import globals

#
# Try to determine the actual date of the picture. By metadata, filename, etc,
# Assuming all the EXIF data was already extracted previously.
# Place this step of processing - one of the latest (i.e. after EXIF, GPS, etc.)
#
class DateOfPicture(ilmodule.ILModule):
    def __init__(self):
        super().__init__()

        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_DATE)

    def onMessage(self, arg):
        self.getLogger().debug("Received topic date request: " + str(arg))
        metadata = self.findDateOfImage(arg)

        # metadata["text_en"] = ""
        # metadata["text_ru"] = ""

        # Json pretty print
        self.getLogger().info(json.dumps(metadata, indent=4))
        self.saveJsonToFile(
            json.dumps(metadata, indent=4),
            os.environ["TEMPORARY_DIR"] + "\\" + "json_" + arg["hash"] + ".json",
        )

        self.getMessageBus().sendMessage(globals.TOPIC_SAVEDB, arg=metadata)

    def loadJsonFromFile(self, filename):
        with open(filename, "r") as f:
            return json.load(f)

    def stringIsDateTime(self, str):
        try:
            time.strptime(str, "%Y:%m:%d %H:%M:%S")
            return True
        except ValueError:
            return False

    def stringIsDate(self, str):
        try:
            time.strptime(str, "%Y:%m:%d")
            return True
        except ValueError:
            return False

    def stringIsTime(self, str):
        try:
            time.strptime(str, "%H:%M:%S")
            return True
        except ValueError:
            return False

    def findDateOfImage(self, image_data):  # Getting the path to the image file.
        try:
            date_time = ""

            # if DateTimeOriginal is not available, use DateTime
            if "DateTimeOriginal" in image_data["EXIF"] and self.stringIsDateTime(
                str(image_data["EXIF"]["DateTimeOriginal"]).replace(": ", ":")
            ):
                date_time = str(image_data["EXIF"]["DateTimeOriginal"]).replace(
                    ": ", ":"
                )
            else:
                if "DateTime" in image_data["EXIF"] and self.stringIsDateTime(
                    str(image_data["EXIF"]["DateTime"]).replace(": ", ":")
                ):
                    date_time = str(image_data["EXIF"]["DateTime"]).replace(": ", ":")

            if date_time != "":
                image_data["dateOfImage"] = date_time
                return image_data

            gps_time = ""
            if "GPSTimeStamp" in image_data["gps"] and self.stringIsTime(
                str(image_data["gps"]["GPSTimeStamp"]).replace(": ", ":")
            ):
                gps_time = str(image_data["gps"]["GPSTimeStamp"]).replace(": ", ":")
            else:
                gps_time = "00:00:01"

            gps_date = ""
            if "GPSDateStamp" in image_data["gps"] and self.stringIsDate(
                str(image_data["gps"]["GPSDateStamp"]).replace(": ", ":")
            ):
                gps_date = str(image_data["gps"]["GPSDateStamp"]).replace(": ", ":")
            else:
                gps_date = ""

            # If there's no DATE - we're not interested in TIME.
            if gps_date != "":

                gps_date_parsed = datetime.fromtimestamp(
                    mktime(time.strptime(gps_date, "%Y:%m:%d"))
                ).date()

                gps_time_parsed = datetime.strptime(gps_time, "%H:%M:%S").time()

                gps_date_parsed = datetime.combine(gps_date_parsed, gps_time_parsed)

                image_data["dateOfImage"] = gps_date_parsed.strftime(
                    "%Y:%m:%d %H:%M:%S"
                )
                return image_data

            # If no date can be found in image_data, let's inspect the filename itself (the last hope)

            # fileName = image_data["image_path"]
            # If we work with OneDrive there's a filename in the input data,
            # local file has only HASH256 as filename...
            fileName = image_data["onedrive_file_name"]

            ################ TEMPORARY  FIX ##############################
            # if image_data["remote_id"] == "2506B8927FF3C181!20400":
            #     fileName = "2018-08-19 15-33-47.JPG"

            # if image_data["remote_id"] == "2506B8927FF3C181!20459":
            #     fileName = "2018-08-21 11-59-52.PNG"

            # if image_data["remote_id"] == "2506B8927FF3C181!20540":
            #     fileName = "2018-08-22 23-30-54.PNG"

            # if image_data["remote_id"] == "2506B8927FF3C181!20541":
            #     fileName = "2018-08-22 23-34-12.JPG"

            # if image_data["remote_id"] == "2506B8927FF3C181!20628":
            #     fileName = "2018-08-27 17-34-36.JPG"

            # if image_data["remote_id"] == "2506B8927FF3C181!20628":
            #     fileName = "2018-08-28 19-44-58.JPG"
            ################ TEMPORARY  FIX ##############################

            fullDateRegExp = re.search(
                "((19|20)\d\d)([\-\._/]*)(0[1-9]|1[012])([\-\._/]*)(0[1-9]|[12][0-9]|3[01])([\-\._/\s]*)(0[0-9]|1[1-9]|2[1-3])([\-\._/\s]*)(0[0-9]|[1-5][1-9])([\-\._/\s]*)(0[0-9]|[1-5][1-9])",
                fileName,
            )
            if fullDateRegExp:
                d = datetime(
                    int(fullDateRegExp.group(1)),
                    int(fullDateRegExp.group(4)),
                    int(fullDateRegExp.group(6)),
                    int(fullDateRegExp.group(8)),
                    int(fullDateRegExp.group(10)),
                    int(fullDateRegExp.group(12)),
                )
                image_data["dateOfImage"] = d.strftime("%Y:%m:%d %H:%M:%S")
                return image_data

            dateOnlyRegExp = re.search(
                "((19|20)\d\d)([\-\._/]*)(0[1-9]|1[012])([\-\._/]*)(0[1-9]|[12][0-9]|3[01])",
                fileName,
            )
            if dateOnlyRegExp:
                d = datetime(
                    int(dateOnlyRegExp.group(1)),
                    int(dateOnlyRegExp.group(4)),
                    int(dateOnlyRegExp.group(6)),
                    0,
                    0,
                    1,
                )
                image_data["dateOfImage"] = d.strftime("%Y:%m:%d %H:%M:%S")
                return image_data
            else:
                self.getLogger().warning(
                    "No DATE information found in picture file: "
                    + str(fileName)
                    + " Returning default date - 1970:01:01 00:00:00"
                )
                image_data["dateOfImage"] = "1970:01:01 00:00:00"
                return image_data

        except Exception as e:
            self.getLogger().error(str(e))
        finally:
            self.cleanupTmp()
