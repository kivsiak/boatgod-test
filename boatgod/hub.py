import aiopubsub

hub = aiopubsub.Hub()

canbus_publisher = aiopubsub.Publisher(hub, prefix=aiopubsub.Key("canbus"))
lora_publisher = aiopubsub.Publisher(hub, prefix=aiopubsub.Key("lora"))
