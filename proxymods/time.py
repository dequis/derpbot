import packets
from util import bind_as_filter

@bind_as_filter
def faster_time(self, header, payload, target):
    if header == packets.packets_by_name['time']:
        newdata = packets.make_packet(header, {'timestamp': payload.timestamp * 30})
        target.send(newdata)
        self.stop_relay()

#if header == packets.packets_by_name['chunk']:
#    chunkfile = open("chunk/chunk_%s_%s_%s.dat.gz" % (payload.x, payload.y, payload.z), "wb")
#    chunkfile.write(payload.data)
#    print "got chunk"
