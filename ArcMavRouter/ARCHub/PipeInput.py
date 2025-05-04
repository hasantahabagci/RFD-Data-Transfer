import sys
sys.path.append('/home/pi/Desktop/anti-iha_haberlesme')
sys.path.append('/home/pi/Desktop/anti-iha_haberlesme/venv/Lib/site-packages/')
import threading
from queue import Queue

import time
import select
import sys

import datetime
"""
PipeInput Class.
"""

bas = time.time()
class PipeInput():

    def __init__(self, hub_pipe_connector, source):
        """
        Constructor of PipeInput.

        :param HubPipelineConnector hub_pipe_connector: connector object to connect related
                                                        callback function and input (source)
                                                        object.
        :param HubElement source: Source of the received messages.
        """
        self.connector = hub_pipe_connector
        self.source = source
        self.receiving_period = 0.001    # set the working period of connection reading.
        self.message_buf_queue = Queue()     # queue messages from source

    def start(self):
        """
        Thread starter function.
        """
        receive_thread = threading.Thread(target=self.receiveFromSource)
        receive_thread.daemon = True
        receive_thread.start()

        transfer_thread = threading.Thread(target=self.parseBufFromSource)
        transfer_thread.daemon = True
        transfer_thread.start()

    def receiveFromSource(self):
        """
        Message receive function from source.
            Reads buffer from source connection when the source reading is available (readable).
            Updates message buffer queue based on received message.
        """

        if self.source.connection.fd is not None:
            rin = []

            if not self.source.connection.portdead:
                rin.append(self.source.connection.fd)
            if rin == []:
                time.sleep(0.0001)
            else:
                try:
                    (rin, win, xin) = select.select(rin, [], [], 0.01)
                    #  print("R:" + str(rin) + "   W:" + str(win))
                except select.error:
                    print(select.error)

                for fd in rin:
                    if fd == self.source.connection.fd:
                        try:
                            # print("{} is readable".format(input.name))
                            received_buffer = self.source.connection.recv(16 * 1024)

                            # print(fd)
                            # if fd == 9:
                            #     print("from_air: ", received_buffer)
                            self.message_buf_queue.put(received_buffer)

                        except Exception as er:
                            pass

        else:
            try:
                received_buffer = self.source.connection.recv(16 * 1024)
                self.message_buf_queue.put(received_buffer)
                # print(received_buffer)
            except:
                self.source.connection.close()
                print("Cannot read receive buffer")


        threading.Timer(self.receiving_period, self.receiveFromSource).start()

    def parseBufFromSource(self):
        """
        Parse message buffer and send it to the pipeline output.
        """

        if not self.message_buf_queue.empty():

            buffer = self.message_buf_queue.get()
            self.buffer_size = sys.getsizeof(buffer)-33

            msgs = self.source.connection.mav.parse_buffer(buffer)

            if msgs != None:
                # print(msgs)
                self.connector.updateCurrentMsg(msgs)

        threading.Timer(self.receiving_period, self.parseBufFromSource).start()