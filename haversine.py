import math


def calcul_de_l_haversine(lat1: float, lat2: float, long1:float, long2: float):

    R = 6371.0

    rad_lat1 = math.radians(lat1)
    rad_lat2 = math.radians(lat2)
    rad_long1 = math.radians(long1)
    rad_long2 = math.radians(long2)

    dlat = math.radians(rad_lat2 - rad_lat1)
    dlong = math.radians(rad_long2 - rad_long1)

    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlong / 2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = R * c

    return round(distance, 2)
