"""
ARCHub main module
----
"""
import sys
sys.path.append('/home/pi/Desktop/anti-iha_haberlesme')
sys.path.append('/home/pi/Desktop/anti-iha_haberlesme/venv/Lib/site-packages/')
from ArcMavRouter.ARCHub.PipeInput import PipeInput
from ArcMavRouter.ARCHub.PipeOutput import PipeOutput
from pymavlink import mavutil
import threading
import time
import select
import sys

"""
Hub Element Class.
----
"""
class HubElement():
    def __init__(self, name=None, type=None, address=None, baudrate=57600, source=None, buffer_size=None, period=0.1, radio_buffer_size=None):
        """
        Constructor of HubElement

            :param String name: Name of the element
            :param String type: Type of element
                                 - "autopilot" for autopilot connection (master mode)
                                 - "serial" for serial connection
                                 - "socket" for socket connection
            :param String address: Connection address (serial or socket)
            :param int baudrate: Baudrate of connection
                                  Default value is None. Set this parameter if only
                                  the connection is a Serial conn.

        """
        self.name = name
        self.type = type
        self.address = address
        self.rate = baudrate
        self.connection = None
        self.source = source
        self.buff_size = buffer_size
        self.period = period
        self.radio_buff = radio_buffer_size
        self.sysid_list = {}

        self.createConnectionObj()
        self.limiter = SendLimiter(self.buff_size, self.radio_buff, self.period, self.connection)

    def createConnectionObj(self):
        """
        Connection creation function
            Creates connection property based on HubElement type.
        """

        try:
            if self.type == "socket":
                self.connection = mavutil.mavudp(self.address, input=False)

                # self.connection = mavutil.mavlink_connection(self.address, autoreconnect=True,
                #                                         baud=self.rate,
                #                                         force_connected=False)
            elif self.type == "socket_input":
                self.connection = mavutil.mavudp(self.address, input=True)
            elif self.type == "autopilot":
                self.connection = mavutil.mavlink_connection(self.address, autoreconnect=True,
                                                             baud=self.rate,
                                                             force_connected=False)
            else:
                self.connection = mavutil.mavlink_connection(self.address, baud=self.rate, autoreconnect=True)

        except Exception as e:
            print("[ERROR] {} connection can't available. Error: {}".format(self.name, e))


"""
Hub Pipeline Class.
"""
class HubPipe():
    def __init__(self, name, input, outputs, msg_filter, targets_to_be_filtered):
        """
        Constructor of HubPipe

            :param String name: Name of the pipe
            :param HubElement input: Source element of the pipe
            :param list outputs: List of targets

            :NOTE outputs argument must be in list format.
            Example: pipe1 = hub.addPipe(name="autopilot_main_pipe", input=autopilot,
                    outputs=[mplanner, dk_object])

        """
        self.name = name
        self.input = input
        self.outputs = outputs
        self.msg_filter = msg_filter
        self.targets_to_be_filtered = targets_to_be_filtered


class HubPipelineConnector():
    """
    Pipeline connector class
        Creates callback relation between PipeInput and PipeOutput objects.
    """
    def __init__(self):
        """
        Constructor of HubPipelineConnector.
        """
        self._newMsgs = None

        self.newMsgs_observers = []

    def updateCurrentMsg(self, msgs):
        """
        Update function for newMsgs property.
        """
        try:
            self.newMsgs = msgs
        except:
            print('ERR: Received msgs cannot be updated.')

    @property
    def newMsgs(self):
        """
        Definition of property decorator for newMsgs.
        """
        return self._newMsgs

    @newMsgs.setter
    def newMsgs(self, value):
        """
        Setter function.
            newMsgs changing sends notify to subscribers
        """
        self._newMsgs = value
        for callback in self.newMsgs_observers:
            # print("Msgs Change")
            callback(self._newMsgs)

    def bindToNewMsgs(self, callback):
        """
        Binding callback to observers.
        """
        self.newMsgs_observers.append(callback)

class SendLimiter():

    def __init__(self, buffer_size_limit, radio_buffer_size_limit, period, connect):

        self.buff = b''

        self.buff_size_limit = buffer_size_limit
        self.radio_buff_size_limit = radio_buffer_size_limit
        self.period = period
        self.connect = connect

        if self.buff_size_limit != None:
            self.limiter()

    def limiter(self):

        if self.buff != b'':
            buff_object = self.connect.mav.parse_buffer(self.buff)
            if buff_object != None:

                send_msg = b''

                for msg in buff_object:
                    mtype = msg.get_type()

                    if mtype !="BAD_DATA":

                        mbuf = msg.get_msgbuf()

                        if sys.getsizeof(send_msg) - 33 < self.radio_buff_size_limit:

                            send_msg = send_msg + mbuf
                    else:
                        self.buff = self.buff[1:]
                #print(send_msg)
                self.connect.write(send_msg)
                self.buff = self.buff[len(send_msg):]

        threading.Timer(self.period, self.limiter).start()



"""
Main Hub Class.
"""
class HubMain():
    def __init__(self):
        """
        Constructor of HubMain
        """
        self.element_list = []
        self.pipeline_list = []

    def addElement(self, name=None, type=None, address=None, baudrate=57600, source=None, buffer_size=None, period=None, radio_buffer_size=None):
        """
        Add Element function.
            Adds new connection objects to the Hub with defined properties.

            :param String name: Name of the element
            :param String type: Type of element
                                 - "autopilot" for autopilot connection (master mode)
                                 - "serial" for serial connection
                                 - "socket" for socket connection
            :param String address: Connection address (serial or socket)
            :param int baudrate: Baudrate of connection
                                  Default value is None. Set this parameter if only
                                  the connection is a Serial conn.
            :return HubElement element: HubElement object
        """
        element = HubElement(name, type, address, baudrate, source, buffer_size, period, radio_buffer_size)
        self.element_list.append(element)
        print(element.connection.fd)
        return element

    def addPipe(self, name, input, outputs, msg_filter, targets_to_be_filtered):
        """
        Add pipe to hub.
            Adds new pipe with given hub elements
            :param String name: Name of the pipe
            :param HubElement input: Source element of the pipe
            :param list outputs: List of hub element targets
                                outputs argument must be in list format.
                                Example: pipe1 = hub.addPipe(name="autopilot_main_pipe", input=autopilot,
                                outputs=[mplanner, dk_object])

            :return HubPipe pipe: HubPipe object
        """
        pipe = HubPipe(name, input, outputs, msg_filter, targets_to_be_filtered)
        self.pipeline_list.append(pipe)
        return pipe

    def initialize_pipes(self):
        """
        Pipeline initializer.
            Creates connector objects which connects input and outputs.
            Starts source reading threads.
        """


        for pipe in self.pipeline_list:
            hub_pipe_connector = HubPipelineConnector()
            source_receiver = PipeInput(hub_pipe_connector, pipe.input)
            targets_sender = PipeOutput(hub_pipe_connector, pipe.outputs,
                                        pipe.msg_filter, pipe.targets_to_be_filtered)
            source_receiver.start()
            time.sleep(0.25)





