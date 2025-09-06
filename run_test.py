from data_logger import *

logger = data_logger()
multimeter = logger.connect("DMM6500")

print(multimeter.get("resistance"))