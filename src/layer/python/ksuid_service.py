import uuid

def uuid6(*args, **kwargs):
    uh = uuid.uuid1(*args, **kwargs).hex
    tlo1 = uh[:5]
    tlo2 = uh[5:8]
    tmid = uh[8:12]
    thig = uh[13:16]
    rest = uh[16:]
    uh6 = thig + tmid + tlo1 + '6' + tlo2 + rest
    return uuid.UUID(hex=uh6)

def generate_ksuid():
    x = uuid6()
    return x