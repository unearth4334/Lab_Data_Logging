from data_logger import *

logger = data_logger()
multimeter = logger.connect("KeithleyDMM6500")

print(multimeter.get("statistics"))